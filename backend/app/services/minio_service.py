import logging
from io import BytesIO
from typing import Optional

from minio import Minio
from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[Minio] = None


def get_minio() -> Minio:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _client


def ensure_bucket(bucket_name: str = "artifacts"):
    client = get_minio()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info(f"Created bucket: {bucket_name}")


def upload_object(bucket: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = get_minio()
    client.put_object(bucket, object_name, BytesIO(data), len(data), content_type=content_type)
    return f"{bucket}/{object_name}"


def get_presigned_url(bucket: str, object_name: str, expires_seconds: int = 3600) -> str:
    client = get_minio()
    return client.presigned_get_object(bucket, object_name, expires=expires_seconds)


def download_object(bucket: str, object_name: str) -> bytes:
    client = get_minio()
    response = client.get_object(bucket, object_name)
    return response.read()
