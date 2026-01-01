"""Advanced PDF assembly and sheet layout utilities."""

from typing import Any, Literal
from io import BytesIO

import fitz  # PyMuPDF
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas


SheetLayout = Literal["grid", "roll", "custom"]


def assemble_sheet_layout(
    label_pdfs: list[bytes],
    sheet_width: float = 8.5 * inch,
    sheet_height: float = 11 * inch,
    columns: int = 2,
    rows: int = 5,
    margin: float = 0.25 * inch,
    spacing: float = 0.1 * inch,
) -> bytes:
    """
    Assemble multiple labels into sheet layout (e.g., 2x5 on letter).

    Args:
        label_pdfs: List of individual label PDFs
        sheet_width: Sheet width
        sheet_height: Sheet height
        columns: Number of columns
        rows: Number of rows per sheet
        margin: Sheet margin
        spacing: Space between labels

    Returns:
        Multi-sheet PDF with labels in grid layout
    """
    labels_per_sheet = columns * rows
    num_sheets = (len(label_pdfs) + labels_per_sheet - 1) // labels_per_sheet

    output_pdf = fitz.open()

    # Calculate label dimensions
    available_width = sheet_width - (2 * margin) - ((columns - 1) * spacing)
    available_height = sheet_height - (2 * margin) - ((rows - 1) * spacing)
    label_width = available_width / columns
    label_height = available_height / rows

    for sheet_num in range(num_sheets):
        # Create new sheet
        sheet_page = output_pdf.new_page(width=sheet_width, height=sheet_height)

        # Add labels to sheet
        start_idx = sheet_num * labels_per_sheet
        end_idx = min(start_idx + labels_per_sheet, len(label_pdfs))

        for i, label_pdf_bytes in enumerate(label_pdfs[start_idx:end_idx]):
            col = i % columns
            row = i // columns

            # Calculate position
            x = margin + col * (label_width + spacing)
            y = margin + row * (label_height + spacing)

            # Insert label
            label_doc = fitz.open(stream=label_pdf_bytes, filetype="pdf")
            if label_doc.page_count > 0:
                label_page = label_doc[0]

                # Create a rectangle for the label position
                rect = fitz.Rect(x, y, x + label_width, y + label_height)

                # Insert the label page
                sheet_page.show_pdf_page(rect, label_doc, 0)

            label_doc.close()

    # Save to bytes
    output_buffer = BytesIO()
    output_pdf.save(output_buffer)
    output_pdf.close()
    output_buffer.seek(0)

    return output_buffer.read()


def assemble_roll_layout(
    label_pdfs: list[bytes],
    roll_width: float = 4 * inch,
    label_height: float = 6 * inch,
    gap: float = 0.125 * inch,
) -> bytes:
    """
    Assemble labels into continuous roll layout.

    Args:
        label_pdfs: List of individual label PDFs
        roll_width: Width of roll
        label_height: Height of each label
        gap: Gap between labels

    Returns:
        Single PDF with labels in vertical roll layout
    """
    total_height = len(label_pdfs) * (label_height + gap)

    output_pdf = fitz.open()
    roll_page = output_pdf.new_page(width=roll_width, height=total_height)

    current_y = 0

    for label_pdf_bytes in label_pdfs:
        label_doc = fitz.open(stream=label_pdf_bytes, filetype="pdf")

        if label_doc.page_count > 0:
            label_page = label_doc[0]

            rect = fitz.Rect(0, current_y, roll_width, current_y + label_height)
            roll_page.show_pdf_page(rect, label_doc, 0)

        label_doc.close()
        current_y += label_height + gap

    output_buffer = BytesIO()
    output_pdf.save(output_buffer)
    output_pdf.close()
    output_buffer.seek(0)

    return output_buffer.read()


