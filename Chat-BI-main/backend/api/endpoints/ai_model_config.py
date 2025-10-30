from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
import logging
import time
import aiohttp
import asyncio

from models.sys_ai_model_config import SysAiModelConfig
from schemas.ai_model_config import (
    AIModelConfigCreate,
    AIModelConfigUpdate,
    AIModelConfigResponse,
    AIModelConfigList
)
from db.session import async_session

router = APIRouter()


# 数据库依赖
async def get_db():
    async with async_session() as session:
        yield session


@router.post("/ai-model-configs", response_model=AIModelConfigResponse, status_code=201)
async def create_ai_model_config(
    config: AIModelConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建AI模型配置"""
    try:
        # 如果设置为默认配置，先取消同类型的其他默认配置
        if config.is_default:
            await db.execute(
                update(SysAiModelConfig)
                .where(
                    SysAiModelConfig.user_id == config.user_id,
                    SysAiModelConfig.model_type == config.model_type  # 只取消同类型的默认配置
                )
                .values(is_default=False)
            )

        # 创建新配置
        db_config = SysAiModelConfig(**config.model_dump())
        db.add(db_config)
        await db.commit()
        await db.refresh(db_config)

        logging.info(f"AI模型配置创建成功: id={db_config.id}, user_id={config.user_id}")
        return db_config
    except Exception as e:
        await db.rollback()
        logging.error(f"创建AI模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建配置失败: {str(e)}")


@router.get("/ai-model-configs", response_model=AIModelConfigList)
async def get_ai_model_configs(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取用户的所有AI模型配置"""
    try:
        # 查询总数
        count_result = await db.execute(
            select(SysAiModelConfig).where(SysAiModelConfig.user_id == user_id)
        )
        total = len(count_result.all())

        # 查询配置列表
        result = await db.execute(
            select(SysAiModelConfig)
            .where(SysAiModelConfig.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(SysAiModelConfig.created_at.desc())
        )
        configs = result.scalars().all()

        return AIModelConfigList(total=total, items=configs)
    except Exception as e:
        logging.error(f"获取AI模型配置列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置列表失败: {str(e)}")


@router.get("/ai-model-configs/{config_id}", response_model=AIModelConfigResponse)
async def get_ai_model_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取指定的AI模型配置"""
    try:
        result = await db.execute(
            select(SysAiModelConfig).where(SysAiModelConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        return config
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取AI模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get("/ai-model-configs/default/{user_id}", response_model=AIModelConfigResponse)
async def get_default_ai_model_config(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户的默认AI模型配置"""
    try:
        result = await db.execute(
            select(SysAiModelConfig)
            .where(
                SysAiModelConfig.user_id == user_id,
                SysAiModelConfig.is_default == True,
                SysAiModelConfig.is_active == True
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="未找到默认配置")

        return config
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取默认AI模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取默认配置失败: {str(e)}")


@router.put("/ai-model-configs/{config_id}", response_model=AIModelConfigResponse)
async def update_ai_model_config(
    config_id: int,
    config_update: AIModelConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新AI模型配置"""
    try:
        # 查询配置是否存在
        result = await db.execute(
            select(SysAiModelConfig).where(SysAiModelConfig.id == config_id)
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            raise HTTPException(status_code=404, detail="配置不存在")

        # 如果设置为默认配置，先取消同类型的其他默认配置
        if config_update.is_default:
            await db.execute(
                update(SysAiModelConfig)
                .where(
                    SysAiModelConfig.user_id == db_config.user_id,
                    SysAiModelConfig.model_type == db_config.model_type,  # 只取消同类型的默认配置
                    SysAiModelConfig.id != config_id
                )
                .values(is_default=False)
            )

        # 更新配置
        update_data = config_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_config, key, value)

        await db.commit()
        await db.refresh(db_config)

        logging.info(f"AI模型配置更新成功: id={config_id}")
        return db_config
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logging.error(f"更新AI模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.delete("/ai-model-configs/{config_id}")
async def delete_ai_model_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除AI模型配置"""
    try:
        result = await db.execute(
            select(SysAiModelConfig).where(SysAiModelConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        await db.execute(
            delete(SysAiModelConfig).where(SysAiModelConfig.id == config_id)
        )
        await db.commit()

        logging.info(f"AI模型配置删除成功: id={config_id}")
        return {"message": "配置删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logging.error(f"删除AI模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除配置失败: {str(e)}")


@router.post("/ai-model-configs/test")
async def test_ai_model_config(
    api_url: str,
    api_key: str,
    model_name: str,
    model_type: str = "chat",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    test_message: str = "Hello, this is a test message."
):
    """测试AI模型配置是否可用"""
    start_time = time.time()

    try:
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 根据模型类型构建不同的请求体
        if model_type == "embedding":
            # Embedding 模型测试 (按照硅基流动标准格式)
            data = {
                "model": model_name,
                "input": test_message
            }
        else:
            # Chat/Generate 模型测试
            data = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": test_message
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

        # 发送异步HTTP请求
        timeout = aiohttp.ClientTimeout(total=30)  # 30秒超时
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()
                    response_time = int((end_time - start_time) * 1000)

                    # 根据模型类型检查响应格式
                    if model_type == "embedding":
                        # 检查 embedding 响应格式
                        if 'data' in result and len(result['data']) > 0:
                            embedding = result['data'][0].get('embedding', [])
                            if embedding and len(embedding) > 0:
                                return {
                                    "success": True,
                                    "responseTime": response_time,
                                    "message": "Embedding 模型连接测试成功",
                                    "response": f"生成了 {len(embedding)} 维的向量表示"
                                }
                            else:
                                return {
                                    "success": False,
                                    "message": "Embedding 响应格式异常：未返回向量数据",
                                    "details": str(result)
                                }
                        else:
                            return {
                                "success": False,
                                "message": "Embedding 响应格式异常：缺少 data 字段",
                                "details": str(result)
                            }
                    else:
                        # 检查 chat/generate 响应格式
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            return {
                                "success": True,
                                "responseTime": response_time,
                                "message": "连接测试成功",
                                "response": content[:100] + "..." if len(content) > 100 else content
                            }
                        else:
                            return {
                                "success": False,
                                "message": "响应格式异常",
                                "details": str(result)
                            }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "message": f"HTTP {response.status}: {error_text}"
                    }

    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": "请求超时，请检查网络连接或API地址"
        }
    except aiohttp.ClientError as e:
        return {
            "success": False,
            "message": f"网络请求失败: {str(e)}"
        }
    except Exception as e:
        logging.error(f"测试AI配置失败: {e}")
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }
