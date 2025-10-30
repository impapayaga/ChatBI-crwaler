"""
向量化服务(Embedding Service) - 使用Qdrant
用于生成列级向量并支持语义检索
支持从数据库读取AI模型配置
"""
from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from core.config import settings
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import httpx

logger = logging.getLogger(__name__)

# 全局embedding配置缓存
_embedding_config_cache = None
_openai_client_cache = None
_dimension_cache: Optional[int] = None
_collection_name_cache: Optional[str] = None

# 初始化Qdrant客户端
qdrant_client = None
try:
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    logger.info(f"Qdrant客户端初始化成功: {settings.QDRANT_URL}")
except Exception as e:
    logger.error(f"Qdrant客户端初始化失败: {e}")


async def _get_embedding_config():
    """从数据库获取embedding模型配置"""
    global _embedding_config_cache

    # 使用缓存(5分钟有效)
    if _embedding_config_cache:
        return _embedding_config_cache

    try:
        from sqlalchemy import select
        from models.sys_ai_model_config import SysAiModelConfig
        from db.session import async_session

        async with async_session() as session:
            # 查询默认的embedding模型配置
            result = await session.execute(
                select(SysAiModelConfig)
                .where(SysAiModelConfig.model_type == 'embedding')
                .where(SysAiModelConfig.is_active == True)
                .where(SysAiModelConfig.is_default == True)
                .limit(1)
            )
            config = result.scalar_one_or_none()

            if config:
                _embedding_config_cache = {
                    'provider': config.provider,
                    'model_name': config.model_name,
                    'api_url': config.api_url,
                    'api_key': config.api_key,
                    'model_params': config.model_params or {}
                }
                logger.info(f"从数据库加载embedding配置: {config.model_name}")
                return _embedding_config_cache

    except Exception as e:
        logger.warning(f"从数据库加载embedding配置失败: {e}")

    # 回退到环境变量配置，使用SiliconFlow
    if settings.OPENAI_API_KEY:
        _embedding_config_cache = {
            'provider': 'siliconflow',
            'model_name': 'BAAI/bge-large-zh-v1.5',  # 1024维模型
            'api_url': 'https://api.siliconflow.cn/v1',
            'api_key': settings.OPENAI_API_KEY,
            'dimension': 1024,
            'model_params': {}
        }
        logger.info("使用环境变量中的SiliconFlow配置")
        return _embedding_config_cache

    logger.warning("未找到有效的embedding配置")
    return None


async def _get_openai_client():
    """获取OpenAI客户端(支持多种API提供商)"""
    global _openai_client_cache

    if _openai_client_cache:
        return _openai_client_cache

    config = await _get_embedding_config()
    if not config:
        return None

    try:
        # 根据provider类型处理API URL
        # OpenAI SDK的行为: base_url + endpoint路径
        # 例如: base_url="https://api.openai.com/v1" -> 自动变成 "https://api.openai.com/v1/embeddings"

        provider = config.get('provider', 'openai').lower()
        api_url = config['api_url'].rstrip('/')

        if provider == 'openai':
            # OpenAI标准: 配置应该是 https://api.openai.com/v1
            # SDK会自动添加 /embeddings
            base_url = api_url if api_url.endswith('/v1') else api_url + '/v1'

        elif provider == 'siliconflow':
            # 硅基流动: 配置是完整URL https://api.siliconflow.cn/v1/embeddings
            # 需要去掉endpoint部分,只保留到/v1
            if '/embeddings' in api_url:
                base_url = api_url.split('/embeddings')[0]
            elif '/chat/completions' in api_url:
                base_url = api_url.split('/chat/completions')[0]
            else:
                # 如果已经是base URL,确保以/v1结尾
                base_url = api_url if api_url.endswith('/v1') else api_url + '/v1'

        else:
            # 其他provider,默认处理方式
            # 移除可能存在的endpoint路径
            if '/embeddings' in api_url:
                base_url = api_url.split('/embeddings')[0]
            elif '/chat/completions' in api_url:
                base_url = api_url.split('/chat/completions')[0]
            else:
                base_url = api_url

            # 确保以/v1结尾(如果URL结构支持)
            if '/v1' in base_url and not base_url.endswith('/v1'):
                # 截取到/v1为止
                base_url = base_url[:base_url.index('/v1') + 3]
            elif not base_url.endswith('/v1') and not base_url.endswith('/api'):
                base_url = base_url + '/v1'

        _openai_client_cache = AsyncOpenAI(
            api_key=config['api_key'],
            base_url=base_url
        )
        logger.info(f"Embedding客户端初始化成功: provider={provider}, base_url={base_url}")
        return _openai_client_cache

    except Exception as e:
        logger.error(f"Embedding客户端初始化失败: {e}")
        return None


