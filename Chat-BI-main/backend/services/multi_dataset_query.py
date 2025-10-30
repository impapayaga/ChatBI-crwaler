"""
多数据集智能查询服务

支持用户选择多个数据集进行智能查询
"""
import logging
from typing import List, Dict, Optional, Tuple
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.sys_dataset import SysDataset, SysDatasetColumn
from services.duckdb_query import query_parquet_with_duckdb
from api.utils.ai_utils import call_configured_ai_model

logger = logging.getLogger(__name__)


async def get_datasets_metadata(
    dataset_ids: List[str],
    async_session: AsyncSession
) -> List[Dict]:
    """
    获取多个数据集的元数据

    Args:
        dataset_ids: 数据集ID列表
        async_session: 数据库会话

    Returns:
        数据集元数据列表，每个包含：
        - id: 数据集ID
        - name: 数据集名称
        - logical_name: 逻辑名称
        - columns: 列信息列表
    """
    datasets_metadata = []

    for dataset_id in dataset_ids:
        try:
            # 查询数据集信息
            result = await async_session.execute(
                select(SysDataset).where(SysDataset.id == dataset_id)
            )
            dataset = result.scalar_one_or_none()

            if not dataset:
                logger.warning(f"数据集不存在: {dataset_id}")
                continue

            # 查询数据集的列信息
            columns_result = await async_session.execute(
                select(SysDatasetColumn).where(
                    SysDatasetColumn.dataset_id == dataset_id
                ).limit(50)  # 限制列数
            )
            columns = columns_result.scalars().all()

            # 构建元数据
            metadata = {
                'id': str(dataset.id),
                'name': dataset.name,
                'logical_name': dataset.logical_name or dataset.name,
                'row_count': dataset.row_count,
                'column_count': dataset.column_count,
                'columns': [
                    {
                        'col_name': col.col_name,
                        'col_type': col.col_type,
                        'sample_values': col.sample_values if col.sample_values else []
                    }
                    for col in columns
                ]
            }

            datasets_metadata.append(metadata)
            logger.info(f"加载数据集元数据: {metadata['logical_name']} ({len(metadata['columns'])}列)")

        except Exception as e:
            logger.error(f"获取数据集元数据失败 {dataset_id}: {e}")
            continue

    return datasets_metadata


async def select_relevant_datasets(
    user_query: str,
    datasets_metadata: List[Dict],
    user_id: int = 1
) -> List[str]:
    """
    使用LLM智能选择与用户问题相关的数据集

    Args:
        user_query: 用户问题
        datasets_metadata: 数据集元数据列表
        user_id: 用户ID

    Returns:
        选中的数据集ID列表
    """
    if len(datasets_metadata) == 1:
        # 只有一个数据集，直接返回
        return [datasets_metadata[0]['id']]

    # 构建数据集描述
    datasets_desc = []
    for idx, dataset in enumerate(datasets_metadata, 1):
        col_names = [col['col_name'] for col in dataset['columns'][:10]]
        col_names_str = ', '.join(col_names)

        desc = f"""数据集 {idx}: {dataset['logical_name']}
- ID: {dataset['id']}
- 行数: {dataset['row_count']}
- 列数: {dataset['column_count']}
- 主要列: {col_names_str}
"""
        datasets_desc.append(desc)

    datasets_context = '\n'.join(datasets_desc)

    system_prompt = f"""你是一个智能的数据集选择助手。根据用户的问题，从提供的数据集中选择最相关的数据集。

**可用的数据集:**
{datasets_context}

**任务:**
分析用户问题，判断需要使用哪个或哪些数据集。

**输出格式:**
只输出数据集的编号，用逗号分隔。例如:
- 如果只需要数据集1: 1
- 如果需要数据集1和2: 1,2
- 如果需要所有数据集: 1,2,3

不要输出任何解释，只输出编号。
"""

    try:
        ai_response = await call_configured_ai_model(
            system_prompt,
            user_query,
            user_id=user_id
        )

        # 解析响应，提取数据集编号
        selected_indices = []
        for char in ai_response:
            if char.isdigit():
                idx = int(char)
                if 1 <= idx <= len(datasets_metadata):
                    selected_indices.append(idx)

        if not selected_indices:
            # 默认使用第一个数据集
            logger.warning("LLM未能选择数据集，默认使用第一个")
            selected_indices = [1]

        # 转换为数据集ID
        selected_ids = [datasets_metadata[idx - 1]['id'] for idx in selected_indices]

        logger.info(f"LLM选择的数据集: {selected_indices} -> {selected_ids}")
        return selected_ids

    except Exception as e:
        logger.error(f"LLM选择数据集失败: {e}，默认使用第一个数据集")
        return [datasets_metadata[0]['id']]


