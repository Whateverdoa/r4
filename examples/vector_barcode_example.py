"""
Vector Barcode Generation - High-quality vector barcodes for print production.

This demonstrates:
- Generating SVG/EPS barcodes with zint
- Vector formats suitable for professional printing
- Integration with PDF workflows
- CMYK color management

Requirements:
- zint must be installed: apt-get install zint (Debian/Ubuntu)
- or brew install zint (macOS)

Run with: python examples/vector_barcode_example.py
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from vdp_modal.vector_barcode import (
    ZintBarcodeGenerator,
    generate_vector_barcode,
    is_zint_available,
    svg_to_pdf,
)


def main():
    """Generate vector barcodes in various formats."""

    print("=" * 60)
    print("VECTOR BARCODE GENERATION")
    print("=" * 60)

    # Check if zint is available
    if not is_zint_available():
        print("\n⚠️  WARNING: zint is not installed!")
        print("\nTo install zint:")
        print("  • Ubuntu/Debian: sudo apt-get install zint")
        print("  • macOS: brew install zint")
        print("  • Windows: Download from https://zint.org.uk/")
        print("\nThis example will exit.")
        return

    print("\n✓ zint is installed and available\n")

    generator = ZintBarcodeGenerator()

    # Example 1: SVG barcode
    print("[1/5] Generating SVG barcode (Code 128)...")
    svg_data = generator.generate(
        data="SVG-BARCODE-001",
        barcode_type="code128",
        output_format="svg",
        scale=2.0,
        height=50,
        border=10,
    )

    svg_path = "/tmp/barcode_code128.svg"
    with open(svg_path, "wb") as f:
        f.write(svg_data)

    print(f"  ✓ Saved: {svg_path} ({len(svg_data):,} bytes)")

    # Example 2: EPS barcode (for professional printing)
    print("\n[2/5] Generating EPS barcode (GS1-128)...")
    eps_data = generator.generate_gs1_128(
        application_identifier="01",
        data="12345678901234",
        output_format="eps",
        scale=2.5,
        height=60,
    )

    eps_path = "/tmp/barcode_gs1_128.eps"
    with open(eps_path, "wb") as f:
        f.write(eps_data)

    print(f"  ✓ Saved: {eps_path} ({len(eps_data):,} bytes)")

    # Example 3: Vector QR Code
    print("\n[3/5] Generating vector QR code...")
    qr_svg = generator.generate_qr_vector(
        data="https://modal.com/docs",
        output_format="svg",
        ecc_level="H",  # High error correction
    )

    qr_path = "/tmp/qr_code.svg"
    with open(qr_path, "wb") as f:
        f.write(qr_svg)

    print(f"  ✓ Saved: {qr_path} ({len(qr_svg):,} bytes)")

    # Example 4: DataMatrix (2D barcode for small items)
    print("\n[4/5] Generating DataMatrix barcode...")
    dm_svg = generator.generate(
        data="DM123456789",
        barcode_type="datamatrix",
        output_format="svg",
        scale=3.0,
    )

    dm_path = "/tmp/datamatrix.svg"
    with open(dm_path, "wb") as f:
        f.write(dm_svg)

    print(f"  ✓ Saved: {dm_path} ({len(dm_svg):,} bytes)")

    # Example 5: Convert SVG to PDF
    print("\n[5/5] Converting SVG to PDF...")

    try:
        pdf_data = svg_to_pdf(svg_data)

        pdf_path = "/tmp/barcode_code128.pdf"
        with open(pdf_path, "wb") as f:
            f.write(pdf_data)

        print(f"  ✓ Saved: {pdf_path} ({len(pdf_data):,} bytes)")

    except ImportError:
        print("  ⚠️  svglib not installed (pip install svglib)")

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)

    print("\nGenerated Files:")
    print(f"  • {svg_path}")
    print(f"  • {eps_path}")
    print(f"  • {qr_path}")
    print(f"  • {dm_path}")

    if os.path.exists("/tmp/barcode_code128.pdf"):
        print(f"  • /tmp/barcode_code128.pdf")

    print("\n" + "=" * 60)
    print("VECTOR BARCODE BENEFITS")
    print("=" * 60)
    print("""
✓ Scalable to any size without quality loss
✓ Perfect for professional printing
✓ Small file sizes
✓ Editable in design software (Illustrator, InDesign)
✓ CMYK color support
✓ Compatible with prepress workflows

Supported formats:
  • SVG: Best for web and modern workflows
  • EPS: Best for professional print production
  • PDF: Universal format
  • EMF: Windows Enhanced Metafile
    """)

    print("\n" + "=" * 60)
    print("RECOMMENDED USE CASES")
    print("=" * 60)
    print("""
• Product packaging (high-resolution printing)
• Labels for pharmaceutical/medical products
• Automotive parts labeling
• Food packaging (GS1 barcodes)
• Any application requiring crisp, scalable barcodes

For Modal integration, use the 'vector_barcode_image' in app.py
    """)

    print("\n✓✓✓ Success! ✓✓✓\n")


if __name__ == "__main__":
    main()
