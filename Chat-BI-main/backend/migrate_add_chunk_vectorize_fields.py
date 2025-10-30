"""
数据库迁移脚本: 添加分片和向量化字段
为 sys_dataset 表添加细粒度的处理状态字段
"""
import asyncio
from sqlalchemy import text
from db.session import async_session, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """执行数据库迁移"""
    async with engine.begin() as conn:
        logger.info("开始迁移: 添加分片和向量化字段...")

        # 添加分片状态字段
        await conn.execute(text("""
            ALTER TABLE sys_dataset
            ADD COLUMN IF NOT EXISTS chunk_status VARCHAR(50) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS chunk_progress INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS chunk_error TEXT
        """))
        logger.info("✓ 分片状态字段已添加")

        # 添加向量化状态字段
        await conn.execute(text("""
            ALTER TABLE sys_dataset
            ADD COLUMN IF NOT EXISTS vectorize_status VARCHAR(50) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS vectorize_progress INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS vectorize_error TEXT
        """))
        logger.info("✓ 向量化状态字段已添加")

        # 为已有数据设置初始状态
        # 如果 parse_status = 'parsed' 且 embedding_status = 'completed'
        # 则认为 chunk 和 vectorize 都已完成
        await conn.execute(text("""
            UPDATE sys_dataset
            SET
                chunk_status = CASE
                    WHEN parse_status = 'parsed' AND embedding_status = 'completed' THEN 'completed'
                    WHEN parse_status = 'parsed' AND embedding_status = 'failed' THEN 'failed'
                    WHEN parse_status = 'parsed' THEN 'pending'
                    ELSE 'pending'
                END,
                chunk_progress = CASE
                    WHEN parse_status = 'parsed' AND embedding_status = 'completed' THEN 100
                    ELSE 0
                END,
                vectorize_status = CASE
                    WHEN embedding_status = 'completed' THEN 'completed'
                    WHEN embedding_status = 'failed' THEN 'failed'
                    WHEN embedding_status = 'embedding' THEN 'vectorizing'
                    ELSE 'pending'
                END,
                vectorize_progress = CASE
                    WHEN embedding_status = 'completed' THEN 100
                    WHEN embedding_status = 'embedding' THEN embedding_progress
                    ELSE 0
                END,
                vectorize_error = embedding_error
            WHERE chunk_status IS NULL OR vectorize_status IS NULL
        """))
        logger.info("✓ 已有数据状态已同步")

        # 添加注释（分开执行以避免 asyncpg 的 prepared statement 限制）
        comments = [
            "COMMENT ON COLUMN sys_dataset.chunk_status IS '分片状态: pending/chunking/completed/failed'",
            "COMMENT ON COLUMN sys_dataset.chunk_progress IS '分片进度(0-100)'",
            "COMMENT ON COLUMN sys_dataset.chunk_error IS '分片错误信息'",
            "COMMENT ON COLUMN sys_dataset.vectorize_status IS '向量化状态: pending/vectorizing/completed/failed'",
            "COMMENT ON COLUMN sys_dataset.vectorize_progress IS '向量化进度(0-100)'",
            "COMMENT ON COLUMN sys_dataset.vectorize_error IS '向量化错误信息'"
        ]
        for comment_sql in comments:
            await conn.execute(text(comment_sql))
        logger.info("✓ 字段注释已添加")

        logger.info("迁移完成!")


async def verify():
    """验证迁移结果"""
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'sys_dataset'
            AND column_name IN ('chunk_status', 'chunk_progress', 'chunk_error',
                               'vectorize_status', 'vectorize_progress', 'vectorize_error')
            ORDER BY column_name
        """))

        logger.info("\n验证结果:")
        for row in result:
            logger.info(f"  {row.column_name:20s} {row.data_type:15s} DEFAULT: {row.column_default}")


if __name__ == "__main__":
    asyncio.run(migrate())
    asyncio.run(verify())