async def generate_sql_for_multi_datasets(
    user_query: str,
    datasets_metadata: List[Dict],
    user_id: int = 1
) -> Dict[str, str]:
    """
    为多个数据集生成SQL查询

    Args:
        user_query: 用户问题
        datasets_metadata: 数据集元数据列表
        user_id: 用户ID

    Returns:
        字典，key为数据集ID，value为对应的SQL查询
    """
    sql_queries = {}

    for dataset in datasets_metadata:
        # 构建列信息描述
        col_descriptions = []
        for col in dataset['columns'][:20]:  # 使用前20列
            col_type = col.get('col_type', 'unknown')
            col_name = col['col_name']
            samples = col.get('sample_values', [])
            sample_str = ', '.join([str(s) for s in samples[:3]]) if samples else ''

            col_desc = f"- `{col_name}` ({col_type})"
            if sample_str:
                col_desc += f" - 示例: {sample_str}"
            col_descriptions.append(col_desc)

        schema_context = '\n'.join(col_descriptions)

        system_prompt = f"""你是一个专业的SQL查询生成助手。根据用户问题和数据集schema生成DuckDB SQL查询。

**重要规则:**
1. 表名必须使用 `dataset` (不要使用table_name等占位符)
2. 列名必须用双引号包裹，如 "column_name"
3. 只能使用提供的列名，不要编造列名
4. 查询结果限制在100行以内
5. 使用标准SQL语法
6. 不要使用注释
7. 只生成一条SQL语句

**数据集名称:** {dataset['logical_name']}
**数据集Schema:**
{schema_context}

**用户问题:** {user_query}

请生成SQL查询，使用以下格式返回:
```sql
SELECT ...
```

注意:
- 如果问题涉及行数统计，使用 COUNT(*)
- 如果问题涉及趋势，使用合适的时间列和GROUP BY
- 如果需要聚合，使用合适的GROUP BY
- 优先使用相关度高的列
"""

        try:
            ai_response = await call_configured_ai_model(
                system_prompt,
                user_query,
                user_id=user_id
            )

            if ai_response:
                # 提取SQL
                sql_start = ai_response.find("```sql\n")
                if sql_start != -1:
                    sql_start += len("```sql\n")
                    sql_end = ai_response.find("\n```", sql_start)
                    if sql_end != -1:
                        sql_query = ai_response[sql_start:sql_end].strip()

                        # 验证SQL不包含占位符
                        if 'table_name' not in sql_query.lower() and 'column_name' not in sql_query.lower():
                            sql_queries[dataset['id']] = sql_query
                            logger.info(f"为数据集 {dataset['logical_name']} 生成SQL: {sql_query[:100]}...")
                            continue

                # 如果没有找到SQL代码块，尝试直接提取
                lines = ai_response.strip().split('\n')
                for line in lines:
                    if line.strip().upper().startswith('SELECT'):
                        sql_queries[dataset['id']] = line.strip()
                        logger.info(f"为数据集 {dataset['logical_name']} 生成SQL: {line[:100]}...")
                        break

            # 如果LLM没有生成有效SQL，使用简单查询
            if dataset['id'] not in sql_queries:
                logger.warning(f"LLM未能为数据集 {dataset['logical_name']} 生成有效SQL，使用默认查询")
                # 清理列名，确保没有不可见字符
                cleaned_col_names = []
                for col in dataset['columns'][:5]:
                    col_name = col["col_name"]
                    # 移除不可见字符
                    import unicodedata
                    cleaned_name = ''.join(char for char in col_name 
                                         if unicodedata.category(char) not in ('Cc', 'Cf', 'Cs', 'Co', 'Cn'))
                    cleaned_col_names.append(f'"{cleaned_name}"')
                
                col_names = ', '.join(cleaned_col_names)
                sql_queries[dataset['id']] = f"SELECT {col_names} FROM dataset LIMIT 10"

        except Exception as e:
            logger.error(f"为数据集 {dataset['logical_name']} 生成SQL失败: {e}")
            # 使用默认查询，清理列名
            try:
                import unicodedata
                cleaned_col_names = []
                for col in dataset['columns'][:5]:
                    col_name = col["col_name"]
                    # 移除不可见字符
                    cleaned_name = ''.join(char for char in col_name 
                                         if unicodedata.category(char) not in ('Cc', 'Cf', 'Cs', 'Co', 'Cn'))
                    cleaned_col_names.append(f'"{cleaned_name}"')
                
                col_names = ', '.join(cleaned_col_names)
                sql_queries[dataset['id']] = f"SELECT {col_names} FROM dataset LIMIT 10"
            except:
                # 如果列名处理也失败，使用最简单的查询
                sql_queries[dataset['id']] = "SELECT * FROM dataset LIMIT 10"

    return sql_queries


