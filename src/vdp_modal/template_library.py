"""Pre-built template library for common use cases.

This module provides a collection of ready-to-use templates for common
VDP scenarios.

Usage:
    from vdp_modal.template_library import TEMPLATE_LIBRARY

    # Get a template
    template = TEMPLATE_LIBRARY["product_label_basic"]

    # Use with DataFrame
    batch = dataframe_to_vdp_batch(df, template, "job-001")
"""

from .template_builder import TemplateBuilder, TemplateConfig


# ========================================================================
# PRODUCT LABELS
# ========================================================================


def _product_label_basic() -> TemplateConfig:
    """Basic product label (100x150mm)."""
    return (
        TemplateBuilder("product_label_basic")
        .size(100, 150)
        .field("Article", "product_code", transform="trim")
        .field("Description", "product_name", transform="uppercase")
        .field("EAN", "barcode", transform="ean13_check_digit")
        .barcode("barcode", "ean13")
        .metadata("category", "product")
        .metadata("description", "Basic product label with EAN-13 barcode")
        .build()
    )


def _product_label_detailed() -> TemplateConfig:
    """Detailed product label with batch and weight info."""
    return (
        TemplateBuilder("product_label_detailed")
        .size(100, 150)
        .field("Article", "product_code", transform="trim")
        .field("Description", "product_name", transform="uppercase")
        .field("EAN", "barcode", transform="ean13_check_digit")
        .field("Batch", "batch_number")
        .field("Weight", "weight", transform="format_decimal_2", required=False)
        .field("MfgDate", "mfg_date", transform="date_yyyymmdd", required=False)
        .field("ExpDate", "exp_date", transform="date_yyyymmdd", required=False)
        .barcode("barcode", "ean13")
        .metadata("category", "product")
        .metadata("description", "Detailed product label with batch info")
        .build()
    )


# ========================================================================
# SHIPPING LABELS
# ========================================================================


def _shipping_label_4x6() -> TemplateConfig:
    """Standard 4x6 inch shipping label."""
    return (
        TemplateBuilder("shipping_label_4x6")
        .size_inches(4, 6)
        .field("OrderID", "order_id")
        .field("Tracking", "tracking_number")
        .field("CustomerName", "customer_name", transform="title")
        .field("Address1", "address_line1")
        .field("Address2", "address_line2", required=False, default="")
        .field("City", "city")
        .field("State", "state", transform="uppercase")
        .field("PostalCode", "postal_code")
        .field("Country", "country", transform="uppercase")
        .barcode("tracking_number", "code128")
        .metadata("category", "shipping")
        .metadata("description", "Standard 4x6 inch shipping label")
        .build()
    )


def _shipping_label_international() -> TemplateConfig:
    """International shipping label with customs info."""
    return (
        TemplateBuilder("shipping_label_international")
        .size_inches(4, 6)
        .field("OrderID", "order_id")
        .field("Tracking", "tracking_number")
        .field("CustomerName", "customer_name", transform="title")
        .field("Address", "address")
        .field("City", "city")
        .field("PostalCode", "postal_code")
        .field("Country", "country", transform="uppercase")
        .field("CustomsValue", "customs_value", transform="format_decimal_2", required=False)
        .field("CustomsDesc", "customs_description", required=False)
        .barcode("tracking_number", "code128")
        .metadata("category", "shipping")
        .metadata("description", "International shipping label with customs")
        .build()
    )


# ========================================================================
# WAREHOUSE / LOGISTICS
# ========================================================================


def _pallet_label() -> TemplateConfig:
    """Pallet label with SSCC-18 barcode."""
    return (
        TemplateBuilder("pallet_label")
        .size(150, 100)
        .field("SSCC", "sscc", transform="sscc18_from_base")
        .field("PalletID", "pallet_id")
        .field("Contents", "contents", transform="uppercase")
        .field("Quantity", "quantity")
        .field("Weight", "weight", transform="format_decimal_2")
        .field("Destination", "destination", transform="uppercase")
        .barcode("sscc", "gs1-128")
        .metadata("category", "warehouse")
        .metadata("description", "Pallet label with SSCC-18")
        .build()
    )


def _bin_location_label() -> TemplateConfig:
    """Warehouse bin location label."""
    return (
        TemplateBuilder("bin_location_label")
        .size(100, 50)
        .field("BinID", "bin_id", transform="uppercase")
        .field("Zone", "zone", transform="uppercase")
        .field("Aisle", "aisle")
        .field("Level", "level")
        .barcode("bin_id", "code128")
        .metadata("category", "warehouse")
        .metadata("description", "Warehouse bin location label")
        .build()
    )


# ========================================================================
# BARCODE ONLY
# ========================================================================


def _barcode_code128_only() -> TemplateConfig:
    """Simple Code 128 barcode label."""
    return (
        TemplateBuilder("barcode_code128_only")
        .size(50, 25)
        .field("Serial", "serial", transform="trim")
        .barcode("serial", "code128")
        .metadata("category", "barcode")
        .metadata("description", "Code 128 barcode only")
        .build()
    )


def _barcode_qr_only() -> TemplateConfig:
    """QR code only label."""
    return (
        TemplateBuilder("barcode_qr_only")
        .size(50, 50)
        .field("Data", "data")
        .barcode("data", "qr")
        .metadata("category", "barcode")
        .metadata("description", "QR code only")
        .build()
    )


