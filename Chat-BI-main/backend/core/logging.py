import logging
from core.config import settings

def setup_logging():
    logging.basicConfig(
        level=settings.FASTAPI_LOG_LEVEL.upper(),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 减少SQLAlchemy日志输出
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)