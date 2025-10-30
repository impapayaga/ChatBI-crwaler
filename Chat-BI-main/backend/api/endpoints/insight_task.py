from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
import json

from api.dependencies.dependencies import redis_client
from api.utils.ai_utils import generate_insight_analysis

router = APIRouter()
logger = logging.getLogger(__name__)


class InsightTaskRequest(BaseModel):
    user_input: str
    data: str  # JSON格式的数据
    user_id: int = 1


class InsightTaskResponse(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    message: str


class InsightTaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int  # 0-100
    result: str = ""
    error: str = ""
    created_at: str
    completed_at: str = ""


async def execute_insight_analysis_task(task_id: str, user_input: str, data_json: str, user_id: int):
    """执行洞察分析任务"""
    try:
        # 更新任务状态为运行中
        await update_task_status(task_id, "running", 10)
        
        # 解析数据
        import pandas as pd
        data = json.loads(data_json)
        df = pd.DataFrame(data)
        
        # 更新进度
        await update_task_status(task_id, "running", 30)
        
        # 执行洞察分析
        logger.info(f"开始执行洞察分析任务: {task_id}")
        insight_result = await generate_insight_analysis(user_input, df, user_id)
        
        # 更新进度
        await update_task_status(task_id, "running", 80)
        
        if insight_result:
            # 保存洞察分析到数据库
            try:
                from db.session import async_session
                from services.conversation_service import save_assistant_message
                
                # 获取任务数据中的conversation_id
                task_data = await redis_client.get(f"insight_task:{task_id}")
                if task_data:
                    task_info = json.loads(task_data)
                    conversation_id = task_info.get("conversation_id")
                    
                    if conversation_id:
                        async with async_session() as db:
                            await save_assistant_message(
                                db,
                                conversation_id,
                                content=insight_result,
                                response_time=0,  # 洞察分析是后台任务，不计算响应时间
                                tokens_used=None  # 洞察分析的token使用量在流式分析中已记录
                            )
                        logger.info(f"洞察分析已保存到数据库: conversation_id={conversation_id}, 内容长度={len(insight_result)}")
            except Exception as e:
                logger.error(f"保存洞察分析到数据库失败: {e}")
            
            # 任务完成
            await update_task_status(
                task_id, 
                "completed", 
                100, 
                result=insight_result,
                completed_at=datetime.now().isoformat()
            )
            logger.info(f"洞察分析任务完成: {task_id}")
        else:
            await update_task_status(task_id, "failed", 100, error="生成洞察分析失败")
            logger.error(f"洞察分析任务失败: {task_id}")
            
    except Exception as e:
        error_msg = f"执行洞察分析任务出错: {str(e)}"
        await update_task_status(task_id, "failed", 100, error=error_msg)
        logger.error(f"任务 {task_id} 执行失败: {e}")


async def update_task_status(task_id: str, status: str, progress: int, result: str = None, error: str = None, completed_at: str = None):
    """更新任务状态"""
    try:
        # 获取现有任务信息
        existing_data = await redis_client.get(f"insight_task:{task_id}")
        if existing_data:
            task_data = json.loads(existing_data)
        else:
            task_data = {
                "task_id": task_id,
                "created_at": datetime.now().isoformat()
            }
        
        # 更新状态
        task_data.update({
            "status": status,
            "progress": progress,
            "updated_at": datetime.now().isoformat()
        })
        
        if result:
            task_data["result"] = result
        if error:
            task_data["error"] = error
        if completed_at:
            task_data["completed_at"] = completed_at
            
        # 存储到Redis，设置24小时过期
        await redis_client.set(
            f"insight_task:{task_id}", 
            json.dumps(task_data, ensure_ascii=False), 
            ex=86400  # 24小时
        )
        
    except Exception as e:
        logger.error(f"更新任务状态失败: {e}")


@router.post("/insight_task", response_model=InsightTaskResponse)
async def create_insight_task(
    request: InsightTaskRequest, 
    background_tasks: BackgroundTasks
):
    """创建洞察分析任务"""
    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        await update_task_status(task_id, "pending", 0)
        
        # 添加后台任务
        background_tasks.add_task(
            execute_insight_analysis_task,
            task_id,
            request.user_input,
            request.data,
            request.user_id
        )
        
        logger.info(f"创建洞察分析任务: {task_id}")
        
        return InsightTaskResponse(
            task_id=task_id,
            status="pending",
            message="洞察分析任务已创建，正在处理中..."
        )
        
    except Exception as e:
        logger.error(f"创建洞察分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/insight_task/{task_id}", response_model=InsightTaskStatus)
async def get_insight_task_status(task_id: str):
    """获取洞察分析任务状态"""
    try:
        task_data = await redis_client.get(f"insight_task:{task_id}")
        
        if not task_data:
            logger.warning(f"任务不存在或已过期: {task_id}")
            raise HTTPException(status_code=404, detail="任务不存在或已过期")
        
        task_info = json.loads(task_data)
        logger.info(f"获取任务状态: {task_id}, 状态: {task_info.get('status')}, 进度: {task_info.get('progress')}")
        
        return InsightTaskStatus(
            task_id=task_id,  # 使用URL参数中的task_id
            status=task_info["status"],
            progress=task_info.get("progress", 0),
            result=task_info.get("result") or "",
            error=task_info.get("error") or "",
            created_at=task_info.get("created_at", ""),
            completed_at=task_info.get("completed_at") or ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.delete("/insight_task/{task_id}")
async def delete_insight_task(task_id: str):
    """删除洞察分析任务"""
    try:
        result = await redis_client.delete(f"insight_task:{task_id}")
        
        if result == 0:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {"message": "任务已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")