def _barcode_gs1_128() -> TemplateConfig:
    """GS1-128 barcode with serial number."""
    return (
        TemplateBuilder("barcode_gs1_128")
        .size(75, 40)
        .field("Serial", "serial")
        .field("GTIN", "gtin", transform="gtin_check_digit", required=False)
        .barcode("serial", "gs1-128")
        .metadata("category", "barcode")
        .metadata("description", "GS1-128 barcode")
        .build()
    )


# ========================================================================
# RETAIL / PRICE TAGS
# ========================================================================


def _price_tag_basic() -> TemplateConfig:
    """Basic price tag."""
    return (
        TemplateBuilder("price_tag_basic")
        .size(50, 30)
        .field("Product", "product_name", transform="title")
        .field("SKU", "sku", transform="uppercase")
        .field("Price", "price", transform="format_decimal_2")
        .field("UPC", "barcode", transform="ean13_check_digit")
        .barcode("barcode", "ean13")
        .metadata("category", "retail")
        .metadata("description", "Basic price tag")
        .build()
    )


# ========================================================================
# ASSET TAGS
# ========================================================================


def _asset_tag() -> TemplateConfig:
    """IT asset tag."""
    return (
        TemplateBuilder("asset_tag")
        .size(75, 50)
        .field("AssetID", "asset_id", transform="uppercase")
        .field("Type", "asset_type", transform="title")
        .field("SerialNumber", "serial_number", transform="uppercase")
        .field("Owner", "owner", transform="title", required=False)
        .field("PurchaseDate", "purchase_date", transform="date_yyyymmdd", required=False)
        .barcode("asset_id", "code128")
        .metadata("category", "asset")
        .metadata("description", "IT asset tracking tag")
        .build()
    )


# ========================================================================
# PHARMACEUTICAL
# ========================================================================


def _pharma_label() -> TemplateConfig:
    """Pharmaceutical product label."""
    return (
        TemplateBuilder("pharma_label")
        .size(100, 60)
        .field("ProductName", "product_name", transform="uppercase")
        .field("NDC", "ndc_code")
        .field("LotNumber", "lot_number", transform="uppercase")
        .field("MfgDate", "mfg_date", transform="date_mmddyyyy")
        .field("ExpDate", "exp_date", transform="date_mmddyyyy")
        .field("Dosage", "dosage")
        .barcode("ndc_code", "datamatrix")
        .metadata("category", "pharmaceutical")
        .metadata("description", "Pharmaceutical product label")
        .build()
    )


# ========================================================================
# TEMPLATE LIBRARY (REGISTRY)
# ========================================================================


TEMPLATE_LIBRARY: dict[str, TemplateConfig] = {
    # Product labels
    "product_label_basic": _product_label_basic(),
    "product_label_detailed": _product_label_detailed(),
    # Shipping labels
    "shipping_label_4x6": _shipping_label_4x6(),
    "shipping_label_international": _shipping_label_international(),
    # Warehouse
    "pallet_label": _pallet_label(),
    "bin_location_label": _bin_location_label(),
    # Barcode only
    "barcode_code128_only": _barcode_code128_only(),
    "barcode_qr_only": _barcode_qr_only(),
    "barcode_gs1_128": _barcode_gs1_128(),
    # Retail
    "price_tag_basic": _price_tag_basic(),
    # Asset tracking
    "asset_tag": _asset_tag(),
    # Pharmaceutical
    "pharma_label": _pharma_label(),
}


def list_templates() -> list[str]:
    """Get list of available templates."""
    return sorted(TEMPLATE_LIBRARY.keys())


def get_template(template_id: str) -> TemplateConfig:
    """
    Get template from library.

    Args:
        template_id: Template identifier

    Returns:
        TemplateConfig object

    Raises:
        KeyError: If template not found
    """
    if template_id not in TEMPLATE_LIBRARY:
        available = ", ".join(list_templates())
        raise KeyError(f"Template '{template_id}' not found. Available: {available}")

    return TEMPLATE_LIBRARY[template_id]


def get_templates_by_category(category: str) -> dict[str, TemplateConfig]:
    """
    Get all templates in a category.

    Args:
        category: Category name (product, shipping, warehouse, etc.)

    Returns:
        Dictionary of template_id -> TemplateConfig
    """
    return {
        template_id: template
        for template_id, template in TEMPLATE_LIBRARY.items()
        if template.metadata.get("category") == category
    }


def print_library() -> None:
    """Print all templates in library."""
    categories = {}
    for template_id, template in TEMPLATE_LIBRARY.items():
        category = template.metadata.get("category", "other")
        if category not in categories:
            categories[category] = []
        categories[category].append((template_id, template))

    print("TEMPLATE LIBRARY")
    print("=" * 60)

    for category in sorted(categories.keys()):
        print(f"\n{category.upper()}:")
        for template_id, template in sorted(categories[category]):
            desc = template.metadata.get("description", "No description")
            size = f"{template.label_width_mm:.0f}x{template.label_height_mm:.0f}mm"
            print(f"  • {template_id:<30} {size:<15} {desc}")

    print(f"\nTotal: {len(TEMPLATE_LIBRARY)} templates")
