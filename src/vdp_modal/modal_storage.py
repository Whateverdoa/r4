"""Modal native storage utilities using Volumes and Dictionaries."""

import modal
from pathlib import Path
from typing import Any, Literal
import json
from datetime import datetime


# Define persistent Modal storage resources
# These are created once and reused across all function calls
vdp_volume = modal.Volume.from_name("vdp-storage", create_if_missing=True)
vdp_dict = modal.Dict.from_name("vdp-metadata", create_if_missing=True)


class ModalVolumeStorage:
    """Storage using Modal Volumes for large files (PDFs, images)."""

    def __init__(self, volume: modal.Volume | None = None):
        """
        Initialize Modal Volume storage.

        Args:
            volume: Modal Volume instance (defaults to shared vdp_volume)
        """
        self.volume = volume or vdp_volume

    def save_pdf(
        self,
        pdf_bytes: bytes,
        job_id: str,
        filename: str = "output.pdf",
        prefix: str = "jobs",
    ) -> str:
        """
        Save PDF to Modal Volume.

        Args:
            pdf_bytes: PDF data as bytes
            job_id: Job identifier
            filename: Output filename
            prefix: Directory prefix in volume

        Returns:
            Path in volume
        """
        # Path in volume: /jobs/job-001/output.pdf
        volume_path = f"/{prefix}/{job_id}/{filename}"

        # Write to volume
        # Note: In Modal functions, you write to the mount point
        # For standalone usage, we'll use a temp directory approach
        local_path = f"/tmp/modal_volume{volume_path}"
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, "wb") as f:
            f.write(pdf_bytes)

        return volume_path

    def save_barcode(
        self,
        barcode_bytes: bytes,
        job_id: str,
        index: int,
        prefix: str = "barcodes",
    ) -> str:
        """
        Save barcode image to Modal Volume.

        Args:
            barcode_bytes: Image data as bytes
            job_id: Job identifier
            index: Barcode index
            prefix: Directory prefix

        Returns:
            Path in volume
        """
        volume_path = f"/{prefix}/{job_id}/barcode_{index:08d}.png"

        local_path = f"/tmp/modal_volume{volume_path}"
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, "wb") as f:
            f.write(barcode_bytes)

        return volume_path

    def save_batch(
        self,
        files: list[tuple[bytes, str]],
        job_id: str,
        prefix: str = "batch",
    ) -> list[str]:
        """
        Save multiple files to Modal Volume.

        Args:
            files: List of (file_bytes, filename) tuples
            job_id: Job identifier
            prefix: Directory prefix

        Returns:
            List of paths in volume
        """
        paths = []

        for file_bytes, filename in files:
            volume_path = f"/{prefix}/{job_id}/{filename}"
            local_path = f"/tmp/modal_volume{volume_path}"
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, "wb") as f:
                f.write(file_bytes)

            paths.append(volume_path)

        return paths

    def read_file(self, volume_path: str) -> bytes:
        """
        Read file from Modal Volume.

        Args:
            volume_path: Path in volume

        Returns:
            File contents as bytes
        """
        local_path = f"/tmp/modal_volume{volume_path}"

        with open(local_path, "rb") as f:
            return f.read()

    def list_files(self, job_id: str, prefix: str = "jobs") -> list[str]:
        """
        List files for a job.

        Args:
            job_id: Job identifier
            prefix: Directory prefix

        Returns:
            List of file paths
        """
        directory = f"/tmp/modal_volume/{prefix}/{job_id}"

        if not Path(directory).exists():
            return []

        files = []
        for path in Path(directory).rglob("*"):
            if path.is_file():
                # Convert back to volume path
                relative = path.relative_to(f"/tmp/modal_volume")
                files.append(f"/{relative}")

        return files

    def delete_job(self, job_id: str, prefix: str = "jobs") -> None:
        """
        Delete all files for a job.

        Args:
            job_id: Job identifier
            prefix: Directory prefix
        """
        import shutil

        directory = f"/tmp/modal_volume/{prefix}/{job_id}"

        if Path(directory).exists():
            shutil.rmtree(directory)


