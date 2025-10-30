import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
import uvicorn
import logging
from api.endpoints import (
    conversation, 
    dataset_upload as dataset, 
    file_preview,
    document_preview,
    progress_stream,
    ai_model_config,
    minio_management,
    generate_chart,
    insight_analysis,
    insight_analysis_stream,
    embedding_config,
    model_selection,
    insight_task,
    monitoring
)
from contextlib import asynccontextmanager
from api.dependencies.dependencies import redis_client, engine
from core.logging import setup_logging
from db.init_db import init_db, insert_default_data  # 导入数据库初始化和插入默认数据函数

# 设置日志记录
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时执行的代码
    await init_db()  # 调用数据库初始化函数
    await insert_default_data()  # 插入默认数据
    yield
    # 在应用关闭时执行的代码
    await redis_client.close()
    await engine.dispose()

# 创建 FastAPI 实例并传入 lifespan 事件处理程序
app = FastAPI(lifespan=lifespan)

# 配置CORS
origins = [
    settings.FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(conversation.router, prefix="/api", tags=["对话"])
app.include_router(dataset.router, prefix="/api", tags=["数据集"])
app.include_router(file_preview.router, prefix="/api", tags=["文件预览"])
app.include_router(document_preview.router, prefix="/api", tags=["通用文档预览"])
app.include_router(progress_stream.router, prefix="/api", tags=["进度流"])

# 添加其他必要的路由
app.include_router(ai_model_config.router, prefix="/api", tags=["AI模型配置"])
app.include_router(minio_management.router, prefix="/api", tags=["MinIO管理"])
app.include_router(generate_chart.router, prefix="/api", tags=["图表生成"])
app.include_router(insight_analysis.router, prefix="/api", tags=["洞察分析"])
app.include_router(insight_analysis_stream.router, prefix="/api", tags=["流式洞察分析"])
app.include_router(embedding_config.router, prefix="/api", tags=["嵌入配置"])
app.include_router(model_selection.router, prefix="/api", tags=["模型选择"])
app.include_router(insight_task.router, prefix="/api", tags=["洞察任务"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["监控"])

if __name__ == "__main__":
    uvicorn.run(app='main:app', host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=settings.RELOAD)