"""PDF processing utilities using PyMuPDF and ReportLab."""

from io import BytesIO
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas


def create_simple_pdf(
    content: dict[str, Any],
    pagesize: tuple[float, float] = letter,
) -> bytes:
    """
    Create a simple PDF using ReportLab.

    Args:
        content: Dictionary with PDF content (text, images, etc.)
        pagesize: Page size (default: letter)

    Returns:
        PDF data as bytes
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    # Draw text
    if "text" in content:
        c.setFont("Helvetica", 12)
        y_position = height - 50
        for line in content["text"]:
            c.drawString(50, y_position, line)
            y_position -= 20

    # Draw images
    if "images" in content:
        for img_data in content["images"]:
            c.drawImage(
                img_data["path"],
                img_data.get("x", 50),
                img_data.get("y", 500),
                width=img_data.get("width", 200),
                height=img_data.get("height", 200),
            )

    c.save()
    buffer.seek(0)
    return buffer.read()


def create_label_pdf(
    barcode_bytes: bytes,
    label_data: dict[str, Any],
    page_width: float = 4 * inch,
    page_height: float = 6 * inch,
) -> bytes:
    """
    Create a label PDF with barcode and text.

    Args:
        barcode_bytes: Barcode image as bytes
        label_data: Label content (title, fields, etc.)
        page_width: Label width
        page_height: Label height

    Returns:
        PDF data as bytes
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Title
    if "title" in label_data:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.25 * inch, page_height - 0.5 * inch, label_data["title"])

    # Fields
    if "fields" in label_data:
        c.setFont("Helvetica", 10)
        y_position = page_height - 1 * inch
        for field in label_data["fields"]:
            label = field.get("label", "")
            value = field.get("value", "")
            c.drawString(0.25 * inch, y_position, f"{label}: {value}")
            y_position -= 0.3 * inch

    # Barcode
    if barcode_bytes:
        barcode_img = Image.open(BytesIO(barcode_bytes))
        temp_path = "/tmp/temp_barcode.png"
        barcode_img.save(temp_path)

        c.drawImage(
            temp_path,
            0.25 * inch,
            0.5 * inch,
            width=3.5 * inch,
            height=1.5 * inch,
            preserveAspectRatio=True,
        )

    c.save()
    buffer.seek(0)
    return buffer.read()


def merge_pdfs(pdf_bytes_list: list[bytes]) -> bytes:
    """
    Merge multiple PDFs into a single PDF.

    Args:
        pdf_bytes_list: List of PDF data as bytes

    Returns:
        Merged PDF data as bytes
    """
    merged_pdf = fitz.open()

    for pdf_bytes in pdf_bytes_list:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        merged_pdf.insert_pdf(pdf_doc)
        pdf_doc.close()

    output_buffer = BytesIO()
    merged_pdf.save(output_buffer)
    merged_pdf.close()
    output_buffer.seek(0)

    return output_buffer.read()


def split_pdf(pdf_bytes: bytes, page_ranges: list[tuple[int, int]]) -> list[bytes]:
    """
    Split a PDF into multiple PDFs based on page ranges.

    Args:
        pdf_bytes: PDF data as bytes
        page_ranges: List of (start_page, end_page) tuples (0-indexed)

    Returns:
        List of PDF data as bytes
    """
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result = []

    for start, end in page_ranges:
        new_pdf = fitz.open()
        new_pdf.insert_pdf(pdf_doc, from_page=start, to_page=end)

        buffer = BytesIO()
        new_pdf.save(buffer)
        new_pdf.close()
        buffer.seek(0)
        result.append(buffer.read())

    pdf_doc.close()
    return result


def extract_pdf_metadata(pdf_bytes: bytes) -> dict[str, Any]:
    """
    Extract metadata from a PDF.

    Args:
        pdf_bytes: PDF data as bytes

    Returns:
        Dictionary with PDF metadata
    """
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    metadata = {
        "page_count": pdf_doc.page_count,
        "metadata": pdf_doc.metadata,
        "pages": [],
    }

    for page_num in range(pdf_doc.page_count):
        page = pdf_doc[page_num]
        metadata["pages"].append({
            "page_number": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "rotation": page.rotation,
        })

    pdf_doc.close()
    return metadata


def render_pdf_page_to_image(
    pdf_bytes: bytes,
    page_number: int = 0,
    dpi: int = 150,
) -> bytes:
    """
    Render a PDF page to a PNG image.

    Args:
        pdf_bytes: PDF data as bytes
        page_number: Page to render (0-indexed)
        dpi: Resolution in dots per inch

    Returns:
        PNG image data as bytes
    """
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = pdf_doc[page_number]

    # Calculate zoom factor from DPI
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")

    pdf_doc.close()
    return img_bytes


def validate_pdf(pdf_bytes: bytes) -> dict[str, Any]:
    """
    Validate a PDF and return diagnostics.

    Args:
        pdf_bytes: PDF data as bytes

    Returns:
        Dictionary with validation results
    """
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        validation = {
            "valid": True,
            "page_count": pdf_doc.page_count,
            "file_size": len(pdf_bytes),
            "is_encrypted": pdf_doc.is_encrypted,
            "is_pdf": pdf_doc.is_pdf,
            "errors": [],
        }

        # Check for common issues
        if pdf_doc.page_count == 0:
            validation["valid"] = False
            validation["errors"].append("PDF has no pages")

        pdf_doc.close()
        return validation

    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
        }


def optimize_pdf(pdf_bytes: bytes, compression: bool = True) -> bytes:
    """
    Optimize a PDF by compressing and cleaning.

    Args:
        pdf_bytes: PDF data as bytes
        compression: Whether to compress the PDF

    Returns:
        Optimized PDF data as bytes
    """
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    output_buffer = BytesIO()
    pdf_doc.save(
        output_buffer,
        garbage=4,  # Maximum garbage collection
        deflate=compression,
        clean=True,
    )
    pdf_doc.close()
    output_buffer.seek(0)

    return output_buffer.read()
