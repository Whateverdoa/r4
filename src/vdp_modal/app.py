"""Main Modal application for VDP processing."""

import modal
from typing import Any, Literal

# Define Modal app
app = modal.App("vdp-production")

# Define container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "python-barcode>=0.15.0",
        "qrcode[pil]>=7.4.0",
        "PyMuPDF>=1.24.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "boto3>=1.34.0",
        "pydantic>=2.0.0",
    )
)

# Create persistent Modal storage resources
vdp_volume = modal.Volume.from_name("vdp-storage", create_if_missing=True)
vdp_dict = modal.Dict.from_name("vdp-metadata", create_if_missing=True)

# Legacy volume for backwards compatibility
volume = vdp_volume

# Storage backend type
StorageBackend = Literal["modal", "s3", "local"]


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=300,
)
def generate_single_barcode(
    data: str,
    barcode_type: str = "code128",
    dpi: int = 300,
) -> bytes:
    """
    Generate a single barcode.

    This function runs in parallel on Modal.

    Args:
        data: Data to encode
        barcode_type: Type of barcode
        dpi: Resolution

    Returns:
        Barcode image as bytes
    """
    from .barcode import generate_barcode

    return generate_barcode(data, barcode_type, dpi)


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=300,
)
def generate_single_label(
    label_data: dict[str, Any],
    serial_number: str,
    barcode_type: str = "code128",
) -> bytes:
    """
    Generate a single label with barcode.

    This function runs in parallel on Modal.

    Args:
        label_data: Label content and layout
        serial_number: Serial number for barcode
        barcode_type: Type of barcode

    Returns:
        PDF label as bytes
    """
    from .barcode import generate_barcode
    from .pdf_processing import create_label_pdf

    # Generate barcode
    barcode_bytes = generate_barcode(serial_number, barcode_type)

    # Create label PDF
    pdf_bytes = create_label_pdf(barcode_bytes, label_data)

    return pdf_bytes


@app.function(
    image=image,
    cpu=4,
    memory=4096,
    timeout=600,
)
def process_vdp_chunk(
    chunk_data: list[dict[str, Any]],
    template: dict[str, Any],
    chunk_id: int,
) -> bytes:
    """
    Process a chunk of VDP data in parallel.

    This is the core worker function that processes a subset of the total job.

    Args:
        chunk_data: List of records to process
        template: Label template configuration
        chunk_id: Unique chunk identifier

    Returns:
        Merged PDF of all labels in this chunk
    """
    from .barcode import generate_barcode
    from .pdf_processing import create_label_pdf, merge_pdfs

    print(f"Processing chunk {chunk_id} with {len(chunk_data)} records")

    pdf_pages = []

    for i, record in enumerate(chunk_data):
        # Generate barcode
        serial = record.get("serial", f"SERIAL-{chunk_id}-{i}")
        barcode_bytes = generate_barcode(
            serial,
            barcode_type=template.get("barcode_type", "code128"),
        )

        # Create label
        label_data = {
            "title": template.get("title", "Label"),
            "fields": [
                {"label": key, "value": value}
                for key, value in record.items()
            ],
        }

        pdf_bytes = create_label_pdf(barcode_bytes, label_data)
        pdf_pages.append(pdf_bytes)

    # Merge all pages in this chunk
    merged_pdf = merge_pdfs(pdf_pages)

    print(f"Chunk {chunk_id} complete: generated {len(pdf_pages)} labels")

    return merged_pdf


