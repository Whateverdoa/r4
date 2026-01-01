"""
Simple VDP example - Generate 1000 labels with barcodes in parallel.

Run with: modal run examples/simple_vdp.py
"""

import modal
from vdp_modal import vdp_app

# Configuration
NUM_LABELS = 1000
CHUNK_SIZE = 100


def main():
    """Generate 1000 product labels."""

    # Sample data
    records = [
        {
            "serial": f"SN-{i:08d}",
            "product": f"Product-{i % 50}",
            "batch": f"BATCH-{i // 100:04d}",
            "date": "2026-01-01",
            "qty": str((i % 10) + 1),
        }
        for i in range(NUM_LABELS)
    ]

    # Template configuration
    template = {
        "title": "Product Label",
        "barcode_type": "code128",
    }

    job_id = f"simple-vdp-{NUM_LABELS}"

    print(f"Starting VDP job: {job_id}")
    print(f"Total records: {len(records)}")
    print(f"Chunk size: {CHUNK_SIZE}")
    print(f"Expected chunks: {len(records) // CHUNK_SIZE}")

    # Import the function from the Modal app
    from vdp_modal.app import run_vdp_pipeline

    with modal.runner.deploy_app(vdp_app):
        # Run the pipeline
        result = run_vdp_pipeline.remote(
            records=records,
            template=template,
            job_id=job_id,
            chunk_size=CHUNK_SIZE,
        )

        print("\n=== Job Complete ===")
        print(f"Job ID: {result['job_id']}")
        print(f"Total Records: {result['total_records']:,}")
        print(f"Total Chunks: {result['total_chunks']}")
        print(f"PDF Size: {result['pdf_size']:,} bytes")

        # Save output
        output_path = f"/tmp/{job_id}.pdf"
        with open(output_path, "wb") as f:
            f.write(result["pdf_bytes"])

        print(f"\nPDF saved to: {output_path}")
        print("✓ Success!")


if __name__ == "__main__":
    main()
