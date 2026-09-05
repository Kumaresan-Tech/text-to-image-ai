import os
import uuid
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class StorageService:
    """Handles file storage — local disk or S3/R2."""

    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        if self.backend == "s3":
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )

    async def upload(self, data: bytes, key: str, content_type: str = "image/png") -> str:
        if self.backend == "s3":
            return self._upload_s3(data, key, content_type)
        return self._upload_local(data, key)

    async def delete(self, key: str) -> None:
        if self.backend == "s3":
            self._delete_s3(key)
        else:
            self._delete_local(key)

    def get_url(self, key: str) -> str:
        if self.backend == "s3":
            return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        backend_url = settings.BACKEND_URL.rstrip("/")
        return f"{backend_url}/storage/{key}"

    def _upload_s3(self, data: bytes, key: str, content_type: str) -> str:
        self.s3.put_object(Bucket=settings.AWS_S3_BUCKET, Key=key, Body=data, ContentType=content_type)
        return self.get_url(key)

    def _upload_local(self, data: bytes, key: str) -> str:
        path = Path(settings.LOCAL_STORAGE_PATH) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self.get_url(key)

    def _delete_s3(self, key: str) -> None:
        try:
            self.s3.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
        except ClientError:
            pass

    def _delete_local(self, key: str) -> None:
        path = Path(settings.LOCAL_STORAGE_PATH) / key
        path.unlink(missing_ok=True)

    def generate_key(self, user_id: str, ext: str = "png") -> str:
        return f"images/{user_id}/{uuid.uuid4().hex}.{ext}"


storage_service = StorageService()
