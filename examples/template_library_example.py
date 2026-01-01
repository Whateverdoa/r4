"""
Template Library Example - Use pre-built templates

This demonstrates:
- Using templates from the built-in library
- No need to build templates from scratch
- 12+ ready-to-use templates for common scenarios
- Quick DataFrame → VDP workflow

Run with: python examples/template_library_example.py
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
from vdp_modal.template_library import (
    TEMPLATE_LIBRARY,
    list_templates,
    get_template,
    get_templates_by_category,
    print_library,
)
from vdp_modal.template_builder import print_template_info
from vdp_modal.vdp_input import dataframe_to_vdp_batch


def example_list_templates():
    """Example 1: List all available templates."""
    print("=" * 60)
    print("EXAMPLE 1: TEMPLATE LIBRARY")
    print("=" * 60)

    print_library()


def example_use_template():
    """Example 2: Use a template from library."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: USE TEMPLATE FROM LIBRARY")
    print("=" * 60)

    # Get template
    template = get_template("product_label_basic")

    print("\n✓ Loaded template 'product_label_basic':")
    print_template_info(template)

    # Create sample data
    df = pd.DataFrame(
        {
            "Article": ["ART-001", "ART-002", "ART-003"],
            "Description": ["Widget A", "Widget B", "Component X"],
            "EAN": ["123456789012", "234567890123", "345678901234"],
        }
    )

    print(f"\n✓ Sample data ({len(df)} rows):")
    print(df.to_string(index=False))

    # Convert to VDPBatch
    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="library-example-001",
    )

    print(f"\n✓ VDPBatch created:")
    print(f"  • Records: {len(batch.records)}")
    print(f"  • First record barcode: {batch.records[0].fields['barcode']}")
    print(f"    (EAN-13 check digit added automatically!)")


def example_shipping_label():
    """Example 3: Shipping label workflow."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: SHIPPING LABEL WORKFLOW")
    print("=" * 60)

    # Get shipping template
    template = get_template("shipping_label_4x6")

    print("\n✓ Using template 'shipping_label_4x6':")
    print_template_info(template)

    # Sample shipping data
    df = pd.DataFrame(
        {
            "OrderID": ["ORD-1001", "ORD-1002"],
            "Tracking": ["1Z999AA10123456784", "1Z999AA10123456785"],
            "CustomerName": ["john smith", "jane doe"],
            "Address1": ["123 Main St", "456 Oak Ave"],
            "City": ["Springfield", "Portland"],
            "State": ["il", "or"],
            "PostalCode": ["62701", "97201"],
            "Country": ["usa", "usa"],
        }
    )

    print(f"\n✓ Shipping data ({len(df)} rows):")
    print(df.head(2).to_string(index=False))

    # Convert (template will auto-uppercase state and country)
    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="shipping-001",
    )

    print(f"\n✓ VDPBatch created:")
    print(f"  • Records: {len(batch.records)}")
    print(f"\n  First label:")
    for key, value in list(batch.records[0].fields.items())[:5]:
        print(f"    • {key}: {value}")


def example_barcode_only():
    """Example 4: Barcode-only labels."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 4: BARCODE-ONLY LABELS")
    print("=" * 60)

    # Get barcode template
    template = get_template("barcode_code128_only")

    print("\n✓ Using template 'barcode_code128_only':")
    print_template_info(template)

    # Sample serial numbers
    df = pd.DataFrame({"Serial": [f"SN-{i:06d}" for i in range(1, 101)]})

    print(f"\n✓ Serial numbers: {len(df)} records")
    print(f"  First 5: {', '.join(df['Serial'].head(5).tolist())}")

    # Convert
    batch = dataframe_to_vdp_batch(
        df=df,
        template=template,
        job_id="barcodes-001",
    )

    print(f"\n✓ VDPBatch created:")
    print(f"  • {len(batch.records)} barcode labels ready for printing")


def example_by_category():
    """Example 5: Browse templates by category."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 5: TEMPLATES BY CATEGORY")
    print("=" * 60)

    categories = ["product", "shipping", "warehouse", "barcode"]

    for category in categories:
        templates = get_templates_by_category(category)
        print(f"\n{category.upper()} Templates ({len(templates)}):")
        for template_id, template in templates.items():
            desc = template.metadata.get("description", "")
            print(f"  • {template_id}: {desc}")


def example_customize_library_template():
    """Example 6: Customize a library template."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 6: CUSTOMIZE LIBRARY TEMPLATE")
    print("=" * 60)

    # Get base template
    base_template = get_template("product_label_basic")

    print("\n✓ Base template 'product_label_basic':")
    print(f"  • Fields: {len(base_template.fields)}")

    # Customize using TemplateBuilder
    from vdp_modal.template_builder import TemplateBuilder

    customized = (
        TemplateBuilder("product_label_custom")
        .size(base_template.label_width_mm, base_template.label_height_mm)
        .dpi(base_template.dpi)
        # Copy fields from base
        .field("Article", "product_code", transform="trim")
        .field("Description", "product_name", transform="uppercase")
        .field("EAN", "barcode", transform="ean13_check_digit")
        # Add custom fields
        .field("Price", "price", transform="format_decimal_2")
        .field("Category", "category", transform="uppercase")
        # Add barcode
        .barcode("barcode", "ean13")
        .metadata("based_on", "product_label_basic")
        .metadata("customized_for", "retail_pricing")
        .build()
    )

    print("\n✓ Customized template:")
    print(f"  • Fields: {len(customized.fields)}")
    print(f"  • Added: price, category")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("TEMPLATE LIBRARY EXAMPLES")
    print("=" * 60)
    print("""
The template library provides 12+ pre-built templates for common use cases.

No need to build templates from scratch - just:
1. Pick a template from the library
2. Load your DataFrame
3. Run the VDP pipeline

Categories:
• Product labels (basic, detailed)
• Shipping labels (domestic, international)
• Warehouse labels (pallets, bin locations)
• Barcode-only labels (Code 128, QR, GS1-128)
• Retail price tags
• Asset tracking tags
• Pharmaceutical labels
    """)

    # Run examples
    example_list_templates()
    example_use_template()
    example_shipping_label()
    example_barcode_only()
    example_by_category()
    example_customize_library_template()

    # Summary
    print("\n\n" + "=" * 60)
    print("QUICK START")
    print("=" * 60)
    print("""
Using templates from the library:

```python
import pandas as pd
from vdp_modal.template_library import get_template
from vdp_modal.vdp_input import dataframe_to_vdp_batch

# 1. Get template
template = get_template("product_label_basic")

# 2. Load data
df = pd.read_excel("products.xlsx")

# 3. Convert to VDPBatch
batch = dataframe_to_vdp_batch(df, template, "job-001")

# 4. Process with Modal
result = run_vdp_pipeline.remote(**batch.to_modal_format())

# Done!
```

That's it - 4 lines of code!

Available templates:
    """)

    for template_id in sorted(list_templates()):
        template = get_template(template_id)
        print(f"  • {template_id}")

    print("\n✓✓✓ Examples Complete! ✓✓✓\n")


if __name__ == "__main__":
    main()
