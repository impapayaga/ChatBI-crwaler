"""
错误处理工具函数
"""

def get_error_suggestions(error_type: str) -> list:
    """
    根据错误类型返回相应的建议
    """
    suggestions = {
        "column_not_found": [
            "检查数据集中的列名是否正确",
            "确保列名不包含特殊字符或空格",
            "尝试重新上传数据文件",
            "联系管理员检查数据集状态"
        ],
        "connection_error": [
            "检查网络连接是否正常",
            "稍后重试",
            "如果问题持续存在，请联系技术支持"
        ],
        "sql_error": [
            "检查查询条件是否正确",
            "确保数据集已完成解析",
            "尝试简化查询条件",
            "联系管理员检查数据库状态"
        ],
        "ai_model_error": [
            "AI服务可能暂时不可用，请稍后重试",
            "检查AI模型配置是否正确",
            "联系管理员检查AI服务状态"
        ],
        "dataset_error": [
            "检查数据集是否已完成上传和解析",
            "确保数据集格式正确",
            "尝试重新上传数据文件",
            "检查数据集权限设置"
        ],
        "permission_error": [
            "您可能没有访问此数据集的权限",
            "联系管理员申请相应权限",
            "检查用户账户状态"
        ],
        "file_error": [
            "检查文件格式是否支持",
            "确保文件大小在允许范围内",
            "尝试重新上传文件",
            "联系管理员了解文件要求"
        ],
        "unknown_error": [
            "请稍后重试",
            "如果问题持续存在，请联系技术支持",
            "提供详细的错误信息以便排查"
        ]
    }
    
    return suggestions.get(error_type, suggestions["unknown_error"])


def format_error_message(error_type: str, original_error: str, user_query: str = "") -> dict:
    """
    格式化错误消息，返回结构化的错误信息
    """
    error_titles = {
        "column_not_found": "数据列未找到",
        "connection_error": "网络连接错误", 
        "sql_error": "数据查询错误",
        "ai_model_error": "AI服务错误",
        "dataset_error": "数据集处理错误",
        "permission_error": "权限不足",
        "file_error": "文件处理错误",
        "unknown_error": "未知错误"
    }
    
    friendly_messages = {
        "column_not_found": "数据集中未找到指定的列，可能是列名包含特殊字符或数据结构发生变化",
        "connection_error": "网络连接超时，请检查网络连接后重试",
        "sql_error": "数据查询失败，请检查查询条件或联系管理员",
        "ai_model_error": "AI服务暂时不可用，请稍后重试",
        "dataset_error": "数据集处理失败，请检查数据集状态或重新上传",
        "permission_error": "权限不足，请联系管理员",
        "file_error": "文件处理失败，请检查文件格式和大小",
        "unknown_error": "生成图表时发生未知错误"
    }
    
    return {
        "title": error_titles.get(error_type, error_titles["unknown_error"]),
        "message": friendly_messages.get(error_type, friendly_messages["unknown_error"]),
        "original_error": original_error,
        "suggestions": get_error_suggestions(error_type),
        "error_type": error_type,
        "user_query": user_query
    }