async def _detect_current_embedding_dimension() -> Optional[int]:
    """
    探测当前激活embedding模型输出维度；使用缓存避免重复调用。
    """
    global _dimension_cache
    if _dimension_cache:
        return _dimension_cache

    client = await _get_openai_client()
    config = await _get_embedding_config()
    if not client or not config:
        logger.warning("无法探测embedding维度：客户端或配置缺失")
        return None

    try:
        resp = await client.embeddings.create(
            model=config['model_name'],
            input="dimension_probe"
        )
        vec = resp.data[0].embedding
        _dimension_cache = len(vec)
        logger.info(f"探测到当前embedding维度: {_dimension_cache}")
        return _dimension_cache
    except Exception as e:
        logger.error(f"探测embedding维度失败: {e}")
        return None


def _build_collection_name_for_dim(base_name: str, dim: Optional[int]) -> str:
    return base_name if not dim else f"{base_name}_{dim}"


def _ensure_collection_with_dim(collection_name: str, dim: int) -> bool:
    if not qdrant_client:
        return False
    try:
        collections = qdrant_client.get_collections().collections
        names = [c.name for c in collections]
        if collection_name not in names:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )
            logger.info(f"Qdrant collection已创建: {collection_name}, 维度: {dim}")
            return True

        info = qdrant_client.get_collection(collection_name)
        existing_dim = info.config.params.vectors.size
        points_count = info.points_count
        if existing_dim == dim:
            return True
        if points_count == 0:
            qdrant_client.delete_collection(collection_name)
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )
            logger.info(f"Qdrant collection已按新维度重建: {collection_name}, 维度: {dim}")
            return True
        logger.error(f"Qdrant集合维度不匹配且非空: {collection_name}, 期望: {dim}, 实际: {existing_dim}, points: {points_count}")
        return False
    except Exception as e:
        logger.error(f"检查/创建维度化Qdrant collection失败: {e}")
        return False


async def _get_or_prepare_collection_name() -> Optional[str]:
    global _collection_name_cache
    if _collection_name_cache:
        return _collection_name_cache
    dim = await _detect_current_embedding_dimension()
    base = settings.QDRANT_COLLECTION_NAME
    collection_name = _build_collection_name_for_dim(base, dim)
    if dim is None:
        _collection_name_cache = collection_name
        return _collection_name_cache
    if not _ensure_collection_with_dim(collection_name, dim):
        return None
    _collection_name_cache = collection_name
    return _collection_name_cache

def _ensure_collection():
    """确保Qdrant collection存在"""
    if not qdrant_client:
        return False

    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if settings.QDRANT_COLLECTION_NAME not in collection_names:
            # 创建collection
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Qdrant collection已创建: {settings.QDRANT_COLLECTION_NAME}")
        return True
    except Exception as e:
        logger.error(f"检查/创建Qdrant collection失败: {e}")
        return False


