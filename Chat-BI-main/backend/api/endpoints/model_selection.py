"""
AI模型选择API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from api.dependencies.dependencies import get_async_session
from services.model_cache_service import ModelCacheService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ModelSelectionRequest(BaseModel):
    """模型选择请求"""
    user_id: int
    model_id: int


class ModelSelectionResponse(BaseModel):
    """模型选择响应"""
    success: bool
    message: str
    model_data: dict = None


@router.post("/select-model", response_model=ModelSelectionResponse)
async def select_model(
    request: ModelSelectionRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    用户选择AI模型

    将选择的模型配置缓存到Redis,供后续AI调用使用

    Args:
        request: 包含user_id和model_id的请求
        db: 数据库会话

    Returns:
        包含成功状态和模型配置的响应
    """
    try:
        logger.info(f"用户{request.user_id}选择模型: {request.model_id}")

        # 更新用户选择的模型到Redis
        model_config = await ModelCacheService.update_user_selected_model(
            user_id=request.user_id,
            model_id=request.model_id,
            db=db
        )

        if not model_config:
            raise HTTPException(
                status_code=404,
                detail="模型配置不存在或未激活"
            )

        return ModelSelectionResponse(
            success=True,
            message=f"已切换到模型: {model_config['config_name']}",
            model_data=model_config
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"选择模型失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"选择模型失败: {str(e)}"
        )


@router.get("/current-model/{user_id}")
async def get_current_model(
    user_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户当前选择的AI模型

    优先从Redis读取,如果Redis中没有则从数据库读取默认模型

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        当前选择的模型配置
    """
    try:
        logger.info(f"获取用户{user_id}当前模型")

        model_config = await ModelCacheService.get_user_selected_model(
            user_id=user_id,
            db=db
        )

        if not model_config:
            raise HTTPException(
                status_code=404,
                detail="未找到可用的AI模型配置"
            )

        return {
            "success": True,
            "model_config": model_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前模型失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取当前模型失败: {str(e)}"
        )
