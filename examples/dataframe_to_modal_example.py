"""
Complete DataFrame → Modal VDP Pipeline

This example demonstrates the full workflow:
1. Load data from Excel/CSV
2. Define template with field mappings
3. Convert to VDPBatch
4. Process with Modal workers in parallel
5. Get final PDF output

Run with: modal run examples/dataframe_to_modal_example.py
"""

import modal
import pandas as pd
from pathlib import Path

# Modal app setup
app = modal.App("dataframe-vdp-demo")

# Use prepress image for full capabilities
from vdp_modal.images import prepress_image


# Helper function to create sample Excel file
def create_sample_excel(filepath: str = "/tmp/sample_orders.xlsx"):
    """Create a sample Excel file for demonstration."""
    data = {
        "Article": [f"PROD-{i:04d}" for i in range(1, 101)],
        "Description": [f"Widget Type {chr(65 + (i % 26))}" for i in range(100)],
        "EAN": [f"{1234567890 + i:012d}" for i in range(100)],
        "Batch": [f"BATCH-{(i // 20) + 1:03d}" for i in range(100)],
        "Quantity": [(i % 5) + 1 for i in range(100)],  # 1-5 labels per product
        "Weight": [round(0.5 + (i % 50) * 0.1, 2) for i in range(100)],
        "MfgDate": ["2026-01-01"] * 100,
    }

    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)
    print(f"Created sample Excel file: {filepath}")
    return filepath


@app.local_entrypoint()
def main():
    """Main entry point - runs locally."""
    print("=" * 60)
    print("DATAFRAME → MODAL VDP PIPELINE")
    print("=" * 60)

    # Step 1: Create sample data (or load your own Excel file)
    print("\n[Step 1] Creating sample data...")
    excel_file = create_sample_excel()

    # Load DataFrame
    df = pd.read_excel(excel_file)
    print(f"✓ Loaded {len(df)} rows from Excel")
    print(f"\nFirst 3 rows:")
    print(df.head(3).to_string(index=False))

    # Step 2: Define template
    print("\n[Step 2] Defining template...")

    from vdp_modal.vdp_input import TemplateConfig, FieldMapping

    template = TemplateConfig(
        template_id="product_label_v3",
        label_width_mm=100,
        label_height_mm=150,
        dpi=300,
        fields=[
            FieldMapping(
                source_column="Article",
                target_name="serial",
                transform="trim",
            ),
            FieldMapping(
                source_column="Description",
                target_name="product",
                transform="uppercase",
            ),
            FieldMapping(
                source_column="EAN",
                target_name="barcode",
                transform="ean13_check_digit",
            ),
            FieldMapping(
                source_column="Batch",
                target_name="batch",
            ),
            FieldMapping(
                source_column="Weight",
                target_name="weight",
                transform="format_decimal_2",
            ),
            FieldMapping(
                source_column="MfgDate",
                target_name="date",
                transform="date_yyyymmdd",
            ),
        ],
    )

    print(f"✓ Template defined: {template.template_id}")
    print(f"  • {len(template.fields)} fields mapped")

    # Step 3: Convert DataFrame to VDPBatch
    print("\n[Step 3] Converting DataFrame to VDPBatch...")

    from vdp_modal.vdp_input import dataframe_to_vdp_batch

    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="dataframe-demo-001",
        quantity_column="Quantity",
    )

    print(f"✓ VDPBatch created:")
    print(f"  • Job ID: {batch.job_id}")
    print(f"  • Records: {len(batch.records)}")
    print(f"  • Total labels (with quantities): {batch.total_labels}")

    # Step 4: Send to Modal workers
    print("\n[Step 4] Processing with Modal workers...")

    from vdp_modal.app import run_vdp_pipeline

    # Convert to Modal format
    modal_data = batch.to_modal_format()

    # Run pipeline on Modal
    result = run_vdp_pipeline.remote(
        records=modal_data["records"],
        template=modal_data["template"],
        job_id=modal_data["job_id"],
        chunk_size=25,  # 25 records per worker
        storage_backend="modal",  # Use Modal storage
    )

    print(f"\n✓ Processing complete!")
    print(f"  • Job ID: {result['job_id']}")
    print(f"  • Total Records: {result['total_records']}")
    print(f"  • Chunks Processed: {result['total_chunks']}")
    print(f"  • PDF Size: {result['pdf_size']:,} bytes")
    print(f"  • Storage: {result.get('storage_url', 'N/A')}")

    # Step 5: Save output
    print("\n[Step 5] Saving output...")

    output_path = f"/tmp/{result['job_id']}.pdf"
    with open(output_path, "wb") as f:
        f.write(result["pdf_bytes"])

    print(f"✓ PDF saved to: {output_path}")

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"""
Input: {len(df)} rows from Excel
Output: {result['total_records']} labels in PDF

Workflow:
  1. Excel → DataFrame (pandas)
  2. DataFrame → VDPBatch (field mapping + transforms)
  3. VDPBatch → Modal workers (parallel processing)
  4. Workers → Final PDF (assembled)
  5. PDF → Storage (Modal Volume + local)

Performance:
  • Processed in {result['total_chunks']} parallel chunks
  • {result['total_records']} labels generated
  • Output: {result['pdf_size'] / 1024:.1f} KB

Storage:
  • Modal Volume: {result.get('storage_url', 'N/A')}
  • Local copy: {output_path}
    """)

    print("\n✓✓✓ Complete! ✓✓✓\n")


if __name__ == "__main__":
    # Note: This requires modal to be installed and authenticated
    # Run with: modal run examples/dataframe_to_modal_example.py
    print("Run this file with: modal run examples/dataframe_to_modal_example.py")