async def query_multiple_datasets(
    dataset_ids: List[str],
    sql_queries: Dict[str, str]
) -> Optional[pd.DataFrame]:
    """
    查询多个数据集并合并结果

    Args:
        dataset_ids: 数据集ID列表
        sql_queries: 数据集ID到SQL查询的映射

    Returns:
        合并后的DataFrame，如果所有查询都失败则返回None
    """
    dfs = []

    for dataset_id in dataset_ids:
        sql_query = sql_queries.get(dataset_id)
        if not sql_query:
            logger.warning(f"数据集 {dataset_id} 没有对应的SQL查询")
            continue

        try:
            df = await query_parquet_with_duckdb(dataset_id, sql_query)
            if df is not None and not df.empty:
                # 添加数据集来源列
                df['_source_dataset'] = dataset_id
                dfs.append(df)
                logger.info(f"数据集 {dataset_id} 查询成功: {len(df)} 行")
            else:
                logger.warning(f"数据集 {dataset_id} 查询返回空结果")

        except Exception as e:
            logger.error(f"查询数据集 {dataset_id} 失败: {e}")
            continue

    if not dfs:
        logger.error("所有数据集查询都失败")
        return None

    # 合并结果
    try:
        if len(dfs) == 1:
            result = dfs[0]
        else:
            # 尝试合并多个DataFrame
            # 如果列结构相同，使用concat；否则使用join
            result = pd.concat(dfs, ignore_index=True)

        logger.info(f"合并后的结果: {len(result)} 行, {len(result.columns)} 列")
        return result

    except Exception as e:
        logger.error(f"合并数据集结果失败: {e}")
        # 如果合并失败，返回第一个成功的结果
        return dfs[0] if dfs else None


async def smart_multi_dataset_query(
    user_query: str,
    dataset_ids: List[str],
    async_session: AsyncSession,
    user_id: int = 1
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    智能多数据集查询主函数

    完整流程：
    1. 获取所有数据集的元数据
    2. 使用LLM选择与问题相关的数据集
    3. 为每个选中的数据集生成SQL查询
    4. 执行查询并合并结果

    Args:
        user_query: 用户问题
        dataset_ids: 用户选中的数据集ID列表
        async_session: 数据库会话
        user_id: 用户ID

    Returns:
        (DataFrame, 数据源描述)
    """
    logger.info(f"开始智能多数据集查询: {len(dataset_ids)} 个数据集")

    # 步骤1: 获取数据集元数据
    datasets_metadata = await get_datasets_metadata(dataset_ids, async_session)

    if not datasets_metadata:
        logger.error("未能获取任何数据集元数据")
        return None, "未能获取数据集信息"

    logger.info(f"成功加载 {len(datasets_metadata)} 个数据集的元数据")

    # 步骤2: 智能选择相关数据集
    selected_ids = await select_relevant_datasets(
        user_query,
        datasets_metadata,
        user_id
    )

    # 过滤出选中的数据集元数据
    selected_metadata = [
        ds for ds in datasets_metadata if ds['id'] in selected_ids
    ]

    logger.info(f"选中 {len(selected_metadata)} 个数据集进行查询")

    # 步骤3: 生成SQL查询
    sql_queries = await generate_sql_for_multi_datasets(
        user_query,
        selected_metadata,
        user_id
    )

    if not sql_queries:
        logger.error("未能生成任何SQL查询")
        return None, "无法生成查询语句"

    # 步骤4: 执行查询并合并结果
    df = await query_multiple_datasets(selected_ids, sql_queries)

    # 构建数据源描述
    dataset_names = [ds['logical_name'] for ds in selected_metadata]
    data_source_desc = f"数据来源: {', '.join(dataset_names)}"

    return df, data_source_desc
