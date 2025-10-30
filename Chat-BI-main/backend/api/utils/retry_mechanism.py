import asyncio
import functools
import logging
from typing import Callable, Any, Optional, List, Type
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RetryConfig:
    """重试配置类"""
    
    def __init__(self,
                 max_attempts: int = 3,
                 delay: float = 1.0,
                 backoff_factor: float = 2.0,
                 max_delay: float = 60.0,
                 exceptions: Optional[List[Type[Exception]]] = None):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.exceptions = exceptions or [Exception]

def retry_async(config: RetryConfig = None):
    """
    异步函数重试装饰器
    
    Args:
        config: 重试配置
        
    Returns:
        装饰器函数
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = config.delay
            
            for attempt in range(config.max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"函数 {func.__name__} 在第 {attempt + 1} 次尝试后成功")
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否是可重试的异常
                    if not any(isinstance(e, exc_type) for exc_type in config.exceptions):
                        logger.error(f"函数 {func.__name__} 遇到不可重试的异常: {str(e)}")
                        raise e
                    
                    if attempt < config.max_attempts - 1:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {str(e)}, {current_delay}秒后重试")
                        await asyncio.sleep(current_delay)
                        current_delay = min(current_delay * config.backoff_factor, config.max_delay)
                    else:
                        logger.error(f"函数 {func.__name__} 在 {config.max_attempts} 次尝试后仍然失败")
            
            raise last_exception
        
        return wrapper
    return decorator

def retry_sync(config: RetryConfig = None):
    """
    同步函数重试装饰器
    
    Args:
        config: 重试配置
        
    Returns:
        装饰器函数
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            
            last_exception = None
            current_delay = config.delay
            
            for attempt in range(config.max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"函数 {func.__name__} 在第 {attempt + 1} 次尝试后成功")
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否是可重试的异常
                    if not any(isinstance(e, exc_type) for exc_type in config.exceptions):
                        logger.error(f"函数 {func.__name__} 遇到不可重试的异常: {str(e)}")
                        raise e
                    
                    if attempt < config.max_attempts - 1:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {str(e)}, {current_delay}秒后重试")
                        time.sleep(current_delay)
                        current_delay = min(current_delay * config.backoff_factor, config.max_delay)
                    else:
                        logger.error(f"函数 {func.__name__} 在 {config.max_attempts} 次尝试后仍然失败")
            
            raise last_exception
        
        return wrapper
    return decorator

class CircuitBreaker:
    """
    熔断器模式实现
    """
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                    logger.info(f"熔断器进入半开状态，尝试调用 {func.__name__}")
                else:
                    raise Exception(f"熔断器开启，拒绝调用 {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        return (self.last_failure_time and 
                datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout))
    
    def _on_success(self):
        """成功调用时的处理"""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.info("熔断器重置为关闭状态")
    
    def _on_failure(self):
        """失败调用时的处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"熔断器开启，失败次数: {self.failure_count}")

# 预定义的重试配置
AI_SERVICE_RETRY = RetryConfig(
    max_attempts=3,
    delay=2.0,
    backoff_factor=2.0,
    exceptions=[ConnectionError, TimeoutError]
)

DATABASE_RETRY = RetryConfig(
    max_attempts=2,
    delay=1.0,
    backoff_factor=1.5,
    exceptions=[ConnectionError]
)

FILE_OPERATION_RETRY = RetryConfig(
    max_attempts=3,
    delay=0.5,
    backoff_factor=1.5,
    exceptions=[IOError, OSError]
)