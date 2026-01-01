# Quick Start Guide

Get started with Modal VDP in 5 minutes.

## Prerequisites

1. **Python 3.11+** installed
2. **Modal account** - Sign up at [modal.com](https://modal.com)
3. **AWS credentials** (optional, for S3 upload)

## Installation

```bash
# 1. Install Modal CLI
pip install modal

# 2. Authenticate with Modal
modal setup

# 3. Clone and install this project
pip install -e .
```

## Your First VDP Job

### Option 1: Run Built-in Example

```bash
# Generate 100 labels with barcodes
modal run examples/simple_vdp.py
```

This will:
- Create 100 product labels with barcodes
- Process them in parallel chunks
- Save the output PDF to `/tmp/simple-vdp-100.pdf`

### Option 2: Use the Main App

```bash
# Generate custom number of labels
modal run src/vdp_modal/app.py --num-records 1000 --chunk-size 100
```

### Option 3: Python API

```python
import modal
from vdp_modal import vdp_app
from vdp_modal.app import run_vdp_pipeline

# Your data
records = [
    {
        "serial": f"SN-{i:06d}",
        "product": f"Product-{i}",
        "date": "2026-01-01",
    }
    for i in range(1000)
]

# Template
template = {
    "title": "My Label",
    "barcode_type": "code128",
}

# Run the pipeline
with modal.runner.deploy_app(vdp_app):
    result = run_vdp_pipeline.remote(
        records=records,
        template=template,
        job_id="my-job-001",
        chunk_size=100,
    )

    # Save output
    with open("output.pdf", "wb") as f:
        f.write(result["pdf_bytes"])

    print(f"Generated {result['total_records']} labels!")
```

## Examples

### 1. Simple VDP (100-1000 labels)

```bash
modal run examples/simple_vdp.py
```

### 2. Barcode Batch (10,000 barcodes)

```bash
modal run examples/barcode_batch.py
```

### 3. Full Pipeline (4000 labels + S3)

```bash
# Set AWS credentials first
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export VDP_S3_BUCKET="your-bucket"

modal run examples/full_pipeline.py
```

### 4. Sheet Layout (Print-ready)

```bash
modal run examples/sheet_layout.py
```

## How It Works

### Architecture

```
Your Data (CSV/JSON/List)
    ↓
Split into Chunks (e.g., 1000 → 10 chunks of 100)
    ↓
Modal Parallel Workers (10 workers process simultaneously)
│   ├── Worker 1: Generate barcodes + PDFs for chunk 1
│   ├── Worker 2: Generate barcodes + PDFs for chunk 2
│   └── ...
    ↓
Assemble Final PDF (Merge all chunks)
    ↓
Upload to S3 (Optional)
    ↓
Done!
```

### Scaling

Modal automatically scales based on your workload:

- **40 workers**: Small job (100 records, chunk_size=10)
- **100 workers**: Medium job (1,000 records, chunk_size=10)
- **1000 workers**: Large job (10,000 records, chunk_size=10)
- **4000 workers**: Massive job (40,000 records, chunk_size=10)

No infrastructure setup required!

## Configuration

### Barcode Types

Supported barcode types:
- `code128` - Most common
- `code39`
- `ean13`, `ean8`
- `gs1-128` - For GS1 data
- `upca`
- `qr` - QR codes

### Template Structure

```python
template = {
    "title": "Product Label",          # Label title
    "barcode_type": "code128",         # Barcode format
    "required_fields": ["serial"],     # Required data fields
}
```

### Record Structure

```python
record = {
    "serial": "SN-123456",        # Required: for barcode
    "product": "Widget A",        # Optional: product name
    "batch": "BATCH-001",         # Optional: batch number
    "date": "2026-01-01",         # Optional: date
    # ... any custom fields
}
```

## Performance Tips

1. **Optimal Chunk Size**: 50-200 records per chunk
   - Too small: overhead from too many workers
   - Too large: slower individual processing

2. **CPU Allocation**: Adjust in `app.py`
   ```python
   @app.function(cpu=4, memory=4096)  # 4 CPUs, 4GB RAM
   ```

3. **Parallel Processing**: Modal automatically parallelizes `.map()` calls

## Troubleshooting

### Issue: "Modal not authenticated"
```bash
modal setup
```

### Issue: "No module named 'vdp_modal'"
```bash
pip install -e .
```

### Issue: S3 upload fails
```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

### Issue: Out of memory
Reduce chunk size or increase memory in `app.py`:
```python
@app.function(memory=8192)  # Increase to 8GB
```

## Next Steps

- **Read the README** for detailed architecture
- **Explore examples/** for more use cases
- **Customize templates** in your own code
- **Add GPU functions** for AI agents (OCR, vision models)
- **Set up webhooks** for real-time processing

## Support

- [Modal Documentation](https://modal.com/docs)
- [Modal Discord](https://discord.gg/modal)
- [GitHub Issues](https://github.com/your-repo/issues)

---

**Happy VDP processing! 🚀**
