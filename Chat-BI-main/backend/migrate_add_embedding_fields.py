"""
数据库迁移脚本: 添加embedding和MD5字段到sys_dataset表

执行方式:
    python migrate_add_embedding_fields.py

变更内容:
    1. 添加 file_md5 字段 (VARCHAR(32), 索引)
    2. 添加 embedding_status 字段 (VARCHAR(50))
    3. 添加 embedding_progress 字段 (INTEGER)
    4. 添加 embedding_error 字段 (TEXT)
"""
import asyncio
import logging
from sqlalchemy import text
from db.session import async_session, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    async with engine.connect() as conn:
        # PostgreSQL查询列是否存在
        query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
            AND column_name = :column_name
        """)
        result = await conn.execute(query, {"table_name": table_name, "column_name": column_name})
        return result.fetchone() is not None


async def add_column_if_not_exists(table_name: str, column_name: str, column_definition: str):
    """如果列不存在则添加"""
    exists = await check_column_exists(table_name, column_name)

    if exists:
        logger.info(f"列 {table_name}.{column_name} 已存在,跳过")
        return False

    async with engine.begin() as conn:
        query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        await conn.execute(query)
        logger.info(f"✓ 已添加列 {table_name}.{column_name}")
        return True


async def create_index_if_not_exists(index_name: str, table_name: str, column_name: str):
    """如果索引不存在则创建"""
    async with engine.connect() as conn:
        # 检查索引是否存在
        query = text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = :table_name
            AND indexname = :index_name
        """)
        result = await conn.execute(query, {"table_name": table_name, "index_name": index_name})
        exists = result.fetchone() is not None

    if exists:
        logger.info(f"索引 {index_name} 已存在,跳过")
        return False

    async with engine.begin() as conn:
        query = text(f"CREATE INDEX {index_name} ON {table_name}({column_name})")
        await conn.execute(query)
        logger.info(f"✓ 已创建索引 {index_name}")
        return True


async def update_existing_records():
    """更新已有记录的默认值"""
    async with async_session() as session:
        # 为现有记录设置embedding_status = 'pending'
        query = text("""
            UPDATE sys_dataset
            SET embedding_status = 'pending',
                embedding_progress = 0
            WHERE embedding_status IS NULL
        """)
        result = await session.execute(query)
        await session.commit()

        updated_count = result.rowcount
        if updated_count > 0:
            logger.info(f"✓ 已更新 {updated_count} 条现有记录的embedding状态")
        else:
            logger.info("没有需要更新的记录")


async def migrate():
    """执行迁移"""
    logger.info("=" * 60)
    logger.info("开始数据库迁移: 添加embedding和MD5字段")
    logger.info("=" * 60)

    try:
        # 1. 添加 file_md5 字段
        await add_column_if_not_exists(
            "sys_dataset",
            "file_md5",
            "VARCHAR(32)"
        )

        # 2. 创建 file_md5 索引
        await create_index_if_not_exists(
            "ix_sys_dataset_file_md5",
            "sys_dataset",
            "file_md5"
        )

        # 3. 添加 embedding_status 字段
        await add_column_if_not_exists(
            "sys_dataset",
            "embedding_status",
            "VARCHAR(50) DEFAULT 'pending'"
        )

        # 4. 添加 embedding_progress 字段
        await add_column_if_not_exists(
            "sys_dataset",
            "embedding_progress",
            "INTEGER DEFAULT 0"
        )

        # 5. 添加 embedding_error 字段
        await add_column_if_not_exists(
            "sys_dataset",
            "embedding_error",
            "TEXT"
        )

        # 6. 更新现有记录
        await update_existing_records()

        logger.info("=" * 60)
        logger.info("✓ 数据库迁移完成!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ 迁移失败: {e}", exc_info=True)
        raise


async def rollback():
    """回滚迁移 (仅在需要时手动执行)"""
    logger.warning("=" * 60)
    logger.warning("开始回滚迁移...")
    logger.warning("=" * 60)

    async with engine.begin() as conn:
        try:
            # 删除添加的列
            columns_to_drop = ["file_md5", "embedding_status", "embedding_progress", "embedding_error"]

            for col in columns_to_drop:
                exists = await check_column_exists("sys_dataset", col)
                if exists:
                    query = text(f"ALTER TABLE sys_dataset DROP COLUMN {col}")
                    await conn.execute(query)
                    logger.warning(f"✓ 已删除列 {col}")

            logger.warning("✓ 回滚完成")

        except Exception as e:
            logger.error(f"✗ 回滚失败: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        # 回滚模式
        print("⚠️  警告: 这将删除所有新添加的字段!")
        confirm = input("确认回滚? (yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(rollback())
        else:
            print("已取消回滚")
    else:
        # 正常迁移
        asyncio.run(migrate())