@app.function(
    image=image,
    cpu=4,
    memory=8192,
    timeout=1200,
)
def assemble_vdp_job(
    chunk_pdfs: list[bytes],
    job_id: str,
) -> bytes:
    """
    Assemble all chunks into final VDP output.

    Args:
        chunk_pdfs: List of PDF chunks
        job_id: Job identifier

    Returns:
        Final assembled PDF
    """
    from .pdf_processing import merge_pdfs, optimize_pdf

    print(f"Assembling {len(chunk_pdfs)} chunks for job {job_id}")

    # Merge all chunks
    final_pdf = merge_pdfs(chunk_pdfs)

    # Optimize the final PDF
    optimized_pdf = optimize_pdf(final_pdf, compression=True)

    print(f"Job {job_id} complete: {len(optimized_pdf)} bytes")

    return optimized_pdf


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=300,
)
def upload_to_s3(
    pdf_bytes: bytes,
    job_id: str,
    bucket: str,
    prefix: str = "vdp-output",
) -> str:
    """
    Upload final PDF to S3.

    Args:
        pdf_bytes: PDF data
        job_id: Job identifier
        bucket: S3 bucket
        prefix: Key prefix

    Returns:
        S3 URL
    """
    from .storage import upload_vdp_output

    print(f"Uploading job {job_id} to s3://{bucket}/{prefix}")

    s3_url = upload_vdp_output(pdf_bytes, job_id, bucket, prefix)

    print(f"Upload complete: {s3_url}")

    return s3_url


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=300,
    volumes={"/data": vdp_volume},
)
def save_to_modal_volume(
    pdf_bytes: bytes,
    job_id: str,
    filename: str = "output.pdf",
    prefix: str = "jobs",
) -> str:
    """
    Save PDF to Modal Volume.

    Args:
        pdf_bytes: PDF data
        job_id: Job identifier
        filename: Output filename
        prefix: Directory prefix in volume

    Returns:
        Volume path (modal://...)
    """
    from pathlib import Path

    # Volume is mounted at /data
    volume_path = f"/data/{prefix}/{job_id}/{filename}"
    Path(volume_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"Saving job {job_id} to Modal Volume: {volume_path}")

    with open(volume_path, "wb") as f:
        f.write(pdf_bytes)

    # Commit changes to volume
    vdp_volume.commit()

    print(f"Save complete: modal://{prefix}/{job_id}/{filename}")

    return f"modal://{prefix}/{job_id}/{filename}"


@app.function(
    image=image,
    cpu=1,
    memory=512,
    timeout=60,
)
def save_job_metadata(
    job_id: str,
    metadata: dict[str, Any],
) -> None:
    """
    Save job metadata to Modal Dict.

    Args:
        job_id: Job identifier
        metadata: Metadata dictionary
    """
    from datetime import datetime

    key = f"job:{job_id}:metadata"

    metadata["updated_at"] = datetime.utcnow().isoformat()

    vdp_dict[key] = metadata

    print(f"Saved metadata for job {job_id}")


@app.function(
    image=image,
    cpu=1,
    memory=512,
    timeout=60,
)
def save_job_result(
    job_id: str,
    result: dict[str, Any],
) -> None:
    """
    Save job result to Modal Dict.

    Args:
        job_id: Job identifier
        result: Result dictionary
    """
    from datetime import datetime

    key = f"job:{job_id}:result"

    result["completed_at"] = datetime.utcnow().isoformat()

    vdp_dict[key] = result

    print(f"Saved result for job {job_id}")