def add_crop_marks(
    pdf_bytes: bytes,
    mark_length: float = 0.25 * inch,
    mark_offset: float = 0.125 * inch,
) -> bytes:
    """
    Add crop marks to a PDF.

    Args:
        pdf_bytes: Input PDF
        mark_length: Length of crop marks
        mark_offset: Distance from page edge

    Returns:
        PDF with crop marks
    """
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in pdf_doc:
        width = page.rect.width
        height = page.rect.height

        # Top-left corner
        page.draw_line(
            (mark_offset, mark_offset),
            (mark_offset + mark_length, mark_offset),
            color=(0, 0, 0),
            width=0.5,
        )
        page.draw_line(
            (mark_offset, mark_offset),
            (mark_offset, mark_offset + mark_length),
            color=(0, 0, 0),
            width=0.5,
        )

        # Top-right corner
        page.draw_line(
            (width - mark_offset, mark_offset),
            (width - mark_offset - mark_length, mark_offset),
            color=(0, 0, 0),
            width=0.5,
        )
        page.draw_line(
            (width - mark_offset, mark_offset),
            (width - mark_offset, mark_offset + mark_length),
            color=(0, 0, 0),
            width=0.5,
        )

        # Bottom-left corner
        page.draw_line(
            (mark_offset, height - mark_offset),
            (mark_offset + mark_length, height - mark_offset),
            color=(0, 0, 0),
            width=0.5,
        )
        page.draw_line(
            (mark_offset, height - mark_offset),
            (mark_offset, height - mark_offset - mark_length),
            color=(0, 0, 0),
            width=0.5,
        )

        # Bottom-right corner
        page.draw_line(
            (width - mark_offset, height - mark_offset),
            (width - mark_offset - mark_length, height - mark_offset),
            color=(0, 0, 0),
            width=0.5,
        )
        page.draw_line(
            (width - mark_offset, height - mark_offset),
            (width - mark_offset, height - mark_offset - mark_length),
            color=(0, 0, 0),
            width=0.5,
        )

    output_buffer = BytesIO()
    pdf_doc.save(output_buffer)
    pdf_doc.close()
    output_buffer.seek(0)

    return output_buffer.read()


def add_registration_marks(
    pdf_bytes: bytes,
    mark_size: float = 0.125 * inch,
) -> bytes:
    """
    Add registration marks to a PDF.

    Args:
        pdf_bytes: Input PDF
        mark_size: Size of registration marks

    Returns:
        PDF with registration marks
    """
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in pdf_doc:
        width = page.rect.width
        height = page.rect.height

        # Draw crosshair registration marks in corners
        positions = [
            (mark_size, mark_size),  # Top-left
            (width - mark_size, mark_size),  # Top-right
            (mark_size, height - mark_size),  # Bottom-left
            (width - mark_size, height - mark_size),  # Bottom-right
        ]

        for x, y in positions:
            # Horizontal line
            page.draw_line(
                (x - mark_size / 2, y),
                (x + mark_size / 2, y),
                color=(0, 0, 0),
                width=0.5,
            )
            # Vertical line
            page.draw_line(
                (x, y - mark_size / 2),
                (x, y + mark_size / 2),
                color=(0, 0, 0),
                width=0.5,
            )
            # Circle
            page.draw_circle((x, y), mark_size / 4, color=(0, 0, 0), width=0.5)

    output_buffer = BytesIO()
    pdf_doc.save(output_buffer)
    pdf_doc.close()
    output_buffer.seek(0)

    return output_buffer.read()


def interleave_pdfs(pdf_list_a: list[bytes], pdf_list_b: list[bytes]) -> bytes:
    """
    Interleave pages from two PDF lists (e.g., front/back for duplex).

    Args:
        pdf_list_a: First set of PDFs
        pdf_list_b: Second set of PDFs

    Returns:
        Interleaved PDF
    """
    output_pdf = fitz.open()

    max_len = max(len(pdf_list_a), len(pdf_list_b))

    for i in range(max_len):
        # Add page from list A
        if i < len(pdf_list_a):
            pdf_a = fitz.open(stream=pdf_list_a[i], filetype="pdf")
            if pdf_a.page_count > 0:
                output_pdf.insert_pdf(pdf_a)
            pdf_a.close()

        # Add page from list B
        if i < len(pdf_list_b):
            pdf_b = fitz.open(stream=pdf_list_b[i], filetype="pdf")
            if pdf_b.page_count > 0:
                output_pdf.insert_pdf(pdf_b)
            pdf_b.close()

    output_buffer = BytesIO()
    output_pdf.save(output_buffer)
    output_pdf.close()
    output_buffer.seek(0)

    return output_buffer.read()
