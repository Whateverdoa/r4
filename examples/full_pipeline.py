"""
Full pipeline example - Complete VDP workflow with S3 upload.

This demonstrates:
- Large-scale parallel processing (4000 labels)
- Sheet layout assembly
- S3 upload
- Complete workflow orchestration

Run with: modal run examples/full_pipeline.py

Note: Set AWS credentials in environment variables:
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
"""

import modal
import os
from vdp_modal import vdp_app


def main():
    """Run complete VDP pipeline with S3 upload."""

    # Configuration
    NUM_LABELS = 4000
    CHUNK_SIZE = 100
    S3_BUCKET = os.getenv("VDP_S3_BUCKET")  # Set this env var

    # Generate sample data
    records = []
    for i in range(NUM_LABELS):
        records.append({
            "serial": f"PKG-{i:08d}",
            "product_name": f"Widget Type {i % 20}",
            "sku": f"SKU-{(i % 100):04d}",
            "batch": f"BATCH-{i // 500:04d}",
            "manufacture_date": "2026-01-01",
            "expiry_date": "2027-01-01",
            "weight": f"{(i % 100 + 50)}.0g",
            "quantity": str((i % 10) + 1),
        })

    # Template with detailed layout
    template = {
        "title": "Packaging Label",
        "barcode_type": "gs1-128",
        "required_fields": ["serial", "product_name"],
    }

    job_id = f"full-pipeline-{NUM_LABELS}"

    print("=" * 60)
    print("VDP PIPELINE - Full Workflow")
    print("=" * 60)
    print(f"\nJob ID: {job_id}")
    print(f"Total Labels: {NUM_LABELS:,}")
    print(f"Chunk Size: {CHUNK_SIZE}")
    print(f"Expected Parallel Workers: {NUM_LABELS // CHUNK_SIZE}")
    print(f"Barcode Type: {template['barcode_type']}")

    if S3_BUCKET:
        print(f"S3 Upload: Enabled (bucket: {S3_BUCKET})")
    else:
        print("S3 Upload: Disabled (set VDP_S3_BUCKET env var to enable)")

    print("\nStarting pipeline...\n")

    from vdp_modal.app import run_vdp_pipeline

    with modal.runner.deploy_app(vdp_app):
        # Run complete pipeline
        result = run_vdp_pipeline.remote(
            records=records,
            template=template,
            job_id=job_id,
            chunk_size=CHUNK_SIZE,
            s3_bucket=S3_BUCKET,
            s3_prefix="production/vdp-output",
        )

        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nJob ID: {result['job_id']}")
        print(f"Total Records: {result['total_records']:,}")
        print(f"Total Chunks Processed: {result['total_chunks']}")
        print(f"Final PDF Size: {result['pdf_size']:,} bytes")
        print(f"Final PDF Size (MB): {result['pdf_size'] / (1024 * 1024):.2f} MB")

        if "s3_url" in result:
            print(f"\n✓ Uploaded to S3: {result['s3_url']}")

        # Save local copy
        output_path = f"/tmp/{job_id}.pdf"
        with open(output_path, "wb") as f:
            f.write(result["pdf_bytes"])

        print(f"\n✓ Local copy saved: {output_path}")

        # Statistics
        avg_size_per_label = result["pdf_size"] / result["total_records"]
        print(f"\nStatistics:")
        print(f"  • Average size per label: {avg_size_per_label:,.0f} bytes")
        print(f"  • Compression ratio: {avg_size_per_label / 1024:.1f} KB/label")

        print("\n✓✓✓ Pipeline Success! ✓✓✓\n")


if __name__ == "__main__":
    main()
