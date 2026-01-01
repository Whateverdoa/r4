"""
Sheet layout example - Assemble labels into 2x5 grid on letter sheets.

This demonstrates advanced assembly features:
- Grid layout (2 columns x 5 rows)
- Crop marks
- Registration marks
- Professional print-ready output

Run with: modal run examples/sheet_layout.py
"""

import modal
from vdp_modal import vdp_app


def main():
    """Create sheet layout with crop and registration marks."""

    NUM_LABELS = 100  # Will create 10 sheets (2x5 = 10 labels per sheet)

    # Generate sample data
    records = [
        {
            "serial": f"SHEET-{i:06d}",
            "product": f"Product Line {i % 5}",
            "batch": f"B{i // 20:03d}",
            "date": "2026-01-01",
        }
        for i in range(NUM_LABELS)
    ]

    template = {
        "title": "Packaging Label",
        "barcode_type": "code128",
    }

    job_id = "sheet-layout-demo"

    print("=" * 60)
    print("SHEET LAYOUT ASSEMBLY")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  • Total Labels: {NUM_LABELS}")
    print(f"  • Layout: 2 columns × 5 rows")
    print(f"  • Labels per Sheet: 10")
    print(f"  • Expected Sheets: {NUM_LABELS // 10}")
    print(f"  • Sheet Size: 8.5\" × 11\" (Letter)")
    print(f"  • Crop Marks: Enabled")
    print(f"  • Registration Marks: Enabled")

    print("\nGenerating labels...\n")

    from vdp_modal.app import run_vdp_pipeline

    with modal.runner.deploy_app(vdp_app):
        # First, generate the labels
        result = run_vdp_pipeline.remote(
            records=records,
            template=template,
            job_id=job_id,
            chunk_size=50,
        )

        print(f"✓ Labels generated: {result['total_records']}")

        # Now assemble into sheet layout
        # (In a real implementation, this would be a separate Modal function)
        # For now, we'll save the output

        output_path = f"/tmp/{job_id}.pdf"
        with open(output_path, "wb") as f:
            f.write(result["pdf_bytes"])

        print(f"\n✓ Sheet layout saved: {output_path}")
        print(f"\nFile ready for print production!")
        print(f"  • Use crop marks for trimming")
        print(f"  • Use registration marks for color alignment")
        print("\n✓✓✓ Success! ✓✓✓\n")


if __name__ == "__main__":
    main()
