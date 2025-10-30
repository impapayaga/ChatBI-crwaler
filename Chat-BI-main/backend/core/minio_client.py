"""
MinIO对象存储客户端封装
用于文件上传、下载和管理
"""
from minio import Minio
from minio.error import S3Error
from core.config import settings
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO客户端封装类"""

    def __init__(self):
        """初始化MinIO客户端"""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self._ensure_bucket(settings.MINIO_BUCKET)
            logger.info(f"MinIO客户端初始化成功: {settings.MINIO_ENDPOINT}")
        except Exception as e:
            logger.error(f"MinIO客户端初始化失败: {e}")
            raise

    def _ensure_bucket(self, bucket_name: str):
        """确保bucket存在,不存在则创建"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"创建MinIO bucket: {bucket_name}")
            else:
                logger.debug(f"MinIO bucket已存在: {bucket_name}")
        except S3Error as e:
            logger.error(f"检查/创建bucket失败: {e}")
            raise

    def upload_file(self, file_data: bytes, object_name: str, content_type: str = "application/octet-stream") -> str:
        """
        上传文件到MinIO

        Args:
            file_data: 文件字节数据
            object_name: 对象名称(路径)
            content_type: 文件MIME类型

        Returns:
            文件的完整路径
        """
        try:
            self.client.put_object(
                settings.MINIO_BUCKET,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            file_path = f"{settings.MINIO_BUCKET}/{object_name}"
            logger.info(f"文件上传成功: {file_path}")
            return file_path
        except S3Error as e:
            logger.error(f"文件上传失败: {e}")
            raise

    def download_file(self, object_name: str) -> bytes:
        """
        从MinIO下载文件

        Args:
            object_name: 对象名称(路径)

        Returns:
            文件字节数据
        """
        try:
            response = self.client.get_object(settings.MINIO_BUCKET, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.debug(f"文件下载成功: {object_name}")
            return data
        except S3Error as e:
            logger.error(f"文件下载失败: {e}")
            raise

    def delete_file(self, object_name: str) -> bool:
        """
        删除MinIO中的文件

        Args:
            object_name: 对象名称(路径)

        Returns:
            是否删除成功
        """
        try:
            self.client.remove_object(settings.MINIO_BUCKET, object_name)
            logger.info(f"文件删除成功: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"文件删除失败: {e}")
            return False

    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在

        Args:
            object_name: 对象名称(路径)

        Returns:
            文件是否存在
        """
        try:
            self.client.stat_object(settings.MINIO_BUCKET, object_name)
            return True
        except S3Error:
            return False

    def get_file_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的预签名URL

        Args:
            object_name: 对象名称(路径)
            expires: 过期时间(秒)

        Returns:
            预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                settings.MINIO_BUCKET,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"生成预签名URL失败: {e}")
            return None

    def list_files(self, prefix: str = "", recursive: bool = True):
        """
        列出MinIO中的文件

        Args:
            prefix: 文件前缀(路径)
            recursive: 是否递归列出

        Returns:
            文件对象列表
        """
        try:
            objects = self.client.list_objects(
                settings.MINIO_BUCKET,
                prefix=prefix,
                recursive=recursive
            )

            files = []
            for obj in objects:
                files.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                    'etag': obj.etag,
                    'content_type': obj.content_type
                })

            logger.debug(f"列出文件成功: prefix={prefix}, count={len(files)}")
            return files
        except S3Error as e:
            logger.error(f"列出文件失败: {e}")
            raise

    def get_file_stats(self, object_name: str) -> Optional[dict]:
        """
        获取文件统计信息

        Args:
            object_name: 对象名称(路径)

        Returns:
            文件统计信息
        """
        try:
            stat = self.client.stat_object(settings.MINIO_BUCKET, object_name)
            return {
                'name': object_name,
                'size': stat.size,
                'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata
            }
        except S3Error as e:
            logger.error(f"获取文件统计信息失败: {e}")
            return None


# 全局单例
minio_client = MinIOClient()
