"""
清理旧数据集脚本

用途：清理迁移前的所有数据集（没有MD5的旧数据）

执行方式:
    python clean_old_datasets.py
"""
import asyncio
import logging
from sqlalchemy import text, select
from db.session import async_session, engine
from models.sys_dataset import SysDataset
from core.minio_client import minio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clean_old_datasets():
    """清理所有旧数据集"""
    logger.info("=" * 60)
    logger.info("开始清理旧数据集...")
    logger.info("=" * 60)

    async with async_session() as session:
        try:
            # 查询所有没有MD5的数据集
            result = await session.execute(
                select(SysDataset).where(SysDataset.file_md5.is_(None))
            )
            old_datasets = result.scalars().all()

            if not old_datasets:
                logger.info("✓ 没有需要清理的旧数据集")
                return

            logger.info(f"找到 {len(old_datasets)} 个旧数据集需要清理")

            # 删除每个数据集
            deleted_count = 0
            for dataset in old_datasets:
                try:
                    logger.info(f"正在删除: {dataset.name} (ID: {dataset.id})")

                    # 1. 删除MinIO文件
                    if dataset.original_file_path:
                        try:
                            minio_client.delete_file(dataset.original_file_path)
                            logger.info(f"  - 删除原始文件: {dataset.original_file_path}")
                        except Exception as e:
                            logger.warning(f"  - 删除原始文件失败: {e}")

                    if dataset.parsed_path:
                        try:
                            minio_client.delete_file(dataset.parsed_path)
                            logger.info(f"  - 删除Parquet文件: {dataset.parsed_path}")
                        except Exception as e:
                            logger.warning(f"  - 删除Parquet文件失败: {e}")

                    # 2. 删除Qdrant embeddings
                    try:
                        from services.embedding_service import delete_dataset_embeddings
                        await delete_dataset_embeddings(str(dataset.id))
                        logger.info(f"  - 删除Qdrant embeddings")
                    except Exception as e:
                        logger.warning(f"  - 删除embeddings失败: {e}")

                    # 3. 删除数据库记录
                    await session.delete(dataset)
                    deleted_count += 1

                except Exception as e:
                    logger.error(f"删除数据集失败 {dataset.id}: {e}")
                    continue

            # 提交删除
            await session.commit()

            logger.info("=" * 60)
            logger.info(f"✓ 成功清理 {deleted_count} 个旧数据集")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"清理过程出错: {e}", exc_info=True)
            await session.rollback()
            raise


async def reset_qdrant_collection():
    """重置Qdrant集合（可选）"""
    logger.info("=" * 60)
    logger.info("重置Qdrant集合...")
    logger.info("=" * 60)

    try:
        from services.embedding_service import qdrant_client
        from core.config import settings

        if not qdrant_client:
            logger.warning("Qdrant客户端未初始化")
            return

        # 删除旧集合
        try:
            qdrant_client.delete_collection(settings.QDRANT_COLLECTION_NAME)
            logger.info(f"✓ 已删除旧集合: {settings.QDRANT_COLLECTION_NAME}")
        except Exception as e:
            logger.info(f"删除集合失败(可能不存在): {e}")

        # 重新创建集合
        from qdrant_client.models import Distance, VectorParams

        qdrant_client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE
            )
        )
        logger.info(f"✓ 已重新创建集合: {settings.QDRANT_COLLECTION_NAME}")

    except Exception as e:
        logger.error(f"重置Qdrant集合失败: {e}", exc_info=True)


if __name__ == "__main__":
    import sys

    print("⚠️  警告: 这将删除所有没有MD5的旧数据集!")
    print("   - 删除MinIO中的文件")
    print("   - 删除Qdrant中的embeddings")
    print("   - 删除数据库记录")
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "--reset-qdrant":
        # 包含重置Qdrant选项
        confirm = input("确认清理并重置Qdrant? (yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(clean_old_datasets())
            asyncio.run(reset_qdrant_collection())
        else:
            print("已取消操作")
    else:
        # 仅清理数据集
        confirm = input("确认清理旧数据集? (yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(clean_old_datasets())
        else:
            print("已取消操作")
