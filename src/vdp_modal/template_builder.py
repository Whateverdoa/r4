"""Template builder for VDP workflows.

This module provides tools for creating, managing, and reusing VDP templates.

Features:
- Fluent API for building templates programmatically
- JSON/YAML serialization for saving/loading templates
- Template registry for storing and discovering templates
- Template introspection and validation
- Interactive CLI builder

Usage:
    from vdp_modal.template_builder import TemplateBuilder

    # Fluent API
    template = (
        TemplateBuilder("product_label_v2")
        .size(100, 150)  # width, height in mm
        .dpi(300)
        .field("Article", "product_code", transform="trim")
        .field("EAN", "barcode", transform="ean13_check_digit", required=True)
        .field("Description", "product_name", transform="uppercase")
        .barcode("barcode", "ean13", format="raster")
        .build()
    )

    # Save for reuse
    template.save_to_file("templates/product_label_v2.json")

    # Load from file
    template = TemplateConfig.load_from_file("templates/product_label_v2.json")
"""

import json
from pathlib import Path
from typing import Any, Optional
from .vdp_input import TemplateConfig, FieldMapping, BarcodeConfig
from .transforms import list_transforms


class TemplateBuilder:
    """Fluent API for building VDP templates."""

    def __init__(self, template_id: str):
        """
        Initialize template builder.

        Args:
            template_id: Unique template identifier
        """
        self.template_id = template_id
        self._label_width_mm: Optional[float] = None
        self._label_height_mm: Optional[float] = None
        self._dpi: int = 300
        self._fields: list[FieldMapping] = []
        self._barcodes: dict[str, BarcodeConfig] = {}
        self._layout: str = "single"
        self._sheet_columns: int = 2
        self._sheet_rows: int = 5
        self._metadata: dict[str, Any] = {}

    def size(self, width_mm: float, height_mm: float) -> "TemplateBuilder":
        """
        Set label size in millimeters.

        Args:
            width_mm: Label width in millimeters
            height_mm: Label height in millimeters

        Returns:
            Self for chaining
        """
        self._label_width_mm = width_mm
        self._label_height_mm = height_mm
        return self

    def size_inches(self, width_inches: float, height_inches: float) -> "TemplateBuilder":
        """
        Set label size in inches.

        Args:
            width_inches: Label width in inches
            height_inches: Label height in inches

        Returns:
            Self for chaining
        """
        self._label_width_mm = width_inches * 25.4
        self._label_height_mm = height_inches * 25.4
        return self

    def dpi(self, dpi: int) -> "TemplateBuilder":
        """
        Set resolution in DPI.

        Args:
            dpi: Dots per inch

        Returns:
            Self for chaining
        """
        self._dpi = dpi
        return self

    def field(
        self,
        source_column: str,
        target_name: Optional[str] = None,
        required: bool = True,
        default: Optional[str] = None,
        transform: Optional[str] = None,
    ) -> "TemplateBuilder":
        """
        Add a field mapping.

        Args:
            source_column: Source column name in DataFrame
            target_name: Target field name (defaults to source_column)
            required: Is this field required?
            default: Default value if missing
            transform: Transform to apply

        Returns:
            Self for chaining
        """
        if target_name is None:
            target_name = source_column.lower().replace(" ", "_")

        field_mapping = FieldMapping(
            source_column=source_column,
            target_name=target_name,
            required=required,
            default=default,
            transform=transform,
        )

        self._fields.append(field_mapping)
        return self

    def barcode(
        self,
        field_name: str,
        barcode_type: str = "code128",
        format: str = "raster",
        dpi: int = 300,
        scale: float = 2.0,
        height: int = 50,
    ) -> "TemplateBuilder":
        """
        Add a barcode configuration.

        Args:
            field_name: Field name containing barcode data
            barcode_type: Barcode symbology
            format: Format: 'raster' or 'vector'
            dpi: Resolution for raster barcodes
            scale: Scale factor for vector barcodes
            height: Barcode height in modules

        Returns:
            Self for chaining
        """
        barcode_config = BarcodeConfig(
            field_name=field_name,
            barcode_type=barcode_type,
            format=format,
            dpi=dpi,
            scale=scale,
            height=height,
        )

        self._barcodes[field_name] = barcode_config
        return self

    def layout(
        self,
        layout_type: str = "single",
        columns: int = 2,
        rows: int = 5,
    ) -> "TemplateBuilder":
        """
        Set sheet layout configuration.

        Args:
            layout_type: Layout type: 'single', 'grid', 'roll'
            columns: Columns per sheet (for grid layout)
            rows: Rows per sheet (for grid layout)

        Returns:
            Self for chaining
        """
        self._layout = layout_type
        self._sheet_columns = columns
        self._sheet_rows = rows
        return self

    def metadata(self, key: str, value: Any) -> "TemplateBuilder":
        """
        Add custom metadata.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for chaining
        """
        self._metadata[key] = value
        return self

    def build(self) -> TemplateConfig:
        """
        Build the template configuration.

        Returns:
            TemplateConfig object

        Raises:
            ValueError: If required fields are missing
        """
        if self._label_width_mm is None or self._label_height_mm is None:
            raise ValueError("Label size must be set using .size() or .size_inches()")

        if not self._fields:
            raise ValueError("At least one field mapping must be added using .field()")

        return TemplateConfig(
            template_id=self.template_id,
            label_width_mm=self._label_width_mm,
            label_height_mm=self._label_height_mm,
            dpi=self._dpi,
            fields=self._fields,
            barcodes=self._barcodes,
            layout=self._layout,
            sheet_columns=self._sheet_columns,
            sheet_rows=self._sheet_rows,
            metadata=self._metadata,
        )


