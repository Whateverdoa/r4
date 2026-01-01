"""
Template Builder Examples

This demonstrates:
- Fluent API for building templates
- Saving/loading templates to/from JSON
- Template registry for managing templates
- Quick builders for common use cases
- Template introspection and validation

Run with: python examples/template_builder_example.py
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from vdp_modal.template_builder import (
    TemplateBuilder,
    TemplateRegistry,
    print_template_info,
    validate_template,
    create_product_label_template,
    create_shipping_label_template,
    create_barcode_only_template,
)


def example_fluent_api():
    """Example 1: Build template using fluent API."""
    print("=" * 60)
    print("EXAMPLE 1: FLUENT API TEMPLATE BUILDER")
    print("=" * 60)

    # Build template with fluent API
    template = (
        TemplateBuilder("product_label_v3")
        .size(100, 150)  # 100mm x 150mm
        .dpi(300)
        .field("Article", "product_code", transform="trim")
        .field("Description", "product_name", transform="uppercase")
        .field("EAN", "barcode", transform="ean13_check_digit", required=True)
        .field("Batch", "batch_number")
        .field("Weight", "weight", transform="format_decimal_2", required=False)
        .field("MfgDate", "mfg_date", transform="date_yyyymmdd", required=False)
        .barcode("barcode", "ean13", format="raster", dpi=300)
        .layout("single")
        .metadata("created_by", "template_builder_example")
        .metadata("version", "3.0")
        .build()
    )

    print("\n✓ Template built using fluent API:")
    print_template_info(template)

    return template


def example_save_load():
    """Example 2: Save and load templates."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: SAVE AND LOAD TEMPLATES")
    print("=" * 60)

    # Build template
    template = (
        TemplateBuilder("shipping_label_v1")
        .size_inches(4, 6)  # 4x6 inches
        .field("OrderID", "order_id")
        .field("Tracking", "tracking_number")
        .field("CustomerName", "customer_name")
        .field("Address", "address")
        .barcode("tracking_number", "code128")
        .build()
    )

    # Save to JSON
    template.save_to_file("/tmp/shipping_label_v1.json")
    print("\n✓ Template saved to: /tmp/shipping_label_v1.json")

    # Load from JSON
    loaded_template = template.load_from_file("/tmp/shipping_label_v1.json")
    print("\n✓ Template loaded from JSON:")
    print_template_info(loaded_template)

    # Verify they match
    assert loaded_template.template_id == template.template_id
    assert len(loaded_template.fields) == len(template.fields)
    print("\n✓ Loaded template matches original!")


def example_template_registry():
    """Example 3: Template registry."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: TEMPLATE REGISTRY")
    print("=" * 60)

    # Initialize registry
    registry = TemplateRegistry("/tmp/vdp_templates")

    # Create and save multiple templates
    templates = [
        create_product_label_template("product_label_std"),
        create_shipping_label_template("shipping_label_std"),
        create_barcode_only_template("barcode_gs1_128", "gs1-128"),
    ]

    print("\n✓ Saving templates to registry...")
    for template in templates:
        registry.save(template)
        print(f"  • Saved: {template.template_id}")

    # List all templates
    print(f"\n✓ Templates in registry:")
    for template_id in registry.list_templates():
        info = registry.get_template_info(template_id)
        print(f"\n  {template_id}:")
        print(f"    • Size: {info['label_size']}")
        print(f"    • Fields: {info['num_fields']}")
        print(f"    • Barcodes: {info['num_barcodes']}")

    # Load a template
    print(f"\n✓ Loading template from registry...")
    loaded = registry.load("product_label_std")
    print_template_info(loaded)


def example_quick_builders():
    """Example 4: Quick builders for common templates."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 4: QUICK BUILDERS")
    print("=" * 60)

    print("\n[1] Product Label Template:")
    product_template = create_product_label_template()
    print_template_info(product_template)

    print("\n\n[2] Shipping Label Template:")
    shipping_template = create_shipping_label_template()
    print_template_info(shipping_template)

    print("\n\n[3] Barcode-Only Template:")
    barcode_template = create_barcode_only_template()
    print_template_info(barcode_template)


