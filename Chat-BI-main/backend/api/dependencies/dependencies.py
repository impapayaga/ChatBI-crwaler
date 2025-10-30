from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import async_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import redis.asyncio as aioredis
from core.config import settings

# 初始化数据库连接
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 初始化 Redis 连接
redis_client = aioredis.from_url(settings.REDIS_URL)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session