class ModalDictStorage:
    """Storage using Modal Dict for metadata and job results."""

    def __init__(self, dict_obj: modal.Dict | None = None):
        """
        Initialize Modal Dict storage.

        Args:
            dict_obj: Modal Dict instance (defaults to shared vdp_dict)
        """
        self.dict = dict_obj or vdp_dict

    def save_job_metadata(
        self,
        job_id: str,
        metadata: dict[str, Any],
    ) -> None:
        """
        Save job metadata.

        Args:
            job_id: Job identifier
            metadata: Metadata dictionary
        """
        key = f"job:{job_id}:metadata"

        # Add timestamp
        metadata["updated_at"] = datetime.utcnow().isoformat()

        self.dict[key] = metadata

    def get_job_metadata(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job metadata.

        Args:
            job_id: Job identifier

        Returns:
            Metadata dictionary or None
        """
        key = f"job:{job_id}:metadata"
        return self.dict.get(key)

    def save_job_result(
        self,
        job_id: str,
        result: dict[str, Any],
    ) -> None:
        """
        Save job result.

        Args:
            job_id: Job identifier
            result: Result dictionary
        """
        key = f"job:{job_id}:result"

        # Add timestamp
        result["completed_at"] = datetime.utcnow().isoformat()

        self.dict[key] = result

    def get_job_result(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job result.

        Args:
            job_id: Job identifier

        Returns:
            Result dictionary or None
        """
        key = f"job:{job_id}:result"
        return self.dict.get(key)

    def save_job_status(
        self,
        job_id: str,
        status: str,
        progress: int | None = None,
        message: str | None = None,
    ) -> None:
        """
        Save job status.

        Args:
            job_id: Job identifier
            status: Status string (pending, processing, completed, failed)
            progress: Progress percentage (0-100)
            message: Status message
        """
        key = f"job:{job_id}:status"

        status_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if progress is not None:
            status_data["progress"] = progress

        if message:
            status_data["message"] = message

        self.dict[key] = status_data

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Status dictionary or None
        """
        key = f"job:{job_id}:status"
        return self.dict.get(key)

    def list_jobs(self, prefix: str = "job:") -> list[str]:
        """
        List all job IDs.

        Args:
            prefix: Key prefix to filter

        Returns:
            List of job IDs
        """
        # Extract job IDs from keys
        job_ids = set()

        for key in self.dict.keys():
            if key.startswith(prefix) and ":metadata" in key:
                # Extract job_id from "job:job_id:metadata"
                parts = key.split(":")
                if len(parts) >= 2:
                    job_ids.add(parts[1])

        return sorted(list(job_ids))

    def delete_job(self, job_id: str) -> None:
        """
        Delete all data for a job.

        Args:
            job_id: Job identifier
        """
        keys_to_delete = [
            f"job:{job_id}:metadata",
            f"job:{job_id}:result",
            f"job:{job_id}:status",
        ]

        for key in keys_to_delete:
            if key in self.dict:
                del self.dict[key]


StorageBackend = Literal["modal", "s3", "local"]


class UnifiedStorage:
    """Unified storage interface supporting Modal, S3, and local storage."""

    def __init__(
        self,
        backend: StorageBackend = "modal",
        s3_bucket: str | None = None,
    ):
        """
        Initialize unified storage.

        Args:
            backend: Storage backend to use
            s3_bucket: S3 bucket (required if backend="s3")
        """
        self.backend = backend

        if backend == "modal":
            self.volume_storage = ModalVolumeStorage()
            self.dict_storage = ModalDictStorage()
        elif backend == "s3":
            if not s3_bucket:
                raise ValueError("s3_bucket required for S3 backend")
            from .storage import S3Storage

            self.s3_storage = S3Storage()
            self.s3_bucket = s3_bucket
        elif backend == "local":
            self.local_base_path = Path("/tmp/vdp-output")
            self.local_base_path.mkdir(parents=True, exist_ok=True)

    def save_pdf(
        self,
        pdf_bytes: bytes,
        job_id: str,
        filename: str = "output.pdf",
    ) -> str:
        """
        Save PDF using configured backend.

        Args:
            pdf_bytes: PDF data
            job_id: Job identifier
            filename: Output filename

        Returns:
            Storage URL or path
        """
        if self.backend == "modal":
            path = self.volume_storage.save_pdf(pdf_bytes, job_id, filename)
            return f"modal://{path}"

        elif self.backend == "s3":
            key = f"vdp-output/{job_id}/{filename}"
            url = self.s3_storage.upload_bytes(
                pdf_bytes,
                self.s3_bucket,
                key,
                content_type="application/pdf",
            )
            return url

        elif self.backend == "local":
            output_dir = self.local_base_path / job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename

            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

            return str(output_path)

    def save_metadata(self, job_id: str, metadata: dict[str, Any]) -> None:
        """
        Save job metadata.

        Args:
            job_id: Job identifier
            metadata: Metadata dictionary
        """
        if self.backend == "modal":
            self.dict_storage.save_job_metadata(job_id, metadata)

        elif self.backend == "s3":
            key = f"vdp-metadata/{job_id}/metadata.json"
            metadata_bytes = json.dumps(metadata).encode()
            self.s3_storage.upload_bytes(
                metadata_bytes,
                self.s3_bucket,
                key,
                content_type="application/json",
            )

        elif self.backend == "local":
            metadata_dir = self.local_base_path / job_id
            metadata_dir.mkdir(parents=True, exist_ok=True)
            metadata_path = metadata_dir / "metadata.json"

            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

    def get_metadata(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job metadata.

        Args:
            job_id: Job identifier

        Returns:
            Metadata dictionary or None
        """
        if self.backend == "modal":
            return self.dict_storage.get_job_metadata(job_id)

        elif self.backend == "s3":
            key = f"vdp-metadata/{job_id}/metadata.json"
            try:
                metadata_bytes = self.s3_storage.download_bytes(self.s3_bucket, key)
                return json.loads(metadata_bytes)
            except Exception:
                return None

        elif self.backend == "local":
            metadata_path = self.local_base_path / job_id / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    return json.load(f)
            return None
