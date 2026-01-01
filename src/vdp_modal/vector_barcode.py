"""Vector barcode generation using zint and advanced PDF operations with Ghostscript.

This module provides high-quality vector barcode generation suitable for
professional printing and prepress workflows.
"""

import subprocess
from pathlib import Path
from typing import Literal
import tempfile
import os


VectorFormat = Literal["svg", "eps", "emf", "pdf"]


class ZintBarcodeGenerator:
    """
    Generate vector barcodes using zint library.

    Zint supports 50+ barcode types and outputs vector formats suitable
    for professional printing.
    """

    # Zint barcode type mappings
    BARCODE_TYPES = {
        # Common 1D barcodes
        "code128": 20,
        "code39": 8,
        "code93": 25,
        "ean13": 13,
        "ean8": 14,
        "upca": 34,
        "upce": 37,
        "itf": 89,
        "gs1-128": 16,
        "codabar": 18,
        # 2D barcodes
        "qr": 58,
        "datamatrix": 71,
        "pdf417": 55,
        "aztec": 92,
        "maxicode": 57,
        # Postal codes
        "postnet": 40,
        "royalmail": 26,
        "auspost": 63,
        # GS1 barcodes
        "gs1-datamatrix": 102,
        "gs1-qr": 104,
        # Pharmaceutical
        "pharmacode": 51,
        "pzn": 52,
    }

    def __init__(self, zint_path: str = "zint"):
        """
        Initialize zint generator.

        Args:
            zint_path: Path to zint executable (default: "zint" from PATH)
        """
        self.zint_path = zint_path
        self._check_zint_available()

    def _check_zint_available(self) -> bool:
        """Check if zint is installed and available."""
        try:
            result = subprocess.run(
                [self.zint_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def generate(
        self,
        data: str,
        barcode_type: str = "code128",
        output_format: VectorFormat = "svg",
        scale: float = 1.0,
        border: int = 10,
        height: int = 50,
        human_readable: bool = True,
    ) -> bytes:
        """
        Generate vector barcode.

        Args:
            data: Data to encode
            barcode_type: Barcode symbology
            output_format: Output format (svg, eps, emf, pdf)
            scale: Scale factor
            border: Border/quiet zone width
            height: Barcode height in modules
            human_readable: Show human-readable text

        Returns:
            Vector barcode as bytes
        """
        # Get zint barcode type code
        barcode_code = self.BARCODE_TYPES.get(barcode_type.lower(), 20)

        # Create temporary file for output
        with tempfile.NamedTemporaryFile(
            suffix=f".{output_format}",
            delete=False,
        ) as tmp_file:
            output_path = tmp_file.name

        try:
            # Build zint command
            cmd = [
                self.zint_path,
                "-b", str(barcode_code),
                "-d", data,
                "--scale", str(scale),
                "--border", str(border),
                "--height", str(height),
                "-o", output_path,
            ]

            # Add format-specific options
            if output_format == "svg":
                cmd.append("--svg")
            elif output_format == "eps":
                cmd.append("--eps")
            elif output_format == "emf":
                cmd.append("--emf")

            # Human readable text
            if not human_readable:
                cmd.append("--notext")

            # Run zint
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"zint failed: {result.stderr}")

            # Read generated file
            with open(output_path, "rb") as f:
                vector_data = f.read()

            return vector_data

        finally:
            # Cleanup temp file
            if os.path.exists(output_path):
                os.unlink(output_path)

    def generate_gs1_128(
        self,
        application_identifier: str,
        data: str,
        output_format: VectorFormat = "svg",
        **kwargs,
    ) -> bytes:
        """
        Generate GS1-128 vector barcode.

        Args:
            application_identifier: AI code (e.g., "01" for GTIN)
            data: Data to encode
            output_format: Output format
            **kwargs: Additional arguments for generate()

        Returns:
            Vector barcode as bytes
        """
        formatted_data = f"({application_identifier}){data}"
        return self.generate(
            formatted_data,
            barcode_type="gs1-128",
            output_format=output_format,
            **kwargs,
        )

    def generate_qr_vector(
        self,
        data: str,
        output_format: VectorFormat = "svg",
        version: int = 0,  # 0 = auto
        ecc_level: Literal["L", "M", "Q", "H"] = "M",
        **kwargs,
    ) -> bytes:
        """
        Generate QR code as vector.

        Args:
            data: Data to encode
            output_format: Output format
            version: QR version (0 = auto, 1-40)
            ecc_level: Error correction level
            **kwargs: Additional arguments for generate()

        Returns:
            Vector QR code as bytes
        """
        # Map ECC levels to zint options
        ecc_map = {"L": 1, "M": 2, "Q": 3, "H": 4}
        ecc_value = ecc_map.get(ecc_level, 2)

        # Note: zint uses --vers for QR version and --secure for ECC
        # We'll use the basic generate for now and extend if needed

        return self.generate(
            data,
            barcode_type="qr",
            output_format=output_format,
            **kwargs,
        )


class GhostscriptProcessor:
    """
    Advanced PDF operations using Ghostscript.

    Provides high-quality PDF processing, color management,
    and prepress optimization.
    """

    def __init__(self, gs_path: str = "gs"):
        """
        Initialize Ghostscript processor.

        Args:
            gs_path: Path to gs executable
        """
        self.gs_path = gs_path

    def embed_barcode_in_pdf(
        self,
        pdf_bytes: bytes,
        barcode_svg: bytes,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> bytes:
        """
        Embed vector barcode into PDF.

        Args:
            pdf_bytes: Input PDF
            barcode_svg: Vector barcode (SVG)
            x, y: Position in points
            width, height: Size in points

        Returns:
            PDF with embedded vector barcode
        """
        # This is a simplified version
        # In production, you'd use reportlab or PyMuPDF to embed SVG
        # Ghostscript is better for post-processing

        # For now, return original PDF
        # TODO: Implement SVG embedding using reportlab's svglib
        return pdf_bytes

    def optimize_for_print(
        self,
        pdf_bytes: bytes,
        color_profile: Literal["CMYK", "RGB", "Grayscale"] = "CMYK",
        resolution: int = 300,
    ) -> bytes:
        """
        Optimize PDF for professional printing.

        Args:
            pdf_bytes: Input PDF
            color_profile: Color space
            resolution: DPI for images

        Returns:
            Optimized PDF
        """
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as input_file:
            input_file.write(pdf_bytes)
            input_path = input_file.name

        output_path = input_path.replace(".pdf", "_optimized.pdf")

        try:
            cmd = [
                self.gs_path,
                "-dNOPAUSE",
                "-dBATCH",
                "-dSAFER",
                "-sDEVICE=pdfwrite",
                f"-r{resolution}",
                f"-sOutputFile={output_path}",
            ]

            # Color conversion
            if color_profile == "CMYK":
                cmd.extend([
                    "-sColorConversionStrategy=CMYK",
                    "-dProcessColorModel=/DeviceCMYK",
                ])
            elif color_profile == "Grayscale":
                cmd.extend([
                    "-sColorConversionStrategy=Gray",
                    "-dProcessColorModel=/DeviceGray",
                ])

            cmd.append(input_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Ghostscript failed: {result.stderr}")

            with open(output_path, "rb") as f:
                optimized_pdf = f.read()

            return optimized_pdf

        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def convert_to_pdf_x(
        self,
        pdf_bytes: bytes,
        pdf_x_version: Literal["PDF/X-1a", "PDF/X-3", "PDF/X-4"] = "PDF/X-3",
    ) -> bytes:
        """
        Convert PDF to PDF/X standard for print production.

        Args:
            pdf_bytes: Input PDF
            pdf_x_version: PDF/X standard version

        Returns:
            PDF/X compliant PDF
        """
        # PDF/X conversion requires specific ICC profiles and settings
        # This is a placeholder for the actual implementation
        return self.optimize_for_print(pdf_bytes, color_profile="CMYK")


def generate_vector_barcode(
    data: str,
    barcode_type: str = "code128",
    output_format: VectorFormat = "svg",
    **kwargs,
) -> bytes:
    """
    Convenience function to generate vector barcode.

    Args:
        data: Data to encode
        barcode_type: Barcode symbology
        output_format: Output format (svg, eps, emf, pdf)
        **kwargs: Additional arguments

    Returns:
        Vector barcode as bytes
    """
    generator = ZintBarcodeGenerator()
    return generator.generate(data, barcode_type, output_format, **kwargs)


def svg_to_pdf(svg_bytes: bytes) -> bytes:
    """
    Convert SVG barcode to PDF.

    Args:
        svg_bytes: SVG data

    Returns:
        PDF data
    """
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPDF
        from io import BytesIO

        # Parse SVG
        drawing = svg2rlg(BytesIO(svg_bytes))

        # Render to PDF
        pdf_buffer = BytesIO()
        renderPDF.drawToFile(drawing, pdf_buffer)
        pdf_buffer.seek(0)

        return pdf_buffer.read()

    except ImportError:
        raise ImportError(
            "svglib required for SVG to PDF conversion. "
            "Install with: pip install svglib"
        )


def is_zint_available() -> bool:
    """Check if zint is installed."""
    try:
        result = subprocess.run(
            ["zint", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_ghostscript_available() -> bool:
    """Check if Ghostscript is installed."""
    try:
        result = subprocess.run(
            ["gs", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