def example_validation():
    """Example 5: Template validation."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 5: TEMPLATE VALIDATION")
    print("=" * 60)

    # Create valid template
    valid_template = (
        TemplateBuilder("valid_template")
        .size(100, 150)
        .field("Article", "article")
        .field("EAN", "barcode", transform="ean13_check_digit")
        .barcode("barcode", "ean13")
        .build()
    )

    print("\n✓ Validating good template...")
    warnings = validate_template(valid_template)
    if not warnings:
        print("  ✓ No warnings - template is valid!")
    else:
        print(f"  ⚠️  Warnings: {warnings}")

    # Create template with issues
    print("\n✓ Creating template with issues...")
    problematic_template = (
        TemplateBuilder("problematic_template")
        .size(100, 150)
        .field("Article", "article", transform="unknown_transform")  # Unknown transform
        .barcode("nonexistent_field", "code128")  # References non-existent field
        .build()
    )

    print("\n✓ Validating problematic template...")
    warnings = validate_template(problematic_template)
    if warnings:
        print(f"  ⚠️  Found {len(warnings)} warning(s):")
        for i, warning in enumerate(warnings, 1):
            print(f"    {i}. {warning}")


def example_chaining_patterns():
    """Example 6: Advanced chaining patterns."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 6: ADVANCED CHAINING PATTERNS")
    print("=" * 60)

    # Start with base template
    base_builder = (
        TemplateBuilder("advanced_label")
        .size(100, 150)
        .dpi(300)
    )

    # Add common fields
    base_builder = (
        base_builder.field("Article", "article", transform="trim")
        .field("Description", "description", transform="uppercase")
    )

    # Conditionally add barcode
    include_barcode = True
    if include_barcode:
        base_builder = base_builder.field("EAN", "barcode", transform="ean13_check_digit")
        base_builder = base_builder.barcode("barcode", "ean13")

    # Add metadata
    base_builder = (
        base_builder.metadata("created_by", "advanced_example")
        .metadata("version", "1.0")
        .metadata("include_barcode", str(include_barcode))
    )

    # Build final template
    template = base_builder.build()

    print("\n✓ Template built with conditional logic:")
    print_template_info(template)


def example_template_to_dict():
    """Example 7: Template serialization to dict."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 7: TEMPLATE TO DICT")
    print("=" * 60)

    template = create_product_label_template()

    # Convert to dict
    template_dict = template.to_dict(template)

    print("\n✓ Template as dictionary:")
    import json

    print(json.dumps(template_dict, indent=2))


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("TEMPLATE BUILDER EXAMPLES")
    print("=" * 60)
    print("""
The template builder provides:

• Fluent API for programmatic template creation
• JSON serialization for saving/loading templates
• Template registry for organizing templates
• Quick builders for common use cases
• Validation and introspection tools
    """)

    # Run examples
    example_fluent_api()
    example_save_load()
    example_template_registry()
    example_quick_builders()
    example_validation()
    example_chaining_patterns()
    example_template_to_dict()

    # Summary
    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Benefits of Template Builder:

✓ No manual Pydantic object creation
✓ Fluent, readable API
✓ Save/load templates as JSON
✓ Reusable template library
✓ Validation before use
✓ Quick builders for common cases

Usage in production:

1. Build once, save to registry:
   template = TemplateBuilder("my_label").size(...).field(...).build()
   registry.save(template)

2. Load and reuse:
   template = registry.load("my_label")
   batch = dataframe_to_vdp_batch(df, template, "job-001")

3. Share templates:
   - Save to JSON
   - Check into version control
   - Share across projects
    """)

    print("\n✓✓✓ Examples Complete! ✓✓✓\n")


if __name__ == "__main__":
    main()
