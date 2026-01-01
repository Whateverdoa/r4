"""
Storage Backend Comparison - Run same job with different storage options.

This demonstrates:
- Modal Volume storage (recommended for Modal-native workflows)
- S3 storage (for integration with existing AWS infrastructure)
- Local storage (for testing and development)

Run with: modal run examples/storage_comparison.py
"""

import modal
import os
from vdp_modal import vdp_app


def run_job_with_storage(storage_backend: str, s3_bucket: str | None = None):
    """Run a VDP job with specified storage backend."""

    from vdp_modal.app import run_vdp_pipeline

    # Sample data
    records = [
        {
            "serial": f"{storage_backend.upper()}-{i:06d}",
            "product": f"Product-{i % 10}",
            "batch": f"B{i // 20:03d}",
        }
        for i in range(100)
    ]

    template = {
        "title": f"{storage_backend.title()} Storage Test",
        "barcode_type": "code128",
    }

    job_id = f"storage-test-{storage_backend}"

    print(f"\n{'=' * 60}")
    print(f"TESTING: {storage_backend.upper()} STORAGE")
    print('=' * 60)

    # Run pipeline
    result = run_vdp_pipeline.remote(
        records=records,
        template=template,
        job_id=job_id,
        chunk_size=25,
        storage_backend=storage_backend,
        s3_bucket=s3_bucket,
    )

    print(f"\n✓ Job Complete:")
    print(f"  • Records: {result['total_records']}")
    print(f"  • PDF Size: {result['pdf_size']:,} bytes")
    print(f"  • Storage URL: {result.get('storage_url', 'N/A')}")

    return result


def main():
    """Compare different storage backends."""

    print("\n" + "=" * 60)
    print("STORAGE BACKEND COMPARISON")
    print("=" * 60)
    print("""
This example runs the same VDP job with different storage backends
to demonstrate the flexibility of the platform.
    """)

    with modal.runner.deploy_app(vdp_app):
        # Test 1: Modal Volume Storage
        print("\n[1/3] Modal Volume Storage")
        print("     No credentials needed, persistent, fast")
        modal_result = run_job_with_storage("modal")

        # Test 2: Local Storage
        print("\n[2/3] Local Storage")
        print("     Returns bytes, user saves locally")
        local_result = run_job_with_storage("local")

        # Test 3: S3 Storage (if configured)
        s3_bucket = os.getenv("VDP_S3_BUCKET")
        if s3_bucket:
            print("\n[3/3] S3 Storage")
            print(f"     Uploading to bucket: {s3_bucket}")
            s3_result = run_job_with_storage("s3", s3_bucket=s3_bucket)
        else:
            print("\n[3/3] S3 Storage - SKIPPED")
            print("     Set VDP_S3_BUCKET environment variable to test")

        # Summary
        print("\n" + "=" * 60)
        print("STORAGE COMPARISON SUMMARY")
        print("=" * 60)

        print(f"\n{'Backend':<15} {'URL':<30} {'Status':<10}")
        print("-" * 60)
        print(f"{'Modal':<15} {modal_result.get('storage_url', 'N/A'):<30} {'✓ Success':<10}")
        print(f"{'Local':<15} {local_result.get('storage_url', 'N/A'):<30} {'✓ Success':<10}")

        if s3_bucket:
            print(f"{'S3':<15} {s3_result.get('storage_url', 'N/A'):<30} {'✓ Success':<10}")
        else:
            print(f"{'S3':<15} {'Not configured':<30} {'- Skipped':<10}")

        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        print("""
• Use MODAL STORAGE for:
  - Modal-native workflows
  - No AWS dependency
  - Fast inter-function access
  - Built-in versioning

• Use S3 STORAGE for:
  - Integration with existing AWS infrastructure
  - Long-term archival
  - External system access
  - CDN distribution

• Use LOCAL STORAGE for:
  - Development and testing
  - One-off jobs
  - When you want direct bytes access
        """)

        print("✓✓✓ Comparison Complete! ✓✓✓\n")


if __name__ == "__main__":
    main()
