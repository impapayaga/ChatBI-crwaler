"""
进度流式传输接口 - 使用Server-Sent Events实现实时进度推送
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.dependencies import get_async_session, redis_client
import asyncio
import json
import logging
from typing import AsyncGenerator

router = APIRouter()
logger = logging.getLogger(__name__)

class ProgressManager:
    """进度管理器 - 使用Redis存储和广播进度信息"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def update_progress(self, task_id: str, step: str, progress: int, message: str = "", error: str = ""):
        """更新任务进度"""
        progress_data = {
            "task_id": task_id,
            "step": step,
            "progress": progress,
            "message": message,
            "error": error,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # 存储到Redis
        await self.redis.setex(f"progress:{task_id}", 300, json.dumps(progress_data))  # 5分钟过期
        
        # 发布到频道供SSE订阅
        await self.redis.publish(f"progress_channel:{task_id}", json.dumps(progress_data))
        
        logger.info(f"进度更新: {task_id} - {step} ({progress}%) - {message}")
    
    async def get_progress(self, task_id: str) -> dict:
        """获取任务当前进度"""
        progress_json = await self.redis.get(f"progress:{task_id}")
        if progress_json:
            return json.loads(progress_json)
        return None
    
    async def subscribe_progress(self, task_id: str) -> AsyncGenerator[str, None]:
        """订阅任务进度更新"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"progress_channel:{task_id}")
        
        try:
            # 首先发送当前进度（如果存在）
            current_progress = await self.get_progress(task_id)
            if current_progress:
                yield f"data: {json.dumps(current_progress)}\n\n"
            
            # 监听新的进度更新
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield f"data: {message['data'].decode()}\n\n"
                    
                    # 如果任务完成或出错，结束流
                    try:
                        data = json.loads(message['data'].decode())
                        if data.get('progress') >= 100 or data.get('error'):
                            break
                    except:
                        pass
                        
        except asyncio.CancelledError:
            logger.info(f"进度订阅被取消: {task_id}")
        finally:
            await pubsub.unsubscribe(f"progress_channel:{task_id}")
            await pubsub.close()

# 全局进度管理器实例
progress_manager = None

def get_progress_manager():
    """获取进度管理器实例"""
    global progress_manager
    if progress_manager is None:
        progress_manager = ProgressManager(redis_client)
    return progress_manager

@router.get("/progress/{task_id}")
async def stream_progress(task_id: str):
    """
    流式传输任务进度 - Server-Sent Events
    
    Args:
        task_id: 任务ID
        
    Returns:
        StreamingResponse: SSE格式的进度流
    """
    logger.info(f"开始流式传输进度: {task_id}")
    
    manager = get_progress_manager()
    
    async def generate_progress_stream():
        """生成进度流数据"""
        try:
            # 设置SSE头部
            yield "event: progress\n"
            yield "retry: 1000\n"
            yield "\n"
            
            # 订阅并流式传输进度
            async for progress_data in manager.subscribe_progress(task_id):
                yield progress_data
                
        except Exception as e:
            logger.error(f"进度流传输错误: {e}")
            error_data = {
                "task_id": task_id,
                "error": str(e),
                "step": "error",
                "progress": 0
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/progress/{task_id}/status")
async def get_progress_status(task_id: str):
    """
    获取任务当前进度状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        dict: 当前进度信息
    """
    manager = get_progress_manager()
    progress = await manager.get_progress(task_id)
    
    if progress:
        return {
            "success": True,
            "data": progress
        }
    else:
        return {
            "success": False,
            "message": "任务进度不存在或已过期"
        }