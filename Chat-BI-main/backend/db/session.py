from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# 从配置中获取 DATABASE_URL
DATABASE_URL = settings.DATABASE_URL

# 创建异步引擎 (echo=False 减少日志输出)
engine = create_async_engine(DATABASE_URL, echo=False)

# 创建异步会话
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)