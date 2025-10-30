from fastapi import APIRouter, HTTPException, Query
from api.utils.monitoring import error_monitor
from typing import Optional

router = APIRouter()

@router.get("/error-stats")
async def get_error_statistics(
    hours: int = Query(24, description="分析最近几小时的错误", ge=1, le=168)
):
    """
    获取错误统计信息
    
    Args:
        hours: 分析时间范围（小时）
        
    Returns:
        错误统计报告
    """
    try:
        stats = await error_monitor.analyze_error_logs(hours=hours)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误统计失败: {str(e)}")

@router.get("/error-trends")
async def get_error_trends(
    days: int = Query(7, description="分析最近几天的错误趋势", ge=1, le=30)
):
    """
    获取错误趋势分析
    
    Args:
        days: 分析时间范围（天）
        
    Returns:
        错误趋势报告
    """
    try:
        trends = await error_monitor.get_error_trends(days=days)
        return {
            "success": True,
            "data": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误趋势失败: {str(e)}")

@router.get("/performance-stats")
async def get_performance_statistics(
    hours: int = Query(24, description="分析最近几小时的性能数据", ge=1, le=168)
):
    """
    获取性能统计信息
    
    Args:
        hours: 分析时间范围（小时）
        
    Returns:
        性能统计报告
    """
    try:
        stats = await error_monitor.get_performance_stats(hours=hours)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")

@router.get("/health-check")
async def health_check():
    """
    系统健康检查
    
    Returns:
        系统状态信息
    """
    try:
        # 获取最近1小时的错误统计
        error_stats = await error_monitor.analyze_error_logs(hours=1)
        total_errors = error_stats.get("total_errors", 0)
        
        # 判断系统健康状态
        if total_errors == 0:
            status = "healthy"
            message = "系统运行正常"
        elif total_errors < 10:
            status = "warning"
            message = f"检测到 {total_errors} 个错误，需要关注"
        else:
            status = "critical"
            message = f"检测到 {total_errors} 个错误，需要立即处理"
        
        return {
            "success": True,
            "data": {
                "status": status,
                "message": message,
                "errors_last_hour": total_errors,
                "timestamp": error_stats.get("generated_at")
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "status": "unknown",
                "message": f"健康检查失败: {str(e)}",
                "errors_last_hour": -1
            }
        }