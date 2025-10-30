"""
数据集文件上传API端点
支持CSV和Excel文件上传
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from datetime import datetime
import logging
import os
import hashlib

from models.sys_dataset import SysDataset
from core.minio_client import minio_client
from core.config import settings
from api.dependencies.dependencies import get_async_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload_dataset")
async def upload_dataset(
    file: UploadFile = File(...),
    logical_name: str = None,
    description: str = None,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    上传CSV/Excel数据集文件

    Args:
        file: 上传的文件
        logical_name: 逻辑名称(可选)
        description: 数据集描述(可选)
        background_tasks: 后台任务
        session: 数据库会话

    Returns:
        {
            "dataset_id": "uuid",
            "status": "parsing",
            "message": "文件上传成功,正在解析..."
        }
    """
    # 校验文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}. 仅支持: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 读取文件数据
    try:
        file_data = await file.read()
        file_size = len(file_data)

        # 检查文件大小
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大: {file_size / 1024 / 1024:.2f}MB. 最大允许: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件为空")

        # 计算文件MD5哈希值
        file_md5 = hashlib.md5(file_data).hexdigest()
        logger.info(f"文件MD5: {file_md5}")

        # 检查是否已存在相同MD5的文件
        result = await session.execute(
            select(SysDataset).where(SysDataset.file_md5 == file_md5)
        )
        existing_dataset = result.scalar_one_or_none()

        if existing_dataset:
            logger.warning(f"重复上传检测: 文件MD5={file_md5} 已存在,数据集ID={existing_dataset.id}")
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "duplicate_file",
                    "message": f"该文件已上传过,文件名: {existing_dataset.name}",
                    "existing_dataset": {
                        "id": str(existing_dataset.id),
                        "name": existing_dataset.name,
                        "created_at": existing_dataset.created_at.isoformat() if existing_dataset.created_at else None
                    }
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取上传文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")

    # 生成数据集ID和存储路径
    dataset_id = uuid4()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    object_name = f"uploads/{dataset_id}_{timestamp}_{file.filename}"

    try:
        # 上传到MinIO
        file_path = minio_client.upload_file(
            file_data,
            object_name,
            content_type=file.content_type or "application/octet-stream"
        )
        logger.info(f"文件已上传到MinIO: {file_path}")

        # 创建数据集记录
        dataset = SysDataset(
            id=dataset_id,
            name=file.filename,
            logical_name=logical_name or file.filename.rsplit('.', 1)[0],
            description=description,
            original_file_path=file_path,
            file_size=file_size,
            file_md5=file_md5,
            parse_status='pending',
            embedding_status='pending'
        )
        session.add(dataset)
        await session.commit()
        await session.refresh(dataset)

        logger.info(f"数据集记录已创建: {dataset_id}")

        # 添加后台解析任务
        from services.dataset_parser import parse_dataset_task
        background_tasks.add_task(
            parse_dataset_task,
            str(dataset_id),
            file_path,
            file.filename
        )

        return {
            "dataset_id": str(dataset_id),
            "status": "parsing",
            "message": "文件上传成功,正在后台解析...",
            "file_name": file.filename,
            "file_size": file_size
        }

    except Exception as e:
        logger.error(f"上传数据集失败: {e}")
        # 清理MinIO中的文件
        try:
            minio_client.delete_file(object_name)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/dataset/{dataset_id}/status")
