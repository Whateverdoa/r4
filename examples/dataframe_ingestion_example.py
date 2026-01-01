"""
DataFrame Ingestion Example - Excel/CSV → VDP Pipeline

This demonstrates the complete workflow:
1. Load data from Excel/CSV
2. Define template with field mappings and transforms
3. Convert DataFrame to VDPBatch
4. Process with Modal workers
5. Get final PDF output

Run with: python examples/dataframe_ingestion_example.py
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
from vdp_modal.vdp_input import (
    dataframe_to_vdp_batch,
    TemplateConfig,
    FieldMapping,
    BarcodeConfig,
)
from vdp_modal.transforms import list_transforms


def create_sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame simulating data from MIS/Excel."""
    data = {
        "Article": ["ART-001", "ART-002", "ART-003", "ART-004", "ART-005"],
        "Description": [
            "Widget Type A",
            "Widget Type B",
            "Component X",
            "Component Y",
            "Assembly Z",
        ],
        "EAN": [
            "123456789012",  # 12 digits (will add check digit)
            "234567890123",
            "345678901234",
            "456789012345",
            "567890123456",
        ],
        "Batch": ["BATCH-001", "BATCH-001", "BATCH-002", "BATCH-002", "BATCH-003"],
        "Quantity": [10, 5, 15, 20, 8],
        "Weight": [1.25, 2.50, 0.75, 1.00, 3.25],
        "Manufacture Date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02", "2026-01-03"],
    }

    return pd.DataFrame(data)


def example_basic_ingestion():
    """Example 1: Basic DataFrame ingestion."""
    print("=" * 60)
    print("EXAMPLE 1: BASIC DATAFRAME INGESTION")
    print("=" * 60)

    # Create sample data
    df = create_sample_dataframe()

    print(f"\nInput DataFrame ({len(df)} rows):")
    print(df.to_string(index=False))

    # Define template with field mappings
    template = TemplateConfig(
        template_id="product_label_v2",
        label_width_mm=100,
        label_height_mm=150,
        dpi=300,
        fields=[
            FieldMapping(
                source_column="Article",
                target_name="product_code",
                transform="trim",
            ),
            FieldMapping(
                source_column="Description",
                target_name="product_name",
                transform="uppercase",
            ),
            FieldMapping(
                source_column="EAN",
                target_name="barcode",
                transform="ean13_check_digit",  # Add EAN-13 check digit
            ),
            FieldMapping(
                source_column="Batch",
                target_name="batch_number",
            ),
            FieldMapping(
                source_column="Weight",
                target_name="weight",
                transform="format_decimal_2",
            ),
            FieldMapping(
                source_column="Manufacture Date",
                target_name="mfg_date",
                transform="date_yyyymmdd",
            ),
        ],
        barcodes={
            "main_barcode": BarcodeConfig(
                field_name="barcode",
                barcode_type="ean13",
                format="raster",
                dpi=300,
            )
        },
    )

    # Convert to VDPBatch
    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="basic-ingestion-001",
        quantity_column="Quantity",  # Use Quantity column for print qty
    )

    print(f"\n✓ VDPBatch Created:")
    print(f"  • Job ID: {batch.job_id}")
    print(f"  • Template: {batch.template.template_id}")
    print(f"  • Records: {len(batch.records)}")
    print(f"  • Total Labels (with quantities): {batch.total_labels}")

    # Show first record
    print(f"\n✓ First Record (transformed):")
    first_record = batch.records[0]
    for key, value in first_record.fields.items():
        print(f"  • {key}: {value}")
    print(f"  • Quantity: {first_record.quantity}")

    # Show second record for comparison
    print(f"\n✓ Second Record:")
    second_record = batch.records[1]
    print(f"  • product_code: {second_record.fields['product_code']}")
    print(f"  • product_name: {second_record.fields['product_name']}")
    print(f"  • barcode: {second_record.fields['barcode']} (with check digit)")
    print(f"  • Quantity: {second_record.quantity}")

    return batch


