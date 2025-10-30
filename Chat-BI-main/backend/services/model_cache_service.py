"""
AI模型缓存服务 - 使用Redis管理用户选择的AI模型配置
"""
import logging
import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.sys_ai_model_config import SysAiModelConfig
from api.dependencies.dependencies import redis_client

logger = logging.getLogger(__name__)


class ModelCacheService:
    """AI模型缓存服务"""

    CACHE_KEY_PREFIX = "user_selected_model"
    CACHE_EXPIRE_SECONDS = 3600 * 24  # 24小时过期

    @staticmethod
    def _get_cache_key(user_id: int) -> str:
        """获取Redis缓存键"""
        return f"{ModelCacheService.CACHE_KEY_PREFIX}:{user_id}"

    @classmethod
    async def get_user_selected_model(
        cls,
        user_id: int,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户选择的AI模型配置

        优先从Redis读取,如果Redis中没有则从数据库读取并缓存

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            模型配置字典,包含: id, config_name, model_name, api_url, api_key等
        """
        cache_key = cls._get_cache_key(user_id)

        try:
            # 1. 尝试从Redis读取
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info(f"从Redis缓存获取用户{user_id}的模型配置")
                return json.loads(cached_data)

            # 2. Redis中没有,从数据库读取
            logger.info(f"Redis缓存未命中,从数据库获取用户{user_id}的模型配置")
            result = await db.execute(
                select(SysAiModelConfig)
                .where(
                    SysAiModelConfig.user_id == user_id,
                    SysAiModelConfig.is_active == True,
                    SysAiModelConfig.model_type == 'chat'  # 只选择chat类型的模型
                )
                .order_by(
                    SysAiModelConfig.is_default.desc(),  # 优先默认模型
                    SysAiModelConfig.id.desc()  # 其次选最新的
                )
            )
            config_obj = result.scalars().first()

            if not config_obj:
                logger.warning(f"用户{user_id}没有可用的AI模型配置")
                return None

            # 3. 构造配置字典
            model_config = {
                'id': config_obj.id,
                'config_name': config_obj.config_name,
                'model_name': config_obj.model_name,
                'model_type': config_obj.model_type,
                'api_url': config_obj.api_url,
                'api_key': config_obj.api_key,
                'temperature': float(config_obj.temperature) if config_obj.temperature else 0.7,
                'max_tokens': config_obj.max_tokens or 2000,
                'is_default': config_obj.is_default
            }

            # 4. 缓存到Redis
            await cls.set_user_selected_model(user_id, model_config)

            return model_config

        except Exception as e:
            logger.error(f"获取用户{user_id}的模型配置失败: {e}")
            return None

    @classmethod
    async def set_user_selected_model(
        cls,
        user_id: int,
        model_config: Dict[str, Any]
    ) -> bool:
        """
        设置用户选择的AI模型配置到Redis

        Args:
            user_id: 用户ID
            model_config: 模型配置字典

        Returns:
            是否设置成功
        """
        cache_key = cls._get_cache_key(user_id)

        try:
            # 将配置序列化为JSON并存储到Redis
            await redis_client.setex(
                cache_key,
                cls.CACHE_EXPIRE_SECONDS,
                json.dumps(model_config, ensure_ascii=False)
            )
            logger.info(f"已缓存用户{user_id}的模型配置: {model_config.get('config_name')}")
            return True

        except Exception as e:
            logger.error(f"缓存用户{user_id}的模型配置失败: {e}")
            return False

    @classmethod
    async def update_user_selected_model(
        cls,
        user_id: int,
        model_id: int,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        更新用户选择的AI模型

        从数据库读取新模型配置并更新到Redis

        Args:
            user_id: 用户ID
            model_id: 新选择的模型ID
            db: 数据库会话

        Returns:
            更新后的模型配置字典
        """
        try:
            # 1. 从数据库获取模型配置
            result = await db.execute(
                select(SysAiModelConfig)
                .where(
                    SysAiModelConfig.id == model_id,
                    SysAiModelConfig.user_id == user_id,
                    SysAiModelConfig.is_active == True
                )
            )
            config_obj = result.scalar_one_or_none()

            if not config_obj:
                logger.error(f"模型配置不存在或未激活: model_id={model_id}, user_id={user_id}")
                return None

            # 2. 构造配置字典
            model_config = {
                'id': config_obj.id,
                'config_name': config_obj.config_name,
                'model_name': config_obj.model_name,
                'model_type': config_obj.model_type,
                'api_url': config_obj.api_url,
                'api_key': config_obj.api_key,
                'temperature': float(config_obj.temperature) if config_obj.temperature else 0.7,
                'max_tokens': config_obj.max_tokens or 2000,
                'is_default': config_obj.is_default
            }

            # 3. 更新到Redis
            await cls.set_user_selected_model(user_id, model_config)

            logger.info(f"用户{user_id}切换到模型: {model_config['config_name']}")
            return model_config

        except Exception as e:
            logger.error(f"更新用户{user_id}的模型配置失败: {e}")
            return None

    @classmethod
    async def clear_user_model_cache(cls, user_id: int) -> bool:
        """
        清除用户的模型缓存

        Args:
            user_id: 用户ID

        Returns:
            是否清除成功
        """
        cache_key = cls._get_cache_key(user_id)

        try:
            await redis_client.delete(cache_key)
            logger.info(f"已清除用户{user_id}的模型缓存")
            return True

        except Exception as e:
            logger.error(f"清除用户{user_id}的模型缓存失败: {e}")
            return False
