"""
重置Qdrant Collection脚本
用于修复向量维度不匹配的问题
"""
from qdrant_client import QdrantClient
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_qdrant_collection():
    """
    删除旧的Qdrant collection并提示重新创建

    原因: 如果之前使用错误的维度(1536)创建了collection，
    而实际embedding模型输出4096维，需要删除重建。
    """
    try:
        client = QdrantClient(url=settings.QDRANT_URL)
        logger.info(f"连接到Qdrant: {settings.QDRANT_URL}")

        # 检查collection是否存在
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if settings.QDRANT_COLLECTION_NAME in collection_names:
            logger.info(f"找到collection: {settings.QDRANT_COLLECTION_NAME}")

            # 获取collection信息
            collection_info = client.get_collection(settings.QDRANT_COLLECTION_NAME)
            vector_size = collection_info.config.params.vectors.size
            logger.info(f"当前向量维度: {vector_size}")
            logger.info(f"配置的向量维度: {settings.EMBEDDING_DIMENSION}")

            if vector_size != settings.EMBEDDING_DIMENSION:
                logger.warning(f"维度不匹配! collection使用{vector_size}维，配置要求{settings.EMBEDDING_DIMENSION}维")
                logger.info("删除旧collection...")

                client.delete_collection(settings.QDRANT_COLLECTION_NAME)
                logger.info("✅ 旧collection已删除")

                logger.info("\n下一步:")
                logger.info("1. 新collection会在上传数据集时自动创建（使用新的维度配置）")
                logger.info("2. 请在前端重新上传数据集以生成embeddings")
                logger.info("3. 或者运行数据集处理脚本重新生成所有embeddings")
            else:
                logger.info("✅ 向量维度匹配，无需重置")

        else:
            logger.info(f"Collection不存在: {settings.QDRANT_COLLECTION_NAME}")
            logger.info("新collection会在上传数据集时自动创建")

    except Exception as e:
        logger.error(f"重置Qdrant collection失败: {e}")
        raise


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Qdrant Collection重置工具")
    logger.info("=" * 60)
    logger.info("")

    try:
        reset_qdrant_collection()
        logger.info("")
        logger.info("=" * 60)
        logger.info("重置完成")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        exit(1)
