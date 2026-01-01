"""Custom Modal images with prepress tools installed.

This module defines various Modal container images with different
tool combinations for different use cases.
"""

import modal


# Base image with Python dependencies only
base_image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "python-barcode>=0.15.0",
    "qrcode[pil]>=7.4.0",
    "PyMuPDF>=1.24.0",
    "reportlab>=4.0.0",
    "Pillow>=10.0.0",
    "boto3>=1.34.0",
    "pydantic>=2.0.0",
)


# Image with zint for vector barcodes
vector_barcode_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "zint",  # Vector barcode generation
        "libzint2.11",  # Zint library
    )
    .pip_install(
        "python-barcode>=0.15.0",
        "qrcode[pil]>=7.4.0",
        "PyMuPDF>=1.24.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "boto3>=1.34.0",
        "pydantic>=2.0.0",
        "svglib>=1.5.0",  # SVG to PDF conversion
    )
)


# Image with Ghostscript for advanced PDF operations
ghostscript_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "ghostscript",  # Advanced PDF processing
    )
    .pip_install(
        "python-barcode>=0.15.0",
        "qrcode[pil]>=7.4.0",
        "PyMuPDF>=1.24.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "boto3>=1.34.0",
        "pydantic>=2.0.0",
    )
)


# Full prepress image with all tools
prepress_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        # Vector barcodes
        "zint",
        "libzint2.11",
        # PDF processing
        "ghostscript",
        # Image processing
        "imagemagick",
        "libmagickwand-dev",
        # Fonts for professional output
        "fonts-liberation",
        "fonts-dejavu-core",
        "gsfonts",
    )
    .pip_install(
        "python-barcode>=0.15.0",
        "qrcode[pil]>=7.4.0",
        "PyMuPDF>=1.24.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "boto3>=1.34.0",
        "pydantic>=2.0.0",
        "svglib>=1.5.0",
        "Wand>=0.6.0",  # ImageMagick Python binding
    )
)


# Lightweight image for barcode-only jobs
barcode_only_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("zint", "libzint2.11")
    .pip_install(
        "python-barcode>=0.15.0",
        "qrcode[pil]>=7.4.0",
        "Pillow>=10.0.0",
        "svglib>=1.5.0",
    )
)


# Image with color management for CMYK printing
color_managed_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "ghostscript",
        "liblcms2-2",  # Color management
        "icc-profiles-free",  # ICC color profiles
    )
    .pip_install(
        "PyMuPDF>=1.24.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "boto3>=1.34.0",
        "pydantic>=2.0.0",
    )
)


def get_image(name: str = "base") -> modal.Image:
    """
    Get Modal image by name.

    Args:
        name: Image name
            - "base": Basic dependencies only
            - "vector": With zint for vector barcodes
            - "ghostscript": With Ghostscript for PDF processing
            - "prepress": Full prepress tools (recommended for production)
            - "barcode": Lightweight barcode-only
            - "color": Color-managed for CMYK printing

    Returns:
        Modal Image object
    """
    images = {
        "base": base_image,
        "vector": vector_barcode_image,
        "ghostscript": ghostscript_image,
        "prepress": prepress_image,
        "barcode": barcode_only_image,
        "color": color_managed_image,
    }

    return images.get(name, base_image)


# Export commonly used images
__all__ = [
    "base_image",
    "vector_barcode_image",
    "ghostscript_image",
    "prepress_image",
    "barcode_only_image",
    "color_managed_image",
    "get_image",
]