async def generate_column_embeddings(dataset_id: str, schema_info: List[Dict[str, Any]]):
    """
    为数据集的所有列生成embedding向量并存入Qdrant

    Args:
        dataset_id: 数据集ID
        schema_info: 列信息列表,包含name, type, stats, samples

    策略:
        - 构造描述文本: 列名 + 类型 + 示例值
        - 调用OpenAI embedding API
        - 存入Qdrant
    """
    # 获取embedding客户端和配置
    client = await _get_openai_client()
    config = await _get_embedding_config()

    if not client or not config:
        logger.warning("Embedding客户端或配置未初始化,跳过embedding生成")
        return

    if not qdrant_client:
        logger.warning("Qdrant客户端未初始化,跳过embedding生成")
        return

    # 选择/创建匹配维度的collection
    collection_name = await _get_or_prepare_collection_name()
    if not collection_name:
        logger.error("无法获取匹配维度的Qdrant集合")
        return

    try:
        logger.info(f"开始为数据集 {dataset_id} 生成 {len(schema_info)} 个列的embedding")

        points = []
        for idx, col_info in enumerate(schema_info):
            try:
                # 构造描述文本
                description = build_column_description(col_info)

                # 调用Embedding API
                response = await client.embeddings.create(
                    model=config['model_name'],
                    input=description
                )
                embedding = response.data[0].embedding

                # 构造Qdrant point
                # Qdrant要求point ID必须是unsigned integer或UUID
                # 使用字符串ID的hash值转换为正整数(32位,避免溢出)
                string_id = f"{dataset_id}_{col_info['name']}_{idx}"
                point_id = abs(hash(string_id)) % (2**31)  # 确保是正整数且在32位范围内

                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "dataset_id": str(dataset_id),
                        "col_name": col_info['name'],
                        "col_type": col_info.get('type'),
                        "col_index": idx,
                        "description": description,
                        "stats": col_info.get('stats', {}),
                        "sample_values": col_info.get('samples', []),
                        "string_id": string_id  # 保存原始字符串ID用于调试
                    }
                )
                points.append(point)

                logger.debug(f"列 '{col_info['name']}' embedding已生成")

            except Exception as e:
                logger.error(f"生成列 '{col_info['name']}' embedding失败: {e}")
                continue

        # 批量插入Qdrant
        if points:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"数据集 {dataset_id} 的 {len(points)} 个列embedding已存入Qdrant")

    except Exception as e:
        logger.error(f"生成column embeddings失败: {e}", exc_info=True)
        raise


def build_column_description(col_info: Dict[str, Any]) -> str:
    """
    构造列的描述文本,用于生成embedding

    Args:
        col_info: 列信息 {name, type, stats, samples}

    Returns:
        描述文本

    示例:
        "列名: sales_amount, 类型: float, 统计: 最小值100.0 最大值50000.0, 示例值: [1250.5, 3400.2, 890.0]"
    """
    parts = [f"列名: {col_info['name']}"]

    # 添加类型
    if col_info.get('type'):
        parts.append(f"类型: {col_info['type']}")

    # 添加关键统计信息
    stats = col_info.get('stats', {})
    if stats:
        stat_strs = []
        if 'min' in stats and stats['min'] is not None:
            stat_strs.append(f"最小值{stats['min']}")
        if 'max' in stats and stats['max'] is not None:
            stat_strs.append(f"最大值{stats['max']}")
        if 'unique_count' in stats:
            stat_strs.append(f"唯一值数{stats['unique_count']}")

        if stat_strs:
            parts.append(f"统计: {' '.join(stat_strs)}")

    # 添加示例值
    samples = col_info.get('samples', [])
    if samples:
        sample_str = ', '.join(str(s) for s in samples[:5])
        parts.append(f"示例值: [{sample_str}]")

    return ', '.join(parts)