async def get_dataset_status(
    dataset_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    查询数据集解析状态

    Args:
        dataset_id: 数据集ID
        session: 数据库会话

    Returns:
        数据集状态信息
    """
    try:
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        return {
            "dataset_id": str(dataset.id),
            "name": dataset.name,
            "logical_name": dataset.logical_name,
            "parse_status": dataset.parse_status,
            "parse_progress": dataset.parse_progress,
            "chunk_status": dataset.chunk_status,
            "chunk_progress": dataset.chunk_progress,
            "chunk_error": dataset.chunk_error,
            "vectorize_status": dataset.vectorize_status,
            "vectorize_progress": dataset.vectorize_progress,
            "vectorize_error": dataset.vectorize_error,
            # 保留旧字段以向后兼容
            "embedding_status": dataset.embedding_status,
            "embedding_progress": dataset.embedding_progress,
            "embedding_error": dataset.embedding_error,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "error_message": dataset.error_message,
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询数据集状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/datasets")
async def list_datasets(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取数据集列表

    Args:
        skip: 跳过数量
        limit: 返回数量
        session: 数据库会话

    Returns:
        数据集列表
    """
    try:
        result = await session.execute(
            select(SysDataset)
            .order_by(SysDataset.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        datasets = result.scalars().all()

        return {
            "total": len(datasets),
            "datasets": [
                {
                    "id": str(d.id),
                    "name": d.name,
                    "logical_name": d.logical_name,
                    "parse_status": d.parse_status,
                    "chunk_status": d.chunk_status,
                    "vectorize_status": d.vectorize_status,
                    "row_count": d.row_count,
                    "column_count": d.column_count,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                }
                for d in datasets
            ]
        }

    except Exception as e:
        logger.error(f"获取数据集列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/dataset/{dataset_id}/retry_parse")
async def retry_parse_dataset(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    重新解析失败的数据集

    Args:
        dataset_id: 数据集ID
        background_tasks: 后台任务
        session: 数据库会话

    Returns:
        重试结果
    """
    try:
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        if dataset.parse_status not in ['failed', 'pending']:
            raise HTTPException(
                status_code=400,
                detail=f"数据集状态为 {dataset.parse_status}，无需重新解析"
            )

        # 重置状态
        dataset.parse_status = 'pending'
        dataset.parse_progress = 0
        dataset.error_message = None
        await session.commit()

        # 添加后台解析任务
        from services.dataset_parser import parse_dataset_task
        background_tasks.add_task(
            parse_dataset_task,
            str(dataset.id),
            dataset.original_file_path,
            dataset.name
        )

        return {
            "success": True,
            "message": "已开始重新解析",
            "dataset_id": dataset_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新解析数据集失败: {e}")
        raise HTTPException(status_code=500, detail=f"重试失败: {str(e)}")


@router.post("/dataset/{dataset_id}/retry_embedding")
async def retry_embedding(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    重新生成数据集的embedding向量

    Args:
        dataset_id: 数据集ID
        background_tasks: 后台任务
        session: 数据库会话

    Returns:
        重试结果
    """
    try:
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        if dataset.parse_status != 'parsed':
            raise HTTPException(
                status_code=400,
                detail=f"数据集解析状态为 {dataset.parse_status}，无法生成embedding"
            )

        if dataset.embedding_status == 'completed':
            raise HTTPException(
                status_code=400,
                detail="Embedding已完成，无需重新生成"
            )

        # 重置embedding状态
        dataset.embedding_status = 'pending'
        dataset.embedding_progress = 0
        dataset.embedding_error = None
        await session.commit()

        # 添加后台任务生成embedding
        async def retry_embedding_task():
            from db.session import async_session
            from services.embedding_service import generate_column_embeddings
            from sqlalchemy import select as sql_select
            from models.sys_dataset import SysDatasetColumn

            async with async_session() as sess:
                # 获取列信息
                col_result = await sess.execute(
                    sql_select(SysDatasetColumn)
                    .where(SysDatasetColumn.dataset_id == dataset_id)
                    .order_by(SysDatasetColumn.col_index)
                )
                columns = col_result.scalars().all()

                if not columns:
                    logger.error(f"数据集 {dataset_id} 没有列信息")
                    return

                # 构造schema_info
                schema_info = []
                for col in columns:
                    schema_info.append({
                        'name': col.col_name,
                        'type': col.col_type,
                        'stats': col.stats or {},
                        'samples': col.sample_values or []
                    })

                # 更新状态为embedding
                ds_result = await sess.execute(
                    sql_select(SysDataset).where(SysDataset.id == dataset_id)
                )
                ds = ds_result.scalar_one()
                ds.embedding_status = 'embedding'
                ds.embedding_progress = 0
                await sess.commit()

                try:
                    # 生成embedding
                    await generate_column_embeddings(str(dataset_id), schema_info)

                    # 更新为完成
                    ds.embedding_status = 'completed'
                    ds.embedding_progress = 100
                    await sess.commit()
                    logger.info(f"数据集 {dataset_id} embedding重新生成成功")

                except Exception as e:
                    logger.error(f"数据集 {dataset_id} embedding重新生成失败: {e}")
                    ds.embedding_status = 'failed'
                    ds.embedding_error = str(e)
                    await sess.commit()

        background_tasks.add_task(retry_embedding_task)

        return {
            "success": True,
            "message": "已开始重新生成embedding",
            "dataset_id": dataset_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新生成embedding失败: {e}")
        raise HTTPException(status_code=500, detail=f"重试失败: {str(e)}")


@router.delete("/dataset/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    删除数据集

    删除顺序：
    1. 删除向量embeddings (Qdrant)
    2. 删除MinIO中的文件
    3. 删除数据库记录

    Args:
        dataset_id: 数据集ID
        session: 数据库会话

    Returns:
        删除结果
    """
    try:
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            logger.warning(f"数据集不存在: {dataset_id}")
            raise HTTPException(status_code=404, detail="数据集不存在")

        logger.info(f"开始删除数据集: {dataset_id}, 名称: {dataset.name}")

        # 1. 删除Qdrant中的embeddings
        try:
            from services.embedding_service import delete_dataset_embeddings
            await delete_dataset_embeddings(dataset_id)
            logger.info(f"Qdrant embeddings删除成功: {dataset_id}")
        except Exception as e:
            logger.warning(f"删除Qdrant embeddings失败 (继续执行): {e}")

        # 2. 删除MinIO中的文件
        minio_errors = []

        # 删除原始文件
        if dataset.original_file_path:
            try:
                # 从完整路径提取对象名称
                # 例如: uploads/xxx_file.csv -> xxx_file.csv
                if '/' in dataset.original_file_path:
                    object_name = dataset.original_file_path
                else:
                    object_name = f"uploads/{dataset.original_file_path}"

                minio_client.delete_file(object_name)
                logger.info(f"原始文件删除成功: {object_name}")
            except Exception as e:
                error_msg = f"删除原始文件失败: {e}"
                logger.warning(error_msg)
                minio_errors.append(error_msg)

        # 删除Parquet文件
        if dataset.parsed_path:
            try:
                if '/' in dataset.parsed_path:
                    object_name = dataset.parsed_path
                else:
                    object_name = f"parquet/{dataset.parsed_path}"

                minio_client.delete_file(object_name)
                logger.info(f"Parquet文件删除成功: {object_name}")
            except Exception as e:
                error_msg = f"删除Parquet文件失败: {e}"
                logger.warning(error_msg)
                minio_errors.append(error_msg)

        # 3. 删除数据库记录
        await session.delete(dataset)
        await session.commit()
        logger.info(f"数据库记录删除成功: {dataset_id}")

        # 构建响应消息
        message = "数据集已成功删除"
        if minio_errors:
            message += f" (部分文件删除失败: {'; '.join(minio_errors)})"

        return {
            "success": True,
            "message": message,
            "dataset_id": dataset_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据集失败: {e}", exc_info=True)
        # 回滚数据库事务
        try:
            await session.rollback()
        except:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


@router.post("/dataset/{dataset_id}/retry_chunk")
async def retry_chunk(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    重新执行数据分片步骤

    Args:
        dataset_id: 数据集ID
        background_tasks: 后台任务
        session: 数据库会话

    Returns:
        重试结果
    """
    try:
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        if dataset.parse_status != 'parsed':
            raise HTTPException(
                status_code=400,
                detail=f"数据集解析状态为 {dataset.parse_status}，无法执行分片"
            )

        if dataset.chunk_status == 'completed' and dataset.vectorize_status == 'completed':
            raise HTTPException(
                status_code=400,
                detail="分片和向量化已全部完成，无需重试"
            )

        # 重置分片状态
        dataset.chunk_status = 'pending'
        dataset.chunk_progress = 0
        dataset.chunk_error = None
        # 同时重置向量化状态(因为需要重新分片)
        dataset.vectorize_status = 'pending'
        dataset.vectorize_progress = 0
        dataset.vectorize_error = None
        await session.commit()

        # 添加后台任务
        async def retry_chunk_task():
            from db.session import async_session
            from models.sys_dataset import SysDatasetColumn
            from sqlalchemy import select as sql_select
            from services.embedding_service import build_column_description, vectorize_columns

            async with async_session() as sess:
                # 获取列信息
                col_result = await sess.execute(
                    sql_select(SysDatasetColumn)
                    .where(SysDatasetColumn.dataset_id == dataset_id)
                    .order_by(SysDatasetColumn.col_index)
                )
                columns = col_result.scalars().all()

                if not columns:
                    logger.error(f"数据集 {dataset_id} 没有列信息")
                    return

                # 构造schema_info
                schema_info = []
                for col in columns:
                    schema_info.append({
                        'name': col.col_name,
                        'type': col.col_type,
                        'stats': col.stats or {},
                        'samples': col.sample_values or []
                    })

                # 更新为chunking状态
                ds_result = await sess.execute(
                    sql_select(SysDataset).where(SysDataset.id == dataset_id)
                )
                ds = ds_result.scalar_one()

                try:
                    # 执行分片
                    ds.chunk_status = 'chunking'
                    ds.chunk_progress = 0
                    await sess.commit()

                    chunked_data = []
                    for idx, col_info in enumerate(schema_info):
                        description = build_column_description(col_info)
                        chunked_data.append({
                            'index': idx,
                            'col_info': col_info,
                            'description': description
                        })
                        progress = int((idx + 1) / len(schema_info) * 100)
                        ds.chunk_progress = progress
                        await sess.commit()

                    ds.chunk_status = 'completed'
                    ds.chunk_progress = 100
                    await sess.commit()
                    logger.info(f"数据集 {dataset_id} 分片重试完成")

                    # 自动执行向量化
                    ds.vectorize_status = 'vectorizing'
                    ds.vectorize_progress = 0
                    await sess.commit()

                    await vectorize_columns(str(dataset_id), chunked_data)

                    ds.vectorize_status = 'completed'
                    ds.vectorize_progress = 100
                    await sess.commit()
                    logger.info(f"数据集 {dataset_id} 向量化完成")

                except Exception as e:
                    logger.error(f"重试失败: {e}")
                    if ds.chunk_status != 'completed':
                        ds.chunk_status = 'failed'
                        ds.chunk_error = str(e)
                    else:
                        ds.vectorize_status = 'failed'
                        ds.vectorize_error = str(e)
                    await sess.commit()

        background_tasks.add_task(retry_chunk_task)

        return {
            "success": True,
            "message": "已开始重新分片和向量化",
            "dataset_id": dataset_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新分片失败: {e}")
        raise HTTPException(status_code=500, detail=f"重试失败: {str(e)}")


@router.post("/dataset/{dataset_id}/retry_vectorize")
async def retry_vectorize(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    重新执行向量化步骤(仅在分片已完成时)

    Args:
        dataset_id: 数据集ID
        background_tasks: 后台任务
        session: 数据库会话

    Returns:
        重试结果
    """
    try:
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        if dataset.parse_status != 'parsed':
            raise HTTPException(
                status_code=400,
                detail=f"数据集解析状态为 {dataset.parse_status}，无法执行向量化"
            )

        if dataset.chunk_status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"分片状态为 {dataset.chunk_status}，必须先完成分片"
            )

        if dataset.vectorize_status == 'completed':
            raise HTTPException(
                status_code=400,
                detail="向量化已完成，无需重试"
            )

        # 重置向量化状态
        dataset.vectorize_status = 'pending'
        dataset.vectorize_progress = 0
        dataset.vectorize_error = None
        await session.commit()

        # 添加后台任务
        async def retry_vectorize_task():
            from db.session import async_session
            from models.sys_dataset import SysDatasetColumn
            from sqlalchemy import select as sql_select
            from services.embedding_service import build_column_description, vectorize_columns

            async with async_session() as sess:
                # 获取列信息
                col_result = await sess.execute(
                    sql_select(SysDatasetColumn)
                    .where(SysDatasetColumn.dataset_id == dataset_id)
                    .order_by(SysDatasetColumn.col_index)
                )
                columns = col_result.scalars().all()

                if not columns:
                    logger.error(f"数据集 {dataset_id} 没有列信息")
                    return

                # 重新构造chunked_data
                chunked_data = []
                for idx, col in enumerate(columns):
                    col_info = {
                        'name': col.col_name,
                        'type': col.col_type,
                        'stats': col.stats or {},
                        'samples': col.sample_values or []
                    }
                    description = build_column_description(col_info)
                    chunked_data.append({
                        'index': idx,
                        'col_info': col_info,
                        'description': description
                    })

                # 更新为vectorizing状态
                ds_result = await sess.execute(
                    sql_select(SysDataset).where(SysDataset.id == dataset_id)
                )
                ds = ds_result.scalar_one()

                try:
                    ds.vectorize_status = 'vectorizing'
                    ds.vectorize_progress = 0
                    await sess.commit()

                    await vectorize_columns(str(dataset_id), chunked_data)

                    ds.vectorize_status = 'completed'
                    ds.vectorize_progress = 100
                    await sess.commit()
                    logger.info(f"数据集 {dataset_id} 向量化重试成功")

                except Exception as e:
                    logger.error(f"向量化重试失败: {e}")
                    ds.vectorize_status = 'failed'
                    ds.vectorize_error = str(e)
                    await sess.commit()

        background_tasks.add_task(retry_vectorize_task)

        return {
            "success": True,
            "message": "已开始重新向量化",
            "dataset_id": dataset_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新向量化失败: {e}")
        raise HTTPException(status_code=500, detail=f"重试失败: {str(e)}")
