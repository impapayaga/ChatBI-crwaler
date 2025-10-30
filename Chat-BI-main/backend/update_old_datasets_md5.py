"""
为旧数据集计算并更新MD5

用途：为迁移前上传的数据集（没有MD5）计算MD5值

执行方式:
    python update_old_datasets_md5.py
"""
import asyncio
import logging
import hashlib
from sqlalchemy import select
from db.session import async_session
from models.sys_dataset import SysDataset
from core.minio_client import minio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_old_datasets_md5():
    """为旧数据集计算并更新MD5"""
    logger.info("=" * 60)
    logger.info("开始为旧数据集计算MD5...")
    logger.info("=" * 60)

    async with async_session() as session:
        try:
            # 查询所有没有MD5的数据集
            result = await session.execute(
                select(SysDataset).where(SysDataset.file_md5.is_(None))
            )
            old_datasets = result.scalars().all()

            if not old_datasets:
                logger.info("✓ 没有需要更新的数据集")
                return

            logger.info(f"找到 {len(old_datasets)} 个数据集需要计算MD5")

            updated_count = 0
            failed_count = 0
            skipped_count = 0

            for idx, dataset in enumerate(old_datasets, 1):
                try:
                    logger.info(f"[{idx}/{len(old_datasets)}] 处理: {dataset.name} (ID: {dataset.id})")

                    # 检查原始文件路径
                    if not dataset.original_file_path:
                        logger.warning(f"  ⚠️  跳过: 没有原始文件路径")
                        skipped_count += 1
                        continue

                    # 从MinIO下载文件
                    try:
                        file_data = minio_client.download_file(dataset.original_file_path)
                        logger.info(f"  - 已下载文件: {len(file_data)} bytes")
                    except Exception as e:
                        logger.error(f"  ✗ 下载文件失败: {e}")
                        failed_count += 1
                        continue

                    # 计算MD5
                    file_md5 = hashlib.md5(file_data).hexdigest()
                    logger.info(f"  - 计算MD5: {file_md5}")

                    # 检查是否已存在相同MD5的数据集
                    check_result = await session.execute(
                        select(SysDataset).where(SysDataset.file_md5 == file_md5)
                    )
                    existing = check_result.scalar_one_or_none()

                    if existing:
                        logger.warning(f"  ⚠️  发现重复文件! 已存在数据集: {existing.name} (ID: {existing.id})")
                        logger.warning(f"     建议删除当前数据集或手动处理")
                        # 仍然更新MD5，但标记为重复
                        dataset.file_md5 = file_md5
                        dataset.description = (dataset.description or "") + f" [警告:重复文件,与{existing.id}相同]"
                    else:
                        # 更新MD5
                        dataset.file_md5 = file_md5

                    # 如果没有embedding_status，设置为pending
                    if not dataset.embedding_status:
                        dataset.embedding_status = 'pending'
                        dataset.embedding_progress = 0

                    updated_count += 1
                    logger.info(f"  ✓ 已更新MD5")

                except Exception as e:
                    logger.error(f"  ✗ 处理失败: {e}")
                    failed_count += 1
                    continue

            # 提交更新
            await session.commit()

            logger.info("=" * 60)
            logger.info(f"✓ 更新完成!")
            logger.info(f"  - 成功: {updated_count}")
            logger.info(f"  - 失败: {failed_count}")
            logger.info(f"  - 跳过: {skipped_count}")
            logger.info("=" * 60)

            if updated_count > 0:
                logger.info("\n建议:")
                logger.info("1. 检查是否有重复文件警告")
                logger.info("2. 重新生成embedding (如果需要)")

        except Exception as e:
            logger.error(f"更新过程出错: {e}", exc_info=True)
            await session.rollback()
            raise


if __name__ == "__main__":
    print("此脚本将为所有旧数据集计算MD5")
    print("- 从MinIO下载原始文件")
    print("- 计算MD5哈希值")
    print("- 更新数据库记录")
    print("- 检测重复文件")
    print()

    confirm = input("确认执行? (yes/no): ")
    if confirm.lower() == "yes":
        asyncio.run(update_old_datasets_md5())
    else:
        print("已取消操作")
