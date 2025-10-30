import logging
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.session import async_session
import pandas as pd
from core.config import settings
from api.schemas.user_input import UserInput
from api.utils.ai_utils import analyze_user_intent_and_generate_sql  # 导入函数
from sqlalchemy.sql import text

# 加载环境变量
load_dotenv()

# 从配置中获取数据库连接信息
DBNAME = settings.DB_NAME
DBUSER = settings.DB_USER
DBPGPASSWORD = settings.DB_PASSWORD
DBHOST = settings.DB_HOST
DBPORT = settings.DB_PORT

async def execute_sql_query(sql_query: str, user_input, async_session: AsyncSession, retry_count=3):
    """
    执行SQL查询并返回DataFrame

    Args:
        sql_query: SQL查询语句
        user_input: 用户输入对象
        async_session: 已经存在的AsyncSession实例(由FastAPI依赖注入)
        retry_count: 重试次数

    Returns:
        DataFrame或None
    """
    # 注意: async_session已经是一个活跃的会话,不需要再用async with包装
    # 也不需要手动开启事务,因为FastAPI的依赖注入已经处理了事务
    for attempt in range(retry_count):
        try:
            result = await async_session.execute(text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        except Exception as e:
            logging.error(f"SQL查询错误 (第{attempt + 1}次尝试): {e}")

            # 关键修复: 显式回滚事务以清除错误状态
            try:
                await async_session.rollback()
                logging.info("事务已回滚，清除错误状态")
            except Exception as rollback_error:
                logging.error(f"回滚事务失败: {rollback_error}")

            if attempt < retry_count - 1:
                logging.info("重新生成SQL查询语句并重试...")
                sql_query = await analyze_user_intent_and_generate_sql(user_input.user_input, user_id=user_input.user_id)
                if not sql_query:
                    logging.error("重新生成SQL查询语句失败")
                    return None
            else:
                logging.error("多次尝试后仍未能成功执行SQL查询")
                return None

    return None