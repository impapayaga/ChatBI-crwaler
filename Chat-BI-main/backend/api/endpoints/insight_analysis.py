from fastapi import APIRouter, HTTPException, Query
import logging
from api.dependencies.dependencies import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/insight_analysis")
async def get_insight_analysis(
    user_input: str = Query(..., description="User input for insight analysis")
):
    try:
        # 从 Redis 中获取洞察分析结果
        insight_analysis = await redis_client.get(f"insight_analysis:{user_input}")
        if insight_analysis:
            return {"insight_analysis": insight_analysis.decode("utf-8")}
        else:
            # 返回默认响应而不是抛出404错误
            return {"insight_analysis": "暂无洞察分析结果，请稍后再试"}
    except Exception as e:
        logger.exception("An error occurred while fetching insight analysis")
        # 返回默认响应而不是抛出500错误
        return {"insight_analysis": "获取洞察分析时发生错误，请稍后再试"}
