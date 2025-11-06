"""
数据库迁移脚本: 添加analysis字段到sys_conversation_message表

执行方式:
    python migrate_add_analysis_column.py

变更内容:
    1. 添加 analysis 字段 (TEXT, 可为空)
"""
import asyncio
import logging
from sqlalchemy import text
from db.session import engine

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


async def migrate():
    """执行迁移"""
    logger.info("=" * 60)
    logger.info("开始数据库迁移: 添加analysis字段到sys_conversation_message表")
    logger.info("=" * 60)

    try:
        # 添加 analysis 字段
        await add_column_if_not_exists(
            "sys_conversation_message",
            "analysis",
            "TEXT"
        )

        logger.info("=" * 60)
        logger.info("✓ 数据库迁移完成!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ 迁移失败: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())





