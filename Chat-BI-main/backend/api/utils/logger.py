import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class ErrorLogger:
    """
    增强的错误日志记录器
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 配置错误日志
        self.error_logger = self._setup_logger(
            "error_logger", self.log_dir / "errors.log", logging.ERROR
        )

        # 配置访问日志
        self.access_logger = self._setup_logger(
            "access_logger", self.log_dir / "access.log", logging.INFO
        )

        # 配置性能日志
        self.performance_logger = self._setup_logger(
            "performance_logger", self.log_dir / "performance.log", logging.INFO
        )

    def _setup_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # 避免重复添加处理器
        if not logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)

            # 格式化器
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

        return logger

    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> str:
        """
        记录错误信息

        Args:
            error: 异常对象
            context: 错误上下文信息
            user_id: 用户ID
            endpoint: API端点

        Returns:
            错误ID用于追踪
        """
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error)}"

        error_info = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "user_id": user_id,
            "endpoint": endpoint,
            "context": context or {},
        }

        self.error_logger.error(json.dumps(error_info, ensure_ascii=False, indent=2))
        return error_id

    def log_access(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        response_time: Optional[float] = None,
        status_code: Optional[int] = None,
    ):
        """记录访问日志"""
        access_info = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "ip_address": ip_address,
            "response_time": response_time,
            "status_code": status_code,
        }

        self.access_logger.info(json.dumps(access_info, ensure_ascii=False))

    def log_performance(
        self, operation: str, duration: float, details: Dict[str, Any] = None
    ):
        """记录性能日志"""
        performance_info = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration": duration,
            "details": details or {},
        }

        self.performance_logger.info(json.dumps(performance_info, ensure_ascii=False))


# 全局日志记录器实例
error_logger = ErrorLogger()