@app.function(
    image=image,
    cpu=1,
    memory=512,
    timeout=60,
)
def get_job_metadata(job_id: str) -> dict[str, Any] | None:
    """
    Get job metadata from Modal Dict.

    Args:
        job_id: Job identifier

    Returns:
        Metadata dictionary or None
    """
    key = f"job:{job_id}:metadata"
    return vdp_dict.get(key)


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=1800,
)
def run_vdp_pipeline(
    records: list[dict[str, Any]],
    template: dict[str, Any],
    job_id: str,
    chunk_size: int = 100,
    storage_backend: StorageBackend = "modal",
    s3_bucket: str | None = None,
    s3_prefix: str = "vdp-output",
    save_metadata: bool = True,
) -> dict[str, Any]:
    """
    Run the complete VDP pipeline with configurable storage.

    This orchestrates the entire workflow:
    1. Split data into chunks
    2. Process chunks in parallel (Modal .map())
    3. Assemble final PDF
    4. Save to storage (Modal Volume, S3, or return bytes)
    5. Save metadata to Modal Dict (optional)

    Args:
        records: List of data records
        template: Label template
        job_id: Unique job identifier
        chunk_size: Records per chunk
        storage_backend: Storage backend ("modal", "s3", or "local")
        s3_bucket: S3 bucket (required if storage_backend="s3")
        s3_prefix: S3 key prefix
        save_metadata: Save job metadata to Modal Dict

    Returns:
        Job result with PDF bytes and metadata
    """
    print(f"Starting VDP job {job_id} with {len(records)} records")
    print(f"Storage backend: {storage_backend}")

    # Split into chunks
    chunks = [
        records[i : i + chunk_size]
        for i in range(0, len(records), chunk_size)
    ]

    print(f"Split into {len(chunks)} chunks of ~{chunk_size} records each")

    # Process all chunks in parallel using Modal's .map()
    chunk_pdfs = list(
        process_vdp_chunk.map(
            [
                (chunk, template, i)
                for i, chunk in enumerate(chunks)
            ]
        )
    )

    print(f"All {len(chunk_pdfs)} chunks processed")

    # Assemble final PDF
    final_pdf = assemble_vdp_job.remote(chunk_pdfs, job_id)

    result = {
        "job_id": job_id,
        "total_records": len(records),
        "total_chunks": len(chunks),
        "pdf_size": len(final_pdf),
        "pdf_bytes": final_pdf,
        "storage_backend": storage_backend,
    }

    # Save to storage based on backend
    if storage_backend == "modal":
        storage_url = save_to_modal_volume.remote(
            final_pdf,
            job_id,
            filename="output.pdf",
            prefix="jobs",
        )
        result["storage_url"] = storage_url

    elif storage_backend == "s3":
        if not s3_bucket:
            raise ValueError("s3_bucket required when storage_backend='s3'")
        s3_url = upload_to_s3.remote(final_pdf, job_id, s3_bucket, s3_prefix)
        result["storage_url"] = s3_url

    elif storage_backend == "local":
        # Just return the bytes, user will save locally
        result["storage_url"] = f"local://{job_id}.pdf"

    # Save metadata to Modal Dict
    if save_metadata:
        metadata = {
            "job_id": job_id,
            "total_records": len(records),
            "total_chunks": len(chunks),
            "pdf_size": len(final_pdf),
            "storage_backend": storage_backend,
            "template": template,
        }
        save_job_metadata.remote(job_id, metadata)

        # Save result
        save_job_result.remote(job_id, result)

    print(f"Job {job_id} complete!")

    return result


@app.function(
    image=image,
    cpu=1,
    memory=1024,
    timeout=300,
)
def batch_generate_barcodes(
    serial_numbers: list[str],
    barcode_type: str = "code128",
    dpi: int = 300,
) -> list[bytes]:
    """
    Generate barcodes in parallel using Modal's .map().

    Args:
        serial_numbers: List of serial numbers
        barcode_type: Barcode type
        dpi: Resolution

    Returns:
        List of barcode images as bytes
    """
    print(f"Generating {len(serial_numbers)} barcodes in parallel")

    barcodes = list(
        generate_single_barcode.map(
            [(sn, barcode_type, dpi) for sn in serial_numbers]
        )
    )

    print(f"Generated {len(barcodes)} barcodes")

    return barcodes


# CLI for local testing
@app.local_entrypoint()
def main(
    num_records: int = 100,
    chunk_size: int = 10,
    storage: StorageBackend = "modal",
):
    """
    Local entrypoint for testing.

    Run with:
        modal run app.py --num-records 100
        modal run app.py --num-records 1000 --storage modal
        modal run app.py --num-records 500 --storage local
    """
    # Generate sample data
    records = [
        {
            "serial": f"SN-{i:06d}",
            "product": f"Product-{i % 10}",
            "batch": f"BATCH-{i // 100}",
            "date": "2026-01-01",
        }
        for i in range(num_records)
    ]

    template = {
        "title": "Product Label",
        "barcode_type": "code128",
    }

    job_id = f"test-job-{num_records}"

    # Run pipeline
    result = run_vdp_pipeline.remote(
        records=records,
        template=template,
        job_id=job_id,
        chunk_size=chunk_size,
        storage_backend=storage,
    )

    print(f"\n=== Job Complete ===")
    print(f"Job ID: {result['job_id']}")
    print(f"Total Records: {result['total_records']}")
    print(f"Total Chunks: {result['total_chunks']}")
    print(f"PDF Size: {result['pdf_size']:,} bytes")
    print(f"Storage Backend: {result['storage_backend']}")
    print(f"Storage URL: {result.get('storage_url', 'N/A')}")

    # Save locally if not using local storage
    if storage != "local":
        output_path = f"/tmp/{job_id}.pdf"
        with open(output_path, "wb") as f:
            f.write(result["pdf_bytes"])
        print(f"\nLocal copy saved to: {output_path}")
    else:
        output_path = f"/tmp/{job_id}.pdf"
        with open(output_path, "wb") as f:
            f.write(result["pdf_bytes"])
        print(f"PDF saved to: {output_path}")
