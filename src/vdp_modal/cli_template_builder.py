"""Interactive CLI template builder.

This provides an interactive command-line interface for building VDP templates
without writing code.

Usage:
    python -m vdp_modal.cli_template_builder

Features:
- Step-by-step template creation
- Field mapping wizard
- Transform selection
- Barcode configuration
- Save to registry or file
- Template preview
"""

from typing import Optional
from .template_builder import TemplateBuilder, TemplateRegistry, print_template_info, validate_template
from .transforms import list_transforms, get_transform_help


def prompt(message: str, default: Optional[str] = None) -> str:
    """Prompt user for input."""
    if default:
        message = f"{message} [{default}]"
    response = input(f"{message}: ").strip()
    return response if response else (default or "")


def prompt_yes_no(message: str, default: bool = False) -> bool:
    """Prompt user for yes/no."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{message} ({default_str}): ").strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]


def prompt_number(message: str, default: Optional[float] = None) -> float:
    """Prompt user for a number."""
    while True:
        response = prompt(message, str(default) if default else None)
        try:
            return float(response)
        except ValueError:
            print("  ⚠️  Please enter a valid number")


def prompt_int(message: str, default: Optional[int] = None) -> int:
    """Prompt user for an integer."""
    while True:
        response = prompt(message, str(default) if default else None)
        try:
            return int(response)
        except ValueError:
            print("  ⚠️  Please enter a valid integer")


def prompt_choice(message: str, choices: list[str], default: Optional[str] = None) -> str:
    """Prompt user to choose from list."""
    print(f"\n{message}:")
    for i, choice in enumerate(choices, 1):
        marker = "*" if choice == default else " "
        print(f"  {marker} {i}. {choice}")

    while True:
        response = prompt("Choice", str(choices.index(default) + 1) if default else None)
        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except (ValueError, IndexError):
            pass
        print("  ⚠️  Invalid choice")


def build_template_interactive() -> TemplateBuilder:
    """Build template using interactive prompts."""
    print("\n" + "=" * 60)
    print("INTERACTIVE TEMPLATE BUILDER")
    print("=" * 60)

    # Template ID
    print("\n[1] Template Identification")
    template_id = prompt("Template ID (unique name)", "my_template")

    builder = TemplateBuilder(template_id)

    # Label size
    print("\n[2] Label Size")
    size_unit = prompt_choice("Size unit", ["millimeters", "inches"], "millimeters")

    if size_unit == "millimeters":
        width = prompt_number("Width (mm)", 100)
        height = prompt_number("Height (mm)", 150)
        builder.size(width, height)
    else:
        width = prompt_number("Width (inches)", 4)
        height = prompt_number("Height (inches)", 6)
        builder.size_inches(width, height)

    # DPI
    print("\n[3] Resolution")
    dpi = prompt_int("DPI", 300)
    builder.dpi(dpi)

    # Fields
    print("\n[4] Field Mappings")
    print("Add fields that map DataFrame columns to label fields")

    available_transforms = list_transforms()

    while True:
        print(f"\n  Current fields: {len(builder._fields)}")

        if not prompt_yes_no("Add a field?", True):
            break

        source_column = prompt("  Source column name (from DataFrame)")
        if not source_column:
            continue

        target_name = prompt("  Target field name", source_column.lower().replace(" ", "_"))

        required = prompt_yes_no("  Required field?", True)

        default = None
        if not required:
            if prompt_yes_no("  Set default value?", False):
                default = prompt("    Default value")

        # Transform
        transform = None
        if prompt_yes_no("  Apply transform?", False):
            print("\n  Available transforms:")
            print("    String: trim, uppercase, lowercase, title")
            print("    Numeric: zero_pad_6, zero_pad_8, format_decimal_2")
            print("    Barcode: ean13_check_digit, ean8_check_digit, sscc18_from_base")
            print("    Date: date_yyyymmdd, date_ddmmyyyy")
            print(f"\n    Full list: {', '.join(available_transforms[:10])}...")

            transform = prompt("    Transform name (or blank)")
            if transform and transform not in available_transforms:
                print(f"    ⚠️  Warning: '{transform}' is not a known transform")

        builder.field(
            source_column=source_column,
            target_name=target_name,
            required=required,
            default=default,
            transform=transform,
        )

        print(f"  ✓ Added field: {source_column} → {target_name}")

    # Barcodes
    print("\n[5] Barcodes")
    if prompt_yes_no("Add barcodes?", True):
        while True:
            if builder._barcodes and not prompt_yes_no("Add another barcode?", False):
                break

            # Show available fields
            field_names = [f.target_name for f in builder._fields]
            if not field_names:
                print("  ⚠️  No fields defined yet. Add fields first.")
                break

            print(f"\n  Available fields: {', '.join(field_names)}")
            field_name = prompt("  Field containing barcode data")

            if field_name not in field_names:
                print(f"  ⚠️  Field '{field_name}' not found")
                continue

            barcode_type = prompt_choice(
                "  Barcode type",
                ["code128", "code39", "ean13", "ean8", "gs1-128", "qr", "datamatrix"],
                "code128",
            )

            format_type = prompt_choice("  Format", ["raster", "vector"], "raster")

            if format_type == "raster":
                bc_dpi = prompt_int("  DPI", 300)
                builder.barcode(field_name, barcode_type, format="raster", dpi=bc_dpi)
            else:
                scale = prompt_number("  Scale", 2.0)
                height = prompt_int("  Height (modules)", 50)
                builder.barcode(field_name, barcode_type, format="vector", scale=scale, height=height)

            print(f"  ✓ Added barcode: {field_name} ({barcode_type})")

    # Layout
    print("\n[6] Layout")
    layout_type = prompt_choice("Layout type", ["single", "grid", "roll"], "single")

    if layout_type == "grid":
        columns = prompt_int("Columns per sheet", 2)
        rows = prompt_int("Rows per sheet", 5)
        builder.layout("grid", columns, rows)
    else:
        builder.layout(layout_type)

    # Metadata
    print("\n[7] Metadata (optional)")
    if prompt_yes_no("Add metadata?", False):
        while True:
            key = prompt("  Metadata key (or blank to finish)")
            if not key:
                break
            value = prompt(f"  Value for '{key}'")
            builder.metadata(key, value)

    return builder


def main():
    """Main CLI entry point."""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         VDP TEMPLATE BUILDER (Interactive CLI)          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

This tool helps you create VDP templates interactively.
You can save templates to the registry or export as JSON.
    """)

    try:
        # Build template
        builder = build_template_interactive()

        # Build and validate
        print("\n" + "=" * 60)
        print("BUILDING TEMPLATE...")
        print("=" * 60)

        try:
            template = builder.build()
            print("\n✓ Template built successfully!")
        except ValueError as e:
            print(f"\n❌ Error building template: {e}")
            return

        # Show preview
        print("\n" + "=" * 60)
        print("TEMPLATE PREVIEW")
        print("=" * 60)
        print_template_info(template)

        # Validate
        print("\n" + "=" * 60)
        print("VALIDATION")
        print("=" * 60)
        warnings = validate_template(template)

        if not warnings:
            print("✓ No warnings - template is valid!")
        else:
            print(f"⚠️  Found {len(warnings)} warning(s):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")

            if not prompt_yes_no("\nContinue despite warnings?", True):
                print("Template not saved.")
                return

        # Save template
        print("\n" + "=" * 60)
        print("SAVE TEMPLATE")
        print("=" * 60)

        save_option = prompt_choice(
            "Where to save?",
            ["registry", "file", "skip"],
            "registry",
        )

        if save_option == "registry":
            registry = TemplateRegistry()
            filepath = registry.save(template)
            print(f"\n✓ Template saved to registry: {filepath}")
            print(f"\nTo load this template:")
            print(f"  from vdp_modal.template_builder import TemplateRegistry")
            print(f"  registry = TemplateRegistry()")
            print(f"  template = registry.load('{template.template_id}')")

        elif save_option == "file":
            filepath = prompt("File path", f"{template.template_id}.json")
            template.save_to_file(filepath)
            print(f"\n✓ Template saved to: {filepath}")
            print(f"\nTo load this template:")
            print(f"  from vdp_modal.vdp_input import TemplateConfig")
            print(f"  template = TemplateConfig.load_from_file('{filepath}')")

        else:
            print("\nTemplate not saved.")

        print("\n✓✓✓ Template Builder Complete! ✓✓✓\n")

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