# ========================================================================
# TEMPLATE SERIALIZATION
# ========================================================================


def template_to_dict(template: TemplateConfig) -> dict[str, Any]:
    """
    Convert TemplateConfig to dictionary.

    Args:
        template: Template configuration

    Returns:
        Dictionary representation
    """
    return {
        "template_id": template.template_id,
        "label_width_mm": template.label_width_mm,
        "label_height_mm": template.label_height_mm,
        "dpi": template.dpi,
        "fields": [
            {
                "source_column": f.source_column,
                "target_name": f.target_name,
                "required": f.required,
                "default": f.default,
                "transform": f.transform,
            }
            for f in template.fields
        ],
        "barcodes": {
            name: {
                "field_name": bc.field_name,
                "barcode_type": bc.barcode_type,
                "format": bc.format,
                "dpi": bc.dpi,
                "scale": bc.scale,
                "height": bc.height,
            }
            for name, bc in template.barcodes.items()
        },
        "layout": template.layout,
        "sheet_columns": template.sheet_columns,
        "sheet_rows": template.sheet_rows,
        "metadata": template.metadata,
    }


def template_from_dict(data: dict[str, Any]) -> TemplateConfig:
    """
    Create TemplateConfig from dictionary.

    Args:
        data: Dictionary representation

    Returns:
        TemplateConfig object
    """
    fields = [FieldMapping(**f) for f in data.get("fields", [])]

    barcodes = {
        name: BarcodeConfig(**bc_data) for name, bc_data in data.get("barcodes", {}).items()
    }

    return TemplateConfig(
        template_id=data["template_id"],
        label_width_mm=data["label_width_mm"],
        label_height_mm=data["label_height_mm"],
        dpi=data.get("dpi", 300),
        fields=fields,
        barcodes=barcodes,
        layout=data.get("layout", "single"),
        sheet_columns=data.get("sheet_columns", 2),
        sheet_rows=data.get("sheet_rows", 5),
        metadata=data.get("metadata", {}),
    )


def save_template(template: TemplateConfig, filepath: str | Path) -> None:
    """
    Save template to JSON file.

    Args:
        template: Template configuration
        filepath: Path to save file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    template_dict = template_to_dict(template)

    with open(filepath, "w") as f:
        json.dump(template_dict, f, indent=2)


def load_template(filepath: str | Path) -> TemplateConfig:
    """
    Load template from JSON file.

    Args:
        filepath: Path to template file

    Returns:
        TemplateConfig object
    """
    with open(filepath) as f:
        data = json.load(f)

    return template_from_dict(data)


# Add convenience methods to TemplateConfig
TemplateConfig.to_dict = template_to_dict
TemplateConfig.from_dict = staticmethod(template_from_dict)
TemplateConfig.save_to_file = save_template
TemplateConfig.load_from_file = staticmethod(load_template)


# ========================================================================
# TEMPLATE REGISTRY
# ========================================================================


class TemplateRegistry:
    """Registry for storing and discovering templates."""

    def __init__(self, base_path: str | Path = ".vdp_templates"):
        """
        Initialize template registry.

        Args:
            base_path: Base directory for storing templates
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, template: TemplateConfig) -> Path:
        """
        Save template to registry.

        Args:
            template: Template to save

        Returns:
            Path to saved template
        """
        filepath = self.base_path / f"{template.template_id}.json"
        save_template(template, filepath)
        return filepath

    def load(self, template_id: str) -> TemplateConfig:
        """
        Load template from registry.

        Args:
            template_id: Template identifier

        Returns:
            TemplateConfig object

        Raises:
            FileNotFoundError: If template not found
        """
        filepath = self.base_path / f"{template_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Template '{template_id}' not found in registry")

        return load_template(filepath)

    def list_templates(self) -> list[str]:
        """
        List all templates in registry.

        Returns:
            List of template IDs
        """
        template_files = self.base_path.glob("*.json")
        return [f.stem for f in template_files]

    def exists(self, template_id: str) -> bool:
        """
        Check if template exists in registry.

        Args:
            template_id: Template identifier

        Returns:
            True if template exists
        """
        filepath = self.base_path / f"{template_id}.json"
        return filepath.exists()

    def delete(self, template_id: str) -> None:
        """
        Delete template from registry.

        Args:
            template_id: Template identifier
        """
        filepath = self.base_path / f"{template_id}.json"
        if filepath.exists():
            filepath.unlink()

    def get_template_info(self, template_id: str) -> dict[str, Any]:
        """
        Get template information without loading full template.

        Args:
            template_id: Template identifier

        Returns:
            Dictionary with template info
        """
        template = self.load(template_id)
        return {
            "template_id": template.template_id,
            "label_size": f"{template.label_width_mm}x{template.label_height_mm}mm",
            "dpi": template.dpi,
            "num_fields": len(template.fields),
            "num_barcodes": len(template.barcodes),
            "layout": template.layout,
        }


