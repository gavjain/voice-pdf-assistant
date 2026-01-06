"""
Cloudflare R2 storage integration (optional).
Falls back to local storage if not configured.
"""

import os
import logging
from pathlib import Path
from typing import Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class R2Storage:
    """Cloudflare R2 storage client (S3-compatible)."""
    
    def __init__(self):
        """Initialize R2 client if credentials are available."""
        self.enabled = False
        self.client = None
        self.bucket_name = os.getenv("R2_BUCKET_NAME")
        
        # Check if R2 is configured
        account_id = os.getenv("R2_ACCOUNT_ID")
        access_key = os.getenv("R2_ACCESS_KEY_ID")
        secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        
        if all([account_id, access_key, secret_key, self.bucket_name]):
            try:
                self.client = boto3.client(
                    "s3",
                    endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name="auto"
                )
                self.enabled = True
                logger.info(f"R2 storage enabled for bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"R2 initialization failed: {e}. Using local storage.")
        else:
            logger.info("R2 not configured. Using local storage.")
    
    def upload_file(self, file_path: Path, key: str) -> Optional[str]:
        """
        Upload file to R2.
        
        Args:
            file_path: Local file path
            key: R2 object key
            
        Returns:
            Public URL if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            self.client.upload_file(
                str(file_path),
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": self._get_content_type(file_path)}
            )
            logger.info(f"Uploaded {key} to R2")
            return f"https://{self.bucket_name}.r2.dev/{key}"
        except Exception as e:
            logger.error(f"R2 upload failed for {key}: {e}")
            return None
    
    def download_file(self, key: str, local_path: Path) -> bool:
        """
        Download file from R2.
        
        Args:
            key: R2 object key
            local_path: Local destination path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.client.download_file(
                self.bucket_name,
                key,
                str(local_path)
            )
            logger.info(f"Downloaded {key} from R2")
            return True
        except Exception as e:
            logger.error(f"R2 download failed for {key}: {e}")
            return False
    
    def delete_file(self, key: str) -> bool:
        """
        Delete file from R2.
        
        Args:
            key: R2 object key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"Deleted {key} from R2")
            return True
        except Exception as e:
            logger.error(f"R2 delete failed for {key}: {e}")
            return False
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type based on file extension."""
        suffix = file_path.suffix.lower()
        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword"
        }
        return content_types.get(suffix, "application/octet-stream")
