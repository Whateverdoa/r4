"""Barcode generation utilities for VDP workflows."""

from io import BytesIO
from typing import Literal

import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image


BarcodeType = Literal[
    "code128",
    "code39",
    "ean13",
    "ean8",
    "gs1-128",
    "itf",
    "upca",
    "qr",
]


def generate_barcode(
    data: str,
    barcode_type: BarcodeType = "code128",
    dpi: int = 300,
    module_width: float = 0.2,
    module_height: float = 15.0,
    font_size: int = 10,
    text_distance: float = 5.0,
    quiet_zone: float = 6.5,
) -> bytes:
    """
    Generate a barcode image.

    Args:
        data: The data to encode in the barcode
        barcode_type: Type of barcode to generate
        dpi: Resolution in dots per inch
        module_width: Width of the narrowest bar in mm
        module_height: Height of the barcode in mm
        font_size: Font size for human-readable text
        text_distance: Distance between barcode and text in mm
        quiet_zone: Size of quiet zone in mm

    Returns:
        PNG image data as bytes
    """
    if barcode_type == "qr":
        return generate_qr_code(data, box_size=10, border=4)

    # Map friendly names to barcode library names
    barcode_map = {
        "code128": "code128",
        "code39": "code39",
        "ean13": "ean13",
        "ean8": "ean8",
        "gs1-128": "gs1_128",
        "itf": "itf",
        "upca": "upca",
    }

    barcode_class_name = barcode_map.get(barcode_type, "code128")
    barcode_class = barcode.get_barcode_class(barcode_class_name)

    # Create image writer with custom options
    writer = ImageWriter()
    writer.dpi = dpi
    writer.module_width = module_width
    writer.module_height = module_height
    writer.font_size = font_size
    writer.text_distance = text_distance
    writer.quiet_zone = quiet_zone

    # Generate barcode
    barcode_instance = barcode_class(data, writer=writer)

    # Render to bytes
    buffer = BytesIO()
    barcode_instance.write(buffer)
    buffer.seek(0)

    return buffer.read()


def generate_qr_code(
    data: str,
    version: int | None = None,
    error_correction: int = qrcode.constants.ERROR_CORRECT_L,
    box_size: int = 10,
    border: int = 4,
) -> bytes:
    """
    Generate a QR code.

    Args:
        data: Data to encode in QR code
        version: QR code version (1-40, None for auto)
        error_correction: Error correction level
        box_size: Size of each box in pixels
        border: Border size in boxes

    Returns:
        PNG image data as bytes
    """
    qr = qrcode.QRCode(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.read()


def generate_gs1_128(
    application_identifier: str,
    data: str,
    dpi: int = 300,
    **kwargs,
) -> bytes:
    """
    Generate a GS1-128 barcode with application identifier.

    Args:
        application_identifier: AI code (e.g., "01" for GTIN)
        data: The data to encode
        dpi: Resolution in dots per inch
        **kwargs: Additional arguments passed to generate_barcode

    Returns:
        PNG image data as bytes
    """
    # Format: (AI)data
    formatted_data = f"({application_identifier}){data}"
    return generate_barcode(formatted_data, barcode_type="gs1-128", dpi=dpi, **kwargs)


def batch_generate_barcodes(
    data_list: list[str],
    barcode_type: BarcodeType = "code128",
    **kwargs,
) -> list[bytes]:
    """
    Generate multiple barcodes in a batch.

    Args:
        data_list: List of data strings to encode
        barcode_type: Type of barcode to generate
        **kwargs: Additional arguments passed to generate_barcode

    Returns:
        List of PNG image data as bytes
    """
    return [generate_barcode(data, barcode_type, **kwargs) for data in data_list]


def barcode_to_pil_image(barcode_bytes: bytes) -> Image.Image:
    """
    Convert barcode bytes to PIL Image.

    Args:
        barcode_bytes: PNG image data as bytes

    Returns:
        PIL Image object
    """
    return Image.open(BytesIO(barcode_bytes))


def save_barcode(barcode_bytes: bytes, filepath: str) -> None:
    """
    Save barcode to file.

    Args:
        barcode_bytes: PNG image data as bytes
        filepath: Path to save the file
    """
    with open(filepath, "wb") as f:
        f.write(barcode_bytes)