# Default global registry
_default_registry = TemplateRegistry()


def get_registry(base_path: Optional[str | Path] = None) -> TemplateRegistry:
    """
    Get template registry.

    Args:
        base_path: Optional custom base path

    Returns:
        TemplateRegistry instance
    """
    if base_path is None:
        return _default_registry
    return TemplateRegistry(base_path)


# ========================================================================
# TEMPLATE INTROSPECTION
# ========================================================================


def print_template_info(template: TemplateConfig) -> None:
    """
    Print detailed template information.

    Args:
        template: Template configuration
    """
    print(f"Template: {template.template_id}")
    print(f"  Size: {template.label_width_mm} x {template.label_height_mm} mm")
    print(f"  DPI: {template.dpi}")
    print(f"  Layout: {template.layout}")

    if template.layout == "grid":
        print(f"  Sheet: {template.sheet_columns} x {template.sheet_rows}")

    print(f"\n  Fields ({len(template.fields)}):")
    for field in template.fields:
        req = "required" if field.required else "optional"
        transform = f" → {field.transform}" if field.transform else ""
        print(f"    • {field.source_column} → {field.target_name} ({req}){transform}")

    if template.barcodes:
        print(f"\n  Barcodes ({len(template.barcodes)}):")
        for name, bc in template.barcodes.items():
            print(f"    • {bc.field_name}: {bc.barcode_type} ({bc.format})")

    if template.metadata:
        print(f"\n  Metadata:")
        for key, value in template.metadata.items():
            print(f"    • {key}: {value}")


def validate_template(template: TemplateConfig) -> list[str]:
    """
    Validate template configuration.

    Args:
        template: Template to validate

    Returns:
        List of validation warnings/errors
    """
    warnings = []

    # Check label size
    if template.label_width_mm <= 0 or template.label_height_mm <= 0:
        warnings.append("Invalid label size (must be positive)")

    # Check fields
    if not template.fields:
        warnings.append("No fields defined")

    # Check for duplicate target names
    target_names = [f.target_name for f in template.fields]
    duplicates = [name for name in set(target_names) if target_names.count(name) > 1]
    if duplicates:
        warnings.append(f"Duplicate target names: {duplicates}")

    # Check transforms exist
    available_transforms = list_transforms()
    for field in template.fields:
        if field.transform and field.transform not in available_transforms:
            warnings.append(f"Unknown transform '{field.transform}' in field '{field.source_column}'")

    # Check barcode references
    field_names = {f.target_name for f in template.fields}
    for name, bc in template.barcodes.items():
        if bc.field_name not in field_names:
            warnings.append(f"Barcode '{name}' references unknown field '{bc.field_name}'")

    return warnings


# ========================================================================
# QUICK BUILDERS (COMMON TEMPLATES)
# ========================================================================


def create_product_label_template(
    template_id: str = "product_label",
    include_barcode: bool = True,
) -> TemplateConfig:
    """
    Create a standard product label template.

    Args:
        template_id: Template identifier
        include_barcode: Include barcode field

    Returns:
        TemplateConfig
    """
    builder = (
        TemplateBuilder(template_id)
        .size(100, 150)
        .field("Article", "product_code", transform="trim")
        .field("Description", "product_name", transform="uppercase")
        .field("Batch", "batch_number")
        .field("Weight", "weight", transform="format_decimal_2", required=False)
        .field("MfgDate", "mfg_date", transform="date_yyyymmdd", required=False)
    )

    if include_barcode:
        builder.field("EAN", "barcode", transform="ean13_check_digit")
        builder.barcode("barcode", "ean13")

    return builder.build()


def create_shipping_label_template(
    template_id: str = "shipping_label",
) -> TemplateConfig:
    """
    Create a shipping label template.

    Args:
        template_id: Template identifier

    Returns:
        TemplateConfig
    """
    return (
        TemplateBuilder(template_id)
        .size(4 * 25.4, 6 * 25.4)  # 4x6 inches in mm
        .field("OrderID", "order_id")
        .field("Tracking", "tracking_number")
        .field("CustomerName", "customer_name")
        .field("Address", "address")
        .field("City", "city")
        .field("PostalCode", "postal_code")
        .field("Country", "country")
        .barcode("tracking_number", "code128")
        .build()
    )


def create_barcode_only_template(
    template_id: str = "barcode_only",
    barcode_type: str = "code128",
) -> TemplateConfig:
    """
    Create a barcode-only template.

    Args:
        template_id: Template identifier
        barcode_type: Barcode symbology

    Returns:
        TemplateConfig
    """
    return (
        TemplateBuilder(template_id)
        .size(50, 25)
        .field("Serial", "serial", transform="trim")
        .barcode("serial", barcode_type)
        .build()
    )