def example_quantity_expansion():
    """Example 2: Quantity expansion."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: QUANTITY EXPANSION")
    print("=" * 60)

    df = create_sample_dataframe()

    template = TemplateConfig(
        template_id="simple_label",
        label_width_mm=100,
        label_height_mm=60,
        fields=[
            FieldMapping(source_column="Article", target_name="article"),
            FieldMapping(source_column="Description", target_name="name"),
        ],
    )

    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="quantity-expansion-001",
        quantity_column="Quantity",
    )

    print(f"\n✓ Before Expansion:")
    print(f"  • Records: {len(batch.records)}")
    print(f"  • Total Labels: {batch.total_labels}")
    print(f"  • Quantities: {[r.quantity for r in batch.records]}")

    # Expand quantities
    expanded_batch = batch.expand_quantities()

    print(f"\n✓ After Expansion:")
    print(f"  • Records: {len(expanded_batch.records)}")
    print(f"  • Total Labels: {expanded_batch.total_labels}")
    print(f"  • All quantities are now 1")

    print(f"\n✓ Example: Article 'ART-001' had quantity=10")
    art001_count = sum(
        1 for r in expanded_batch.records if r.fields.get("article") == "ART-001"
    )
    print(f"  → Now appears {art001_count} times as separate records")


def example_chunking():
    """Example 3: Chunking for parallel workers."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: CHUNKING FOR PARALLEL WORKERS")
    print("=" * 60)

    # Create larger dataset
    data = {
        "Article": [f"ART-{i:04d}" for i in range(250)],
        "Description": [f"Product {i}" for i in range(250)],
        "Barcode": [f"{1234567890 + i:012d}" for i in range(250)],
    }
    df = pd.DataFrame(data)

    template = TemplateConfig(
        template_id="bulk_labels",
        label_width_mm=100,
        label_height_mm=60,
        fields=[
            FieldMapping(source_column="Article", target_name="article"),
            FieldMapping(source_column="Description", target_name="description"),
            FieldMapping(source_column="Barcode", target_name="barcode"),
        ],
    )

    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="bulk-job-001",
    )

    print(f"\n✓ Original Batch:")
    print(f"  • Records: {len(batch.records)}")

    # Split into chunks for parallel processing
    chunks = batch.chunk_for_workers(chunk_size=50)

    print(f"\n✓ After Chunking (chunk_size=50):")
    print(f"  • Total Chunks: {len(chunks)}")
    print(f"  • Records per chunk:")

    for i, chunk in enumerate(chunks):
        print(f"    - Chunk {i}: {len(chunk.records)} records (job_id: {chunk.job_id})")

    print(f"\n✓ Each chunk can be processed by a separate Modal worker")


def example_modal_format():
    """Example 4: Convert to Modal format."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 4: CONVERT TO MODAL FORMAT")
    print("=" * 60)

    df = create_sample_dataframe().head(3)

    template = TemplateConfig(
        template_id="modal_demo",
        label_width_mm=100,
        label_height_mm=60,
        fields=[
            FieldMapping(source_column="Article", target_name="serial"),
            FieldMapping(source_column="Description", target_name="product"),
        ],
    )

    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="modal-demo-001",
    )

    # Convert to Modal format
    modal_format = batch.to_modal_format()

    print(f"\n✓ VDPBatch → Modal Format:")
    print(f"\nJob ID: {modal_format['job_id']}")
    print(f"\nTemplate:")
    for key, value in modal_format["template"].items():
        print(f"  • {key}: {value}")

    print(f"\nRecords (ready for run_vdp_pipeline):")
    for i, record in enumerate(modal_format["records"][:2]):
        print(f"\n  Record {i + 1}:")
        for key, value in record.items():
            print(f"    • {key}: {value}")

    print(f"\n✓ This can be passed directly to run_vdp_pipeline.remote()")


def example_available_transforms():
    """Example 5: Show available transforms."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 5: AVAILABLE TRANSFORMS")
    print("=" * 60)

    transforms = list_transforms()

    print(f"\n✓ {len(transforms)} transforms available:\n")

    categories = {
        "String": ["trim", "uppercase", "lowercase", "title", "remove_spaces", "alphanumeric_only"],
        "Numeric": ["zero_pad_6", "zero_pad_8", "zero_pad_12", "format_decimal_2"],
        "Barcode": [
            "ean13_check_digit",
            "ean8_check_digit",
            "sscc18_from_base",
            "gtin_check_digit",
        ],
        "Date": ["date_yyyymmdd", "date_ddmmyyyy", "date_mmddyyyy"],
    }

    for category, transform_list in categories.items():
        print(f"{category} Transforms:")
        for t in transform_list:
            if t in transforms:
                print(f"  • {t}")
        print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("DATAFRAME INGESTION EXAMPLES")
    print("=" * 60)
    print("""
This demonstrates the complete data ingestion pipeline:

    DataFrame → Normalize → Validate → Transform → VDPBatch → Workers

Key features:
• Field mapping with transforms
• Automatic validation
• Quantity expansion
• Chunking for parallel workers
• Modal-ready output format
    """)

    # Run examples
    example_basic_ingestion()
    example_quantity_expansion()
    example_chunking()
    example_modal_format()
    example_available_transforms()

    # Summary
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
To use with Modal:

1. Create your DataFrame (from Excel, CSV, MIS):
   df = pd.read_excel("orders.xlsx")

2. Define your template:
   template = TemplateConfig(
       template_id="my_label",
       label_width_mm=100,
       label_height_mm=150,
       fields=[...],
   )

3. Convert to VDPBatch:
   batch = dataframe_to_vdp_batch(df, template, "job-001")

4. Send to Modal:
   result = run_vdp_pipeline.remote(**batch.to_modal_format())

5. Get your PDF:
   pdf_bytes = result["pdf_bytes"]

See examples/dataframe_to_modal_example.py for complete Modal integration.
    """)

    print("\n✓✓✓ Examples Complete! ✓✓✓\n")


if __name__ == "__main__":
    main()
