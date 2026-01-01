"""
Modal Storage example - Use Modal Volumes and Dicts instead of S3.

This demonstrates:
- Saving PDFs to Modal Volumes
- Storing metadata in Modal Dicts
- Retrieving job results
- No AWS credentials needed!

Run with: modal run examples/modal_storage_example.py
"""

import modal
from vdp_modal import vdp_app


def main():
    """Generate VDP job and save to Modal storage."""

    NUM_LABELS = 500

    # Generate sample data
    records = [
        {
            "serial": f"MOD-{i:08d}",
            "product": f"Component-{i % 25}",
            "batch": f"BATCH-{i // 50:04d}",
            "date": "2026-01-01",
        }
        for i in range(NUM_LABELS)
    ]

    template = {
        "title": "Modal Storage Demo",
        "barcode_type": "code128",
    }

    job_id = "modal-storage-demo-001"

    print("=" * 60)
    print("MODAL STORAGE EXAMPLE")
    print("=" * 60)
    print(f"\nJob ID: {job_id}")
    print(f"Total Labels: {NUM_LABELS:,}")
    print(f"Storage: Modal Volume + Modal Dict")
    print(f"Credentials Required: None!")
    print("\nStarting job...\n")

    from vdp_modal.app import run_vdp_pipeline, get_job_metadata

    with modal.runner.deploy_app(vdp_app):
        # Run pipeline with Modal storage
        result = run_vdp_pipeline.remote(
            records=records,
            template=template,
            job_id=job_id,
            chunk_size=50,
            storage_backend="modal",  # Use Modal storage!
            save_metadata=True,  # Save to Modal Dict
        )

        print("\n" + "=" * 60)
        print("JOB COMPLETE")
        print("=" * 60)
        print(f"\nJob ID: {result['job_id']}")
        print(f"Total Records: {result['total_records']:,}")
        print(f"PDF Size: {result['pdf_size']:,} bytes")
        print(f"Storage Backend: {result['storage_backend']}")
        print(f"Storage URL: {result['storage_url']}")

        # Retrieve metadata from Modal Dict
        print("\n" + "=" * 60)
        print("RETRIEVING METADATA FROM MODAL DICT")
        print("=" * 60)

        metadata = get_job_metadata.remote(job_id)

        if metadata:
            print(f"\nMetadata for job '{job_id}':")
            print(f"  • Total Records: {metadata['total_records']}")
            print(f"  • Total Chunks: {metadata['total_chunks']}")
            print(f"  • PDF Size: {metadata['pdf_size']:,} bytes")
            print(f"  • Updated At: {metadata['updated_at']}")

        # Save local copy
        output_path = f"/tmp/{job_id}.pdf"
        with open(output_path, "wb") as f:
            f.write(result["pdf_bytes"])

        print(f"\n✓ Local copy saved: {output_path}")

        print("\n" + "=" * 60)
        print("BENEFITS OF MODAL STORAGE")
        print("=" * 60)
        print("""
✓ No AWS credentials needed
✓ Persistent across function calls
✓ Shared between Modal apps
✓ Built-in versioning and snapshots
✓ Fast access within Modal ecosystem
✓ Metadata stored in Modal Dict (key-value store)
        """)

        print("✓✓✓ Success! ✓✓✓\n")


if __name__ == "__main__":
    main()
