# Vector Barcodes Guide

Professional vector barcode generation for print production and prepress workflows.

## Overview

Vector barcodes are resolution-independent graphics suitable for professional printing. Unlike raster barcodes (PNG, JPG), vector barcodes:

- **Scale infinitely** without quality loss
- **Print perfectly** at any size
- **Smaller file sizes** for the same quality
- **Editable** in design software
- **CMYK compatible** for professional printing

## Why Vector Barcodes?

### Raster vs Vector Comparison

| Feature | Raster (PNG) | Vector (SVG/EPS) |
|---------|--------------|------------------|
| **Resolution** | Fixed (300 DPI) | Infinite |
| **File Size** | Large | Small |
| **Scaling** | Loses quality | Perfect at any size |
| **Editing** | Pixel-based | Object-based |
| **Printing** | May show artifacts | Always crisp |
| **Color** | RGB/CMYK | True CMYK |

### When to Use Vector Barcodes

✓ **Professional printing** (packaging, labels)
✓ **Large format** (posters, banners)
✓ **Variable sizes** (same artwork at multiple sizes)
✓ **Prepress workflows** (Adobe InDesign, Illustrator)
✓ **CMYK color requirements**
✓ **Long-term archival** (smaller files)

## Installation

### System Requirements

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y zint libzint2.11 ghostscript
```

**macOS:**
```bash
brew install zint ghostscript
```

**Windows:**
- Download zint from [zint.org.uk](https://zint.org.uk/)
- Download Ghostscript from [ghostscript.com](https://www.ghostscript.com/)

### Python Dependencies

```bash
# For SVG to PDF conversion
pip install svglib

# For full vector support
pip install modal-vdp[vector]
```

## Usage

### Basic Vector Barcode Generation

```python
from vdp_modal.vector_barcode import ZintBarcodeGenerator

generator = ZintBarcodeGenerator()

# Generate SVG barcode
svg_data = generator.generate(
    data="PRODUCT-12345",
    barcode_type="code128",
    output_format="svg",
    scale=2.0,
    height=50,
    border=10,
)

# Save to file
with open("barcode.svg", "wb") as f:
    f.write(svg_data)
```

### Supported Formats

```python
# SVG - Best for modern workflows
svg = generator.generate(data, output_format="svg")

# EPS - Best for professional print
eps = generator.generate(data, output_format="eps")

# PDF - Universal format
pdf = generator.generate(data, output_format="pdf")

# EMF - Windows Enhanced Metafile
emf = generator.generate(data, output_format="emf")
```

### Supported Barcode Types

```python
# Common 1D barcodes
generator.generate(data, barcode_type="code128")
generator.generate(data, barcode_type="code39")
generator.generate(data, barcode_type="ean13")
generator.generate(data, barcode_type="upca")
generator.generate(data, barcode_type="gs1-128")

# 2D barcodes
generator.generate_qr_vector(data, output_format="svg")
generator.generate(data, barcode_type="datamatrix")
generator.generate(data, barcode_type="pdf417")
generator.generate(data, barcode_type="aztec")

# Postal codes
generator.generate(data, barcode_type="postnet")
generator.generate(data, barcode_type="royalmail")

# Pharmaceutical
generator.generate(data, barcode_type="pharmacode")
```

### GS1-128 Barcodes

For GS1 application identifiers:

```python
# GS1-128 with GTIN
eps_data = generator.generate_gs1_128(
    application_identifier="01",
    data="12345678901234",
    output_format="eps",
    scale=2.5,
    height=60,
)
```

### QR Codes with Error Correction

```python
qr_svg = generator.generate_qr_vector(
    data="https://example.com",
    output_format="svg",
    ecc_level="H",  # High error correction (L, M, Q, H)
)
```

## Modal Integration

### Using Vector Barcodes in Modal

```python
import modal
from vdp_modal.images import vector_barcode_image

app = modal.App("vector-vdp")

@app.function(image=vector_barcode_image)
def generate_vector_label(serial: str) -> bytes:
    """Generate label with vector barcode."""
    from vdp_modal.vector_barcode import ZintBarcodeGenerator
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO

    # Generate vector barcode
    generator = ZintBarcodeGenerator()
    barcode_svg = generator.generate(
        serial,
        barcode_type="code128",
        output_format="svg",
    )

    # Create PDF with vector barcode
    # (Implementation using svglib)

    return pdf_bytes
```

### Custom Modal Image

Create a custom Modal image with all prepress tools:

```python
from vdp_modal.images import prepress_image

app = modal.App("prepress-workflow")

@app.function(image=prepress_image)
def advanced_prepress(pdf_bytes: bytes) -> bytes:
    """Full prepress workflow with vector barcodes."""
    from vdp_modal.vector_barcode import ZintBarcodeGenerator
    from vdp_modal.vector_barcode import GhostscriptProcessor

    # Generate vector barcodes
    generator = ZintBarcodeGenerator()

    # Process with Ghostscript
    gs = GhostscriptProcessor()
    optimized_pdf = gs.optimize_for_print(
        pdf_bytes,
        color_profile="CMYK",
        resolution=300,
    )

    return optimized_pdf
