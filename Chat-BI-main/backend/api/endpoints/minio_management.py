"""
MinIO文件管理API端点
提供文件列表、下载、删除等管理功能
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import io

from core.minio_client import minio_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/minio/files")
async def list_minio_files(prefix: str = "", recursive: bool = True):
    """
    列出MinIO中的所有文件

    Args:
        prefix: 文件路径前缀，用于过滤文件
        recursive: 是否递归列出子目录中的文件

    Returns:
        文件列表，包含文件名、大小、修改时间等信息
    """
    try:
        files = minio_client.list_files(prefix=prefix, recursive=recursive)

        # 计算总大小
        total_size = sum(f['size'] for f in files)

        return {
            "success": True,
            "total": len(files),
            "total_size": total_size,
            "files": files
        }
    except Exception as e:
        logger.error(f"列出MinIO文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.get("/minio/file/{file_path:path}")
async def get_file_info(file_path: str):
    """
    获取文件详细信息

    Args:
        file_path: 文件路径

    Returns:
        文件详细信息
    """
    try:
        stats = minio_client.get_file_stats(file_path)

        if not stats:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 生成临时下载链接
        download_url = minio_client.get_file_url(file_path, expires=3600)
        stats['download_url'] = download_url

        return {
            "success": True,
            "file": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.get("/minio/download/{file_path:path}")
async def download_file(file_path: str):
    """
    下载MinIO中的文件

    Args:
        file_path: 文件路径

    Returns:
        文件流
    """
    try:
        if not minio_client.file_exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        file_data = minio_client.download_file(file_path)

        # 从路径中提取文件名
        filename = file_path.split('/')[-1]

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.delete("/minio/file/{file_path:path}")
async def delete_minio_file(file_path: str):
    """
    删除MinIO中的文件

    Args:
        file_path: 文件路径

    Returns:
        删除结果
    """
    try:
        if not minio_client.file_exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        success = minio_client.delete_file(file_path)

        if not success:
            raise HTTPException(status_code=500, detail="文件删除失败")

        return {
            "success": True,
            "message": f"文件 {file_path} 已成功删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/minio/stats")
async def get_minio_stats():
    """
    获取MinIO存储统计信息

    Returns:
        存储统计信息
    """
    try:
        all_files = minio_client.list_files(prefix="", recursive=True)

        # 按目录分组统计
        stats_by_dir = {}
        for file in all_files:
            # 提取目录名
            parts = file['name'].split('/')
            dir_name = parts[0] if len(parts) > 1 else 'root'

            if dir_name not in stats_by_dir:
                stats_by_dir[dir_name] = {
                    'count': 0,
                    'total_size': 0
                }

            stats_by_dir[dir_name]['count'] += 1
            stats_by_dir[dir_name]['total_size'] += file['size']

        total_size = sum(f['size'] for f in all_files)

        return {
            "success": True,
            "total_files": len(all_files),
            "total_size": total_size,
            "stats_by_directory": stats_by_dir
        }
    except Exception as e:
        logger.error(f"获取MinIO统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