async def vectorize_columns(dataset_id: str, chunked_data: List[Dict[str, Any]]):
    """
    对已分片的列数据进行向量化并存入Qdrant

    Args:
        dataset_id: 数据集ID
        chunked_data: 分片数据列表，每项包含 {index, col_info, description}

    Raises:
        Exception: 向量化失败时抛出异常
    """
    # 获取embedding客户端和配置
    client = await _get_openai_client()
    config = await _get_embedding_config()

    if not client or not config:
        raise Exception("Embedding客户端或配置未初始化")

    if not qdrant_client:
        raise Exception("Qdrant客户端未初始化")

    # 选择/创建匹配维度的collection
    collection_name = await _get_or_prepare_collection_name()
    if not collection_name:
        raise Exception("无法获取匹配维度的Qdrant集合")

    try:
        logger.info(f"开始为数据集 {dataset_id} 向量化 {len(chunked_data)} 个列")

        # 获取数据库会话以更新进度
        from db.session import async_session
        from models.sys_dataset import SysDataset
        from sqlalchemy import select

        points = []
        for item in chunked_data:
            idx = item['index']
            col_info = item['col_info']
            description = item['description']

            try:
                # 调用Embedding API
                response = await client.embeddings.create(
                    model=config['model_name'],
                    input=description
                )
                embedding = response.data[0].embedding

                # 构造Qdrant point
                string_id = f"{dataset_id}_{col_info['name']}_{idx}"
                point_id = abs(hash(string_id)) % (2**31)

                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "dataset_id": str(dataset_id),
                        "col_name": col_info['name'],
                        "col_type": col_info.get('type'),
                        "col_index": idx,
                        "description": description,
                        "stats": col_info.get('stats', {}),
                        "sample_values": col_info.get('samples', []),
                        "string_id": string_id
                    }
                )
                points.append(point)

                # 更新向量化进度
                progress = int((idx + 1) / len(chunked_data) * 100)
                async with async_session() as session:
                    result = await session.execute(
                        select(SysDataset).where(SysDataset.id == dataset_id)
                    )
                    dataset = result.scalar_one_or_none()
                    if dataset:
                        dataset.vectorize_progress = progress
                        await session.commit()

                logger.debug(f"列 '{col_info['name']}' 向量化完成 ({idx+1}/{len(chunked_data)})")

            except Exception as e:
                logger.error(f"向量化列 '{col_info['name']}' 失败: {e}")
                raise  # 向量化失败应该中断流程

        # 批量插入Qdrant
        if points:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"数据集 {dataset_id} 的 {len(points)} 个列向量已存入Qdrant")
        else:
            raise Exception("没有成功生成任何向量")

    except Exception as e:
        logger.error(f"向量化失败: {e}", exc_info=True)
        raise


