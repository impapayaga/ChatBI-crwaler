from fastapi import APIRouter
from . import generate_chart, insight_analysis, ai_model_config, insight_analysis_stream, dataset_upload, embedding_config, model_selection, conversation, minio_management, insight_task, monitoring, progress_stream, file_preview

router = APIRouter()


router.include_router(generate_chart.router, prefix="/api", tags=["generate_chart"])
router.include_router(insight_analysis.router, prefix="/api", tags=["insight_analysis"])
router.include_router(ai_model_config.router, prefix="/api", tags=["ai_model_config"])
router.include_router(insight_analysis_stream.router, prefix="/api", tags=["insight_analysis_stream"])
router.include_router(dataset_upload.router, prefix="/api", tags=["dataset"])
router.include_router(embedding_config.router, prefix="/api", tags=["embedding_config"])
router.include_router(model_selection.router, prefix="/api", tags=["model_selection"])
router.include_router(conversation.router, prefix="/api", tags=["conversation"])
router.include_router(minio_management.router, prefix="/api", tags=["minio_management"])
router.include_router(insight_task.router, prefix="/api", tags=["insight_task"])
router.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
router.include_router(progress_stream.router, prefix="/api", tags=["progress"])
router.include_router(file_preview.router, prefix="/api", tags=["file_preview"])