"""
统一错误处理装饰器和工具函数
"""
import logging
from functools import wraps
from fastapi import HTTPException
from typing import Callable, Any, Dict
from .error_utils import format_error_message

logger = logging.getLogger(__name__)


def handle_api_errors(error_context: str = "API操作"):
    """
    API错误处理装饰器
    
    Args:
        error_context: 错误上下文描述
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # 重新抛出HTTP异常
                raise
            except Exception as e:
                logger.exception(f"{error_context}失败: {e}")
                
                # 分析错误类型
                error_message = str(e)
                error_type = classify_error(error_message)
                
                # 格式化错误信息
                formatted_error = format_error_message(error_type, error_message)
                
                # 抛出标准化的HTTP异常
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": formatted_error['message'],
                        "error_type": error_type,
                        "title": formatted_error['title'],
                        "suggestions": formatted_error['suggestions'],
                        "original_error": error_message
                    }
                )
        return wrapper
    return decorator


def classify_error(error_message: str) -> str:
    """
    根据错误消息分类错误类型
    
    Args:
        error_message: 错误消息
        
    Returns:
        错误类型
    """
    error_message_lower = error_message.lower()
    
    if "column" in error_message and "not found" in error_message:
        return "column_not_found"
    elif "connection" in error_message_lower or "timeout" in error_message_lower:
        return "connection_error"
    elif "sql" in error_message_lower or "query" in error_message_lower:
        return "sql_error"
    elif "ai" in error_message_lower or "model" in error_message_lower:
        return "ai_model_error"
    elif "dataset" in error_message_lower:
        return "dataset_error"
    elif "permission" in error_message_lower or "access" in error_message_lower:
        return "permission_error"
    elif "file" in error_message_lower and ("size" in error_message_lower or "format" in error_message_lower):
        return "file_error"
    elif "network" in error_message_lower or "连接" in error_message:
        return "connection_error"
    else:
        return "unknown_error"


def create_error_response(
    error_type: str, 
    error_message: str, 
    user_context: str = "",
    additional_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    创建标准化的错误响应
    
    Args:
        error_type: 错误类型
        error_message: 错误消息
        user_context: 用户上下文
        additional_data: 额外数据
        
    Returns:
        标准化错误响应
    """
    formatted_error = format_error_message(error_type, error_message, user_context)
    
    response = {
        "error": formatted_error['message'],
        "error_type": error_type,
        "title": formatted_error['title'],
        "suggestions": formatted_error['suggestions'],
        "is_error": True,
        "success": False
    }
    
    if additional_data:
        response.update(additional_data)
    
    return response