async def search_relevant_columns(
    query: str,
    top_k: int = 5,
    dataset_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    根据用户问题检索最相关的列(使用Qdrant)
    支持多维度集合查询，确保能检索到历史数据

    Args:
        query: 用户问题
        top_k: 返回top K个结果
        dataset_id: 可选的数据集ID过滤

    Returns:
        相关列列表,每项包含: dataset_id, col_name, similarity, col_type等
    """
    # 获取embedding客户端和配置
    client = await _get_openai_client()
    config = await _get_embedding_config()

    if not client or not config:
        logger.warning("Embedding客户端或配置未初始化,无法进行向量检索")
        return []

    if not qdrant_client:
        logger.warning("Qdrant客户端未初始化,无法进行向量检索")
        return []

    try:
        # 生成问题的embedding
        response = await client.embeddings.create(
            model=config['model_name'],
            input=query
        )
        query_embedding = response.data[0].embedding

        # 构造过滤条件
        query_filter = None
        if dataset_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="dataset_id",
                        match=MatchValue(value=str(dataset_id))
                    )
                ]
            )

        # 获取所有相关的collections
        all_collections = qdrant_client.get_collections().collections
        base_collection_name = settings.QDRANT_COLLECTION_NAME
        relevant_collections = []
        
        # 获取查询向量的维度
        query_dim = len(query_embedding)
        logger.info(f"查询向量维度: {query_dim}")
        
        # 查找所有以base_collection_name开头的collections
        for collection in all_collections:
            if collection.name.startswith(base_collection_name):
                # 检查集合的维度是否与查询向量匹配
                try:
                    collection_info = qdrant_client.get_collection(collection.name)
                    collection_dim = collection_info.config.params.vectors.size
                    if collection_dim == query_dim:
                        relevant_collections.append(collection.name)
                        logger.info(f"集合 {collection.name} 维度匹配: {collection_dim}")
                    else:
                        logger.info(f"集合 {collection.name} 维度不匹配: 期望{query_dim}, 实际{collection_dim}")
                except Exception as e:
                    logger.warning(f"获取集合 {collection.name} 信息失败: {e}")
                    continue
        
        logger.info(f"找到维度匹配的collections: {relevant_collections}")

        # 在所有相关collections中搜索
        all_results = []
        for collection_name in relevant_collections:
            try:
                search_result = qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    query_filter=query_filter,
                    limit=top_k
                )
                
                # 为每个结果添加collection信息
                for hit in search_result:
                    all_results.append({
                        'dataset_id': hit.payload.get('dataset_id'),
                        'col_name': hit.payload.get('col_name'),
                        'col_type': hit.payload.get('col_type'),
                        'col_index': hit.payload.get('col_index'),
                        'similarity': float(hit.score),
                        'description': hit.payload.get('description'),
                        'stats': hit.payload.get('stats', {}),
                        'sample_values': hit.payload.get('sample_values', []),
                        'collection_name': collection_name  # 添加collection信息
                    })
                    
            except Exception as e:
                logger.warning(f"在collection {collection_name} 中搜索失败: {e}")
                continue

        # 按相似度排序并返回top_k个结果
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        relevant_columns = all_results[:top_k]

        if relevant_columns:
            logger.info(f"检索到 {len(relevant_columns)} 个相关列, top similarity: {relevant_columns[0]['similarity']:.3f}")
        else:
            logger.info("未检索到相关列")

        return relevant_columns

    except Exception as e:
        logger.error(f"向量检索失败: {e}", exc_info=True)
        return []


async def get_dataset_columns(dataset_id: str) -> List[Dict[str, Any]]:
    """
    从Qdrant获取数据集的所有列信息
    支持多维度集合查询，确保能获取到历史数据

    Args:
        dataset_id: 数据集ID

    Returns:
        列信息列表
    """
    if not qdrant_client:
        logger.warning("Qdrant客户端未初始化")
        return []

    try:
        # 获取所有相关的collections
        all_collections = qdrant_client.get_collections().collections
        base_collection_name = settings.QDRANT_COLLECTION_NAME
        relevant_collections = []
        
        # 查找所有以base_collection_name开头的collections
        for collection in all_collections:
            if collection.name.startswith(base_collection_name):
                relevant_collections.append(collection.name)
        
        logger.info(f"在collections中查找数据集 {dataset_id} 的列信息: {relevant_collections}")

        # 在所有相关collections中查找
        all_columns = []
        for collection_name in relevant_collections:
            try:
                scroll_result = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="dataset_id",
                                match=MatchValue(value=str(dataset_id))
                            )
                        ]
                    ),
                    limit=1000  # 假设不超过1000列
                )

                for point in scroll_result[0]:
                    all_columns.append({
                        'col_name': point.payload.get('col_name'),
                        'col_type': point.payload.get('col_type'),
                        'col_index': point.payload.get('col_index'),
                        'stats': point.payload.get('stats', {}),
                        'sample_values': point.payload.get('sample_values', []),
                        'collection_name': collection_name  # 添加collection信息
                    })
                    
            except Exception as e:
                logger.warning(f"在collection {collection_name} 中查找列信息失败: {e}")
                continue

        # 按col_index排序
        all_columns.sort(key=lambda x: x.get('col_index', 0))
        logger.info(f"找到数据集 {dataset_id} 的 {len(all_columns)} 个列")
        return all_columns

    except Exception as e:
        logger.error(f"获取数据集列信息失败: {e}")
        return []


async def delete_dataset_embeddings(dataset_id: str):
    """
    删除数据集的所有embedding

    Args:
        dataset_id: 数据集ID
    """
    if not qdrant_client:
        logger.warning("Qdrant客户端未初始化")
        return

    try:
        # 使用filter删除
        collection_name = await _get_or_prepare_collection_name()
        if not collection_name:
            logger.error("无法获取匹配维度的Qdrant集合，跳过删除")
            return
        qdrant_client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="dataset_id",
                        match=MatchValue(value=str(dataset_id))
                    )
                ]
            )
        )
        logger.info(f"数据集 {dataset_id} 的embeddings已从Qdrant删除")

    except Exception as e:
        logger.error(f"删除embeddings失败: {e}")
