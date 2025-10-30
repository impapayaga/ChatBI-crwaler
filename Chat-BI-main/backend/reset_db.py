"""
数据库重置脚本
使用方法: python reset_db.py

警告: 此脚本会删除所有现有表并重新创建，所有数据将丢失！
"""
import asyncio
import logging
from sqlalchemy.exc import SQLAlchemyError
from models.base import Base
from db.session import engine
from db.init_db import init_db, insert_default_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def reset_database():
    """重置数据库：删除所有表并重新创建"""
    try:
        async with engine.begin() as conn:
            # 删除所有表
            logging.info("正在删除所有现有表...")
            await conn.run_sync(Base.metadata.drop_all)
            logging.info("所有表已删除")

        # 重新创建表
        await init_db()

        # 插入默认数据
        await insert_default_data()

        logging.info("数据库重置完成！")

    except SQLAlchemyError as e:
        logging.error(f"数据库操作错误: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("警告: 此操作将删除所有现有表和数据！")
    print("=" * 60)

    confirm = input("确认要重置数据库吗？(输入 yes 继续): ")

    if confirm.lower() == 'yes':
        asyncio.run(reset_database())
    else:
        print("操作已取消")
