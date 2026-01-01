"""Cloud storage utilities for S3 and file management."""

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError


class S3Storage:
    """S3 storage client for uploading and downloading files."""

    def __init__(
        self,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str = "us-east-1",
    ):
        """
        Initialize S3 storage client.

        Args:
            aws_access_key_id: AWS access key (defaults to env var)
            aws_secret_access_key: AWS secret key (defaults to env var)
            region_name: AWS region
        """
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region_name,
        )

    def upload_bytes(
        self,
        data: bytes,
        bucket: str,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload bytes to S3.

        Args:
            data: Bytes to upload
            bucket: S3 bucket name
            key: S3 object key
            content_type: MIME type
            metadata: Optional metadata

        Returns:
            S3 URL of uploaded file
        """
        extra_args = {
            "ContentType": content_type,
        }
        if metadata:
            extra_args["Metadata"] = metadata

        self.s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            **extra_args,
        )

        return f"s3://{bucket}/{key}"

    def upload_file(
        self,
        filepath: str | Path,
        bucket: str,
        key: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """
        Upload a file to S3.

        Args:
            filepath: Path to file to upload
            bucket: S3 bucket name
            key: S3 object key (defaults to filename)
            content_type: MIME type (auto-detected if None)

        Returns:
            S3 URL of uploaded file
        """
        filepath = Path(filepath)
        if key is None:
            key = filepath.name

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.s3_client.upload_file(
            str(filepath),
            bucket,
            key,
            ExtraArgs=extra_args if extra_args else None,
        )

        return f"s3://{bucket}/{key}"

    def download_bytes(self, bucket: str, key: str) -> bytes:
        """
        Download file from S3 as bytes.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            File contents as bytes
        """
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def download_file(self, bucket: str, key: str, filepath: str | Path) -> Path:
        """
        Download file from S3 to local path.

        Args:
            bucket: S3 bucket name
            key: S3 object key
            filepath: Local path to save file

        Returns:
            Path to downloaded file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        self.s3_client.download_file(bucket, key, str(filepath))
        return filepath

    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        List objects in S3 bucket.

        Args:
            bucket: S3 bucket name
            prefix: Prefix to filter objects
            max_keys: Maximum number of keys to return

        Returns:
            List of object metadata dictionaries
        """
        response = self.s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )

        return response.get("Contents", [])

    def delete_object(self, bucket: str, key: str) -> None:
        """
        Delete an object from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key
        """
        self.s3_client.delete_object(Bucket=bucket, Key=key)

    def object_exists(self, bucket: str, key: str) -> bool:
        """
        Check if an object exists in S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def get_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for temporary access.

        Args:
            bucket: S3 bucket name
            key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration,
        )


def parse_s3_url(s3_url: str) -> tuple[str, str]:
    """
    Parse S3 URL into bucket and key.

    Args:
        s3_url: S3 URL (s3://bucket/key)

    Returns:
        Tuple of (bucket, key)
    """
    parsed = urlparse(s3_url)
    if parsed.scheme != "s3":
        raise ValueError(f"Invalid S3 URL: {s3_url}")

    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    return bucket, key


def upload_vdp_output(
    pdf_bytes: bytes,
    job_id: str,
    bucket: str,
    prefix: str = "vdp-output",
) -> str:
    """
    Upload VDP output PDF to S3 with standardized naming.

    Args:
        pdf_bytes: PDF data as bytes
        job_id: Unique job identifier
        bucket: S3 bucket name
        prefix: S3 key prefix

    Returns:
        S3 URL of uploaded file
    """
    storage = S3Storage()
    key = f"{prefix}/{job_id}/output.pdf"

    return storage.upload_bytes(
        pdf_bytes,
        bucket,
        key,
        content_type="application/pdf",
        metadata={"job_id": job_id},
    )


def upload_barcode_batch(
    barcode_list: list[bytes],
    job_id: str,
    bucket: str,
    prefix: str = "barcodes",
) -> list[str]:
    """
    Upload a batch of barcodes to S3.

    Args:
        barcode_list: List of barcode image bytes
        job_id: Unique job identifier
        bucket: S3 bucket name
        prefix: S3 key prefix

    Returns:
        List of S3 URLs
    """
    storage = S3Storage()
    urls = []

    for i, barcode_bytes in enumerate(barcode_list):
        key = f"{prefix}/{job_id}/barcode_{i:06d}.png"
        url = storage.upload_bytes(
            barcode_bytes,
            bucket,
            key,
            content_type="image/png",
            metadata={"job_id": job_id, "index": str(i)},
        )
        urls.append(url)

    return urls
