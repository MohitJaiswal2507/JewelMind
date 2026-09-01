"""
Supabase Storage Service & Jewellery Sketch Asset Management
"""

import os
import uuid
from typing import Optional, Set, Tuple, Union
import httpx

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger

# Supported MIME types and extensions
ALLOWED_MIME_TYPES: Set[str] = {
    "image/png",
    "image/jpeg",
    "image/webp",
}

ALLOWED_EXTENSIONS: Set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

# Mapping extensions to normalized content types
EXTENSION_MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class StorageService:
    def __init__(self):
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_BYTES
        self.supabase_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""
        self.api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY

    def validate_file(
        self,
        file_bytes: bytes,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Validates file size and MIME type.
        Raises 413 on oversized files, 400 on unsupported formats.
        Returns the normalized content type string.
        """
        # 1. Size Validation
        if len(file_bytes) == 0:
            raise AppException(
                message="Uploaded file is empty.",
                code="EMPTY_FILE",
                status_code=400,
            )

        if len(file_bytes) > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            actual_mb = round(len(file_bytes) / (1024 * 1024), 2)
            raise AppException(
                message=f"File size ({actual_mb} MB) exceeds maximum allowed limit of {max_mb:.0f} MB.",
                code="FILE_TOO_LARGE",
                status_code=413,
                details={"max_size_bytes": self.max_size_bytes, "actual_size_bytes": len(file_bytes)},
            )

        # 2. Extension & MIME Validation
        ext = os.path.splitext(filename or "")[1].lower()
        
        # Check by content_type header or file extension
        detected_mime = content_type
        if not detected_mime or detected_mime == "application/octet-stream":
            detected_mime = EXTENSION_MIME_MAP.get(ext)

        if not detected_mime or detected_mime.lower() not in ALLOWED_MIME_TYPES:
            raise AppException(
                message="Unsupported file type. Only PNG, JPEG, and WEBP formats are supported.",
                code="INVALID_FILE_TYPE",
                status_code=400,
                details={
                    "allowed_types": list(ALLOWED_MIME_TYPES),
                    "received_type": content_type,
                    "received_extension": ext,
                },
            )

        # Basic magic bytes sanity check
        if detected_mime == "image/png" and not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            # Check if extension mismatch
            if ext not in [".png"]:
                raise AppException(
                    message="File content does not match PNG signature.",
                    code="CORRUPT_FILE_CONTENT",
                    status_code=400,
                )
        elif detected_mime == "image/jpeg" and not file_bytes.startswith(b"\xff\xd8\xff"):
            if ext not in [".jpg", ".jpeg"]:
                raise AppException(
                    message="File content does not match JPEG signature.",
                    code="CORRUPT_FILE_CONTENT",
                    status_code=400,
                )

        return detected_mime.lower()

    def generate_storage_path(
        self,
        user_id: Union[str, uuid.UUID],
        design_id: Union[str, uuid.UUID],
        original_filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Constructs safe storage path: {user_id}/{design_id}/{unique_filename}.
        Returns (relative_path_in_bucket, unique_filename).
        """
        ext = os.path.splitext(original_filename or "")[1].lower()
        if not ext and content_type:
            if content_type == "image/png":
                ext = ".png"
            elif content_type in ["image/jpeg", "image/jpg"]:
                ext = ".jpg"
            elif content_type == "image/webp":
                ext = ".webp"

        if ext not in ALLOWED_EXTENSIONS:
            ext = ".png"

        unique_filename = f"sketch_{uuid.uuid4().hex[:12]}{ext}"
        storage_path = f"{str(user_id)}/{str(design_id)}/{unique_filename}"
        return storage_path, unique_filename

    def get_public_url(self, storage_path: str) -> str:
        """
        Constructs public URL for a stored object in Supabase Storage.
        """
        if self.supabase_url:
            return f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{storage_path}"
        return f"/storage/{self.bucket}/{storage_path}"

    def _is_mock_or_test_mode(self) -> bool:
        """
        Returns True if running in testing environment or if Supabase URL is unconfigured/placeholder.
        """
        if settings.APP_ENV == "testing":
            return True
        if not self.supabase_url or not self.api_key:
            return True
        if "your-project" in self.supabase_url or "example.com" in self.supabase_url:
            return True
        return False

    async def upload_sketch(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        user_id: Union[str, uuid.UUID],
        design_id: Union[str, uuid.UUID],
    ) -> Tuple[str, str]:
        """
        Uploads jewellery sketch file to Supabase Storage.
        Returns (public_url, storage_path).
        """
        # Validate file
        validated_mime = self.validate_file(file_bytes, filename, content_type)
        
        # Build safe storage path
        storage_path, _ = self.generate_storage_path(
            user_id=user_id,
            design_id=design_id,
            original_filename=filename,
            content_type=validated_mime,
        )

        # Upload to Supabase Storage via REST API if in live mode
        if not self._is_mock_or_test_mode():
            url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "apikey": self.api_key,
                "Content-Type": validated_mime,
                "x-upsert": "true",
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, content=file_bytes, headers=headers)
                    if response.status_code not in (200, 201):
                        logger.error(
                            f"Supabase storage upload failed [{response.status_code}]: {response.text}"
                        )
                        raise AppException(
                            message="Failed to upload sketch to cloud storage.",
                            code="STORAGE_UPLOAD_FAILED",
                            status_code=502,
                            details={"supabase_status": response.status_code},
                        )
            except httpx.RequestError as exc:
                logger.error(f"Network error during Supabase upload: {exc}")
                raise AppException(
                    message="Network error connecting to storage provider.",
                    code="STORAGE_NETWORK_ERROR",
                    status_code=502,
                )

        public_url = self.get_public_url(storage_path)
        return public_url, storage_path

    async def delete_sketch(self, storage_path_or_url: Optional[str]) -> bool:
        """
        Deletes a sketch file from Supabase Storage.
        Safe operation: does not raise errors if object does not exist or URL is null.
        """
        if not storage_path_or_url:
            return True

        # Extract relative path from URL if needed
        storage_path = storage_path_or_url
        marker = f"/{self.bucket}/"
        if marker in storage_path:
            storage_path = storage_path.split(marker, 1)[1]

        if not self._is_mock_or_test_mode():
            url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "apikey": self.api_key,
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.delete(url, headers=headers)
                    if response.status_code not in (200, 204, 404):
                        logger.warning(
                            f"Failed to delete sketch from storage [{response.status_code}]: {response.text}"
                        )
            except Exception as exc:
                logger.warning(f"Error during storage delete for {storage_path}: {exc}")

        return True


storage_service = StorageService()
