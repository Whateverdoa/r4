# Modal VDP - Massive Parallel Variable Data Printing

A serverless platform for massive-scale Variable Data Printing (VDP) generation using Modal's infrastructure.

## Features

- **Massive Parallelization**: Scale from 40 to 4000+ workers instantly
- **CPU-Heavy Prepress Tasks**: PyMuPDF, ReportLab, image processing
- **Barcode Generation**: GS1-128, QR codes, and more
  - **Raster barcodes**: PNG format using python-barcode
  - **Vector barcodes**: SVG/EPS format using zint (professional printing)
- **PDF Processing**: Parallel rendering, assembly, and validation
- **Prepress Tools**: Ghostscript for CMYK conversion, PDF/X compliance
- **DataFrame Ingestion**: Excel/CSV → VDP pipeline with Pydantic validation
  - **Field mapping** with automatic column normalization
  - **Transform registry** (20+ transforms: EAN-13, SSCC-18, date formatting, etc.)
  - **Quantity expansion** and chunking for parallel workers
  - **Multi-template support** in single DataFrame
- **Template Builder**: Easy template creation and management
  - **Fluent API** for programmatic template building
  - **Template library** with 12+ pre-built templates
  - **JSON serialization** for saving/loading templates
  - **Template registry** for organizing and discovering templates
  - **Interactive CLI** builder for no-code template creation
  - **Validation** and introspection tools
- **Async Pipelines**: Orchestrate complex workflows
- **Flexible Storage**: Modal Volumes, S3, or local storage
  - **Modal Storage** (recommended): Built-in Volumes and Dicts, no credentials needed
  - **S3 Storage**: AWS integration for existing infrastructure
  - **Local Storage**: Development and testing
- **GPU-Ready**: Future support for AI agents (OCR, vision models, layout analysis)

## Use Cases

1. **VDP Generation**: Split large jobs into 1000s of parallel tasks
2. **Batch Processing**: Process thousands of labels, barcodes, or PDFs
3. **Prepress Workflows**: Image preprocessing, layer extraction, vector analysis
4. **AI Agents**: OCR, spec detection, PDF fixing (GPU-accelerated)

## Quick Start

### Installation

```bash
# Install Modal CLI
pip install modal

# Authenticate with Modal
modal setup

# Install project dependencies
pip install -e .
```

### Run Your First VDP Job

```python
import modal
from vdp_modal import vdp_app

# Generate 1000 barcoded labels in parallel
with modal.runner.deploy_app(vdp_app):
    result = vdp_app.generate_vdp_batch.remote(
        job_id="job-001",
        records=1000,
        template="label_template.json"
    )
```

## Project Structure

```
modal-vdp/
├── src/
│   └── vdp_modal/
│       ├── app.py              # Main Modal application
│       ├── barcode.py          # Barcode generation
│       ├── pdf_processing.py   # PDF utilities
│       ├── pipeline.py         # Async pipeline orchestration
│       ├── assembly.py         # File assembly and merging
│       └── storage.py          # S3/cloud storage
├── examples/
│   ├── simple_vdp.py          # Basic VDP example
│   ├── barcode_batch.py       # Barcode generation
│   └── pipeline_example.py    # Full pipeline workflow
├── tests/
├── pyproject.toml
└── README.md
```

## Architecture

### Parallel VDP Pipeline

```
Data Ingest
    ↓
Split into Tasks (1 → 1000s)
    ↓
Parallel Workers (Modal Functions)
│   ├── Barcode Generation
│   ├── PDF Rendering
│   ├── Image Processing
│   └── Metadata Extraction
    ↓
Assembly (Combine Results)
    ↓
Upload to S3 / DFE
```

### Key Components

- **Modal Functions**: Serverless workers that auto-scale
- **Volumes**: Shared storage for large files
- **Queues**: Async task orchestration
- **Images**: Pre-configured containers with dependencies

## Examples

### 1. Parallel Barcode Generation

```python
# Generate 10,000 GS1-128 barcodes in parallel
result = generate_barcodes.map(
    serial_numbers,
    barcode_type="gs1-128",
    dpi=300
)
```

### 2. VDP PDF Assembly

```python
# Split job → render pages → assemble final PDF
job = split_vdp_job(data, chunks=1000)
pages = render_pdf_pages.map(job.chunks)
final_pdf = assemble_pdf(pages)
```

### 3. Async Pipeline

```python
# Full workflow: ingest → process → generate → upload
pipeline = VDPPipeline()
await pipeline.run(
    input_data="orders.csv",
    template="label.json",
    output_bucket="s3://my-bucket/output/"
)
```

### 4. Storage Options

```python
# Option 1: Modal Storage (recommended, no credentials needed)
result = run_vdp_pipeline.remote(
    records=data,
    template=template,
    job_id="job-001",
    storage_backend="modal",  # Saves to Modal Volume
)

# Option 2: S3 Storage (for AWS integration)
result = run_vdp_pipeline.remote(
    records=data,
    template=template,
    job_id="job-002",
    storage_backend="s3",
    s3_bucket="my-bucket",
)

# Option 3: Local Storage (for testing)
result = run_vdp_pipeline.remote(
    records=data,
    template=template,
    job_id="job-003",
    storage_backend="local",  # Returns bytes
)
```

See [STORAGE_GUIDE.md](STORAGE_GUIDE.md) for detailed storage documentation.

## Performance

- **Cold Start**: Sub-second (Modal optimized)
- **Scalability**: 40 → 4000 workers automatically
- **Cost**: Pay per second of compute
- **Concurrency**: 1000s of parallel tasks

## Development

```bash
# Run tests
pytest

# Format code
black src/

# Lint
ruff src/

# Type check
mypy src/
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[STORAGE_GUIDE.md](STORAGE_GUIDE.md)** - Complete storage documentation (Modal, S3, local)
- **[VECTOR_BARCODES.md](VECTOR_BARCODES.md)** - Professional vector barcode generation with zint

## Roadmap

- [x] Core VDP pipeline
- [x] Barcode generation (raster + vector)
- [x] PDF processing
- [x] Modal storage (Volumes + Dicts)
- [x] S3 integration
- [x] Vector barcodes with zint
- [x] Ghostscript for prepress
- [ ] GPU-based AI agents
- [ ] OCR and vision models
- [ ] Real-time webhooks
- [ ] Scheduled workers
- [ ] Advanced color management (ICC profiles)

## License

MIT

## Links

- [Modal Documentation](https://modal.com/docs)
- [Modal Examples](https://modal.com/docs/examples)
- [Zint Barcode Generator](https://zint.org.uk/)
- [Ghostscript](https://www.ghostscript.com/)