```

## Ghostscript Operations

### PDF Optimization for Print

```python
from vdp_modal.vector_barcode import GhostscriptProcessor

gs = GhostscriptProcessor()

# Optimize for CMYK printing
optimized = gs.optimize_for_print(
    pdf_bytes,
    color_profile="CMYK",
    resolution=300,
)

# Convert to grayscale
grayscale = gs.optimize_for_print(
    pdf_bytes,
    color_profile="Grayscale",
    resolution=300,
)
```

### PDF/X Conversion

For professional print shops:

```python
# Convert to PDF/X-3 (CMYK with ICC profiles)
pdfx = gs.convert_to_pdf_x(
    pdf_bytes,
    pdf_x_version="PDF/X-3",
)
```

## Prepress Workflows

### Complete Prepress Pipeline

```python
from vdp_modal.vector_barcode import (
    ZintBarcodeGenerator,
    GhostscriptProcessor,
    svg_to_pdf,
)

def prepress_workflow(data: str) -> bytes:
    """Complete prepress workflow."""

    # 1. Generate vector barcode
    generator = ZintBarcodeGenerator()
    barcode_eps = generator.generate(
        data,
        barcode_type="gs1-128",
        output_format="eps",
        scale=3.0,
        height=60,
    )

    # 2. Convert to PDF
    barcode_pdf = svg_to_pdf(barcode_eps)

    # 3. Embed in label design
    # (Use ReportLab or PyMuPDF)

    # 4. Optimize for print
    gs = GhostscriptProcessor()
    final_pdf = gs.optimize_for_print(
        label_pdf,
        color_profile="CMYK",
        resolution=300,
    )

    # 5. Convert to PDF/X
    pdfx = gs.convert_to_pdf_x(final_pdf)

    return pdfx
```

### Color Management

```python
# Use color-managed Modal image
from vdp_modal.images import color_managed_image

@app.function(image=color_managed_image)
def color_managed_output(pdf_bytes: bytes) -> bytes:
    """Generate color-managed PDF with ICC profiles."""

    gs = GhostscriptProcessor()

    return gs.optimize_for_print(
        pdf_bytes,
        color_profile="CMYK",
        resolution=300,
    )
```

## File Size Comparison

Example barcode "PRODUCT-123456789":

| Format | Raster (PNG, 300 DPI) | Vector (SVG) | Vector (EPS) |
|--------|----------------------|--------------|--------------|
| File Size | ~15 KB | ~2 KB | ~3 KB |
| Quality at 2x | Blurry | Perfect | Perfect |
| Quality at 10x | Very blurry | Perfect | Perfect |
| Editable | No | Yes | Yes |

## Best Practices

### For Professional Printing

1. **Use EPS format** for Adobe workflows
2. **Enable CMYK color** for print production
3. **Set appropriate DPI** (300+ for printing)
4. **Include bleed and crop marks**
5. **Convert to PDF/X** before sending to print shop

```python
# Recommended for professional printing
eps_data = generator.generate(
    data,
    barcode_type="gs1-128",
    output_format="eps",
    scale=3.0,
    height=60,
    border=12,
)
```

### For Digital/Web Use

1. **Use SVG format** for web displays
2. **Smaller scale** to reduce file size
3. **Consider PNG** if browser compatibility is an issue

```python
# Recommended for web/digital
svg_data = generator.generate(
    data,
    barcode_type="qr",
    output_format="svg",
    scale=1.5,
    border=4,
)
```

### For Variable Data Printing (VDP)

1. **Pre-generate vector barcodes** in parallel
2. **Embed in PDF templates** using ReportLab
3. **Optimize final PDF** with Ghostscript
4. **Archive in vector format** for reuse

## Troubleshooting

### zint Not Found

```bash
# Check if zint is installed
which zint

# Install on Ubuntu/Debian
sudo apt-get install zint

# Install on macOS
brew install zint
```

### Ghostscript Not Found

```bash
# Check if Ghostscript is installed
which gs

# Install on Ubuntu/Debian
sudo apt-get install ghostscript

# Install on macOS
brew install ghostscript
```

### SVG to PDF Conversion Fails

```bash
# Install svglib
pip install svglib reportlab
```

### Modal Container Missing Tools

Use the appropriate Modal image:

```python
from vdp_modal.images import (
    vector_barcode_image,  # Has zint
    ghostscript_image,      # Has Ghostscript
    prepress_image,         # Has everything
)

@app.function(image=prepress_image)
def my_function():
    # Now zint and gs are available
    pass
```

## Examples

See the `examples/` directory:

- `vector_barcode_example.py` - Generate vector barcodes
- Full Modal integration examples coming soon

## References

- [Zint Documentation](https://zint.org.uk/)
- [Ghostscript Documentation](https://www.ghostscript.com/doc/)
- [PDF/X Standards](https://en.wikipedia.org/wiki/PDF/X)
- [GS1 Barcode Standards](https://www.gs1.org/)

---

For more information, see:
- [Modal Documentation](https://modal.com/docs)
- [ReportLab User Guide](https://www.reportlab.com/docs/)
