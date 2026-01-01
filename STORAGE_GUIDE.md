# Storage Guide

Complete guide to storage options in Modal VDP.

## Overview

Modal VDP supports three storage backends:

1. **Modal Storage** (Volumes + Dicts) - Recommended
2. **S3 Storage** - For AWS integration
3. **Local Storage** - For development/testing

## Modal Storage (Recommended)

### Volumes - For Large Files (PDFs, Images)

Modal Volumes provide persistent, high-performance file storage that persists across function calls.

**Benefits:**
- No AWS credentials needed
- Fast access within Modal ecosystem
- Automatic versioning and snapshots
- Shared across Modal apps
- Built-in replication

**Usage:**

```python
from vdp_modal.app import run_vdp_pipeline

result = run_vdp_pipeline.remote(
    records=your_data,
    template=your_template,
    job_id="my-job",
    storage_backend="modal",  # Use Modal storage
)

# File saved to Modal Volume
print(result["storage_url"])  # modal://jobs/my-job/output.pdf
```

**Volume Structure:**

```
/vdp-storage/
├── jobs/
│   ├── job-001/
│   │   └── output.pdf
│   ├── job-002/
│   │   └── output.pdf
│   └── ...
├── barcodes/
│   ├── job-001/
│   │   ├── barcode_00000000.png
│   │   ├── barcode_00000001.png
│   │   └── ...
│   └── ...
└── batch/
    └── ...
```

### Dicts - For Metadata (JSON Data)

Modal Dicts provide fast key-value storage for job metadata and results.

**Benefits:**
- Instant lookups
- No S3 API calls
- Built-in serialization
- Perfect for job status tracking

**Usage:**

```python
from vdp_modal.app import save_job_metadata, get_job_metadata

# Save metadata
save_job_metadata.remote(
    job_id="my-job",
    metadata={
        "total_records": 1000,
        "created_by": "user@example.com",
        "template_version": "v2",
    }
)

# Retrieve metadata
metadata = get_job_metadata.remote("my-job")
print(metadata["total_records"])  # 1000
```

**Dict Structure:**

```
job:my-job:metadata    → Job configuration and input data
job:my-job:result      → Job result summary
job:my-job:status      → Current job status and progress
```

### Accessing Files from Modal Volume

```python
# In a Modal function with volume mounted
@app.function(volumes={"/data": vdp_volume})
def read_output():
    with open("/data/jobs/my-job/output.pdf", "rb") as f:
        pdf_bytes = f.read()
    return pdf_bytes
```

## S3 Storage

Use S3 for integration with existing AWS infrastructure or long-term archival.

**Benefits:**
- Integration with AWS ecosystem
- Long-term archival
- CDN distribution (via CloudFront)
- External system access

**Setup:**

```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export VDP_S3_BUCKET="your-bucket"
```

**Usage:**

```python
result = run_vdp_pipeline.remote(
    records=your_data,
    template=your_template,
    job_id="my-job",
    storage_backend="s3",
    s3_bucket="my-vdp-bucket",
    s3_prefix="production/output",
)

print(result["storage_url"])  # s3://my-vdp-bucket/production/output/my-job/output.pdf
```

**S3 Structure:**

```
s3://my-bucket/
├── production/
│   └── output/
│       ├── job-001/
│       │   └── output.pdf
│       └── job-002/
│           └── output.pdf
└── vdp-metadata/
    ├── job-001/
    │   └── metadata.json
    └── job-002/
        └── metadata.json
```

## Local Storage

Use for development, testing, or when you want direct bytes access.

**Benefits:**
- Simple and straightforward
- No credentials needed
- Full control over file location
- Good for testing

**Usage:**

```python
result = run_vdp_pipeline.remote(
    records=your_data,
    template=your_template,
    job_id="my-job",
    storage_backend="local",
)

# Save the returned bytes
with open("output.pdf", "wb") as f:
    f.write(result["pdf_bytes"])
```

## Unified Storage Interface

For applications that need to switch between storage backends:

```python
from vdp_modal.modal_storage import UnifiedStorage

# Initialize with backend of choice
storage = UnifiedStorage(backend="modal")
# or
storage = UnifiedStorage(backend="s3", s3_bucket="my-bucket")
# or
storage = UnifiedStorage(backend="local")

# Same interface for all backends
storage_url = storage.save_pdf(
    pdf_bytes=my_pdf,
    job_id="my-job",
    filename="output.pdf"
)

storage.save_metadata(
    job_id="my-job",
    metadata={"total_records": 1000}
)
```

## Comparison Table

| Feature | Modal Storage | S3 Storage | Local Storage |
|---------|---------------|------------|---------------|
| **Setup** | None needed | AWS credentials | None needed |
| **Cost** | Included in Modal | S3 pricing | Free |
| **Speed (Modal)** | Fast | Medium | N/A |
| **Speed (External)** | Medium | Fast | Instant |
| **Persistence** | Permanent | Permanent | Temporary |
| **Sharing** | Modal apps only | Anyone with access | Local only |
| **Versioning** | Built-in | Optional | Manual |
| **Best For** | Modal workflows | AWS integration | Development |

## Best Practices

### For Production Workloads

```python
# Use Modal storage with metadata tracking
result = run_vdp_pipeline.remote(
    records=records,
    template=template,
    job_id=job_id,
    storage_backend="modal",
    save_metadata=True,  # Track job in Modal Dict
)

# Optionally copy to S3 for archival
if archive_to_s3:
    upload_to_s3.remote(
        result["pdf_bytes"],
        job_id,
        "archive-bucket",
    )
```

### For Development

```python
# Use local storage for quick iteration
result = run_vdp_pipeline.remote(
    records=test_records,
    template=test_template,
    job_id="test",
    storage_backend="local",
    save_metadata=False,  # Skip metadata for testing
)
```

### For Hybrid Workflows

```python
# Save to Modal Volume for fast Modal access
# Also upload to S3 for external systems
result = run_vdp_pipeline.remote(
    records=records,
    template=template,
    job_id=job_id,
    storage_backend="modal",
)

# Parallel upload to S3
upload_to_s3.remote(
    result["pdf_bytes"],
    job_id,
    "external-bucket",
)
```

## Storage Costs

### Modal Storage
- **Volumes**: $0.10/GB-month
- **Dicts**: Included (reasonable use)
- **Egress**: Free within Modal

### S3 Storage
- **Storage**: ~$0.023/GB-month (Standard)
- **Requests**: ~$0.005 per 1,000 PUT requests
- **Egress**: $0.09/GB (to internet)

### Recommendation

For most use cases, **use Modal Storage** for active jobs and **archive to S3** for long-term storage:

```python
# Keep last 30 days in Modal Volume (fast access)
# Archive older jobs to S3 (cheaper long-term)
```

## Cleanup and Maintenance

### Delete Old Jobs from Modal Volume

```python
@app.function(volumes={"/data": vdp_volume})
def cleanup_old_jobs(days_old: int = 30):
    import os
    import time
    from pathlib import Path

    cutoff_time = time.time() - (days_old * 86400)
    jobs_dir = Path("/data/jobs")

    for job_dir in jobs_dir.iterdir():
        if job_dir.stat().st_mtime < cutoff_time:
            shutil.rmtree(job_dir)
            print(f"Deleted old job: {job_dir.name}")

    vdp_volume.commit()
```

### Archive to S3 Before Cleanup

```python
# Archive before deleting
archive_to_s3.remote(job_id)
cleanup_old_jobs.remote(days_old=30)
```

## Examples

See the `examples/` directory for complete examples:

- `modal_storage_example.py` - Using Modal Volumes and Dicts
- `storage_comparison.py` - Compare all storage backends
- `full_pipeline.py` - S3 storage example

## Troubleshooting

### Modal Volume Not Persisting

Make sure to call `volume.commit()` after writes:

```python
@app.function(volumes={"/data": vdp_volume})
def save_file():
    with open("/data/output.pdf", "wb") as f:
        f.write(pdf_bytes)

    vdp_volume.commit()  # Important!
```

### S3 Access Denied

Check AWS credentials:

```bash
modal secret list  # Check if AWS credentials are set
modal secret create aws-credentials \
    AWS_ACCESS_KEY_ID="..." \
    AWS_SECRET_ACCESS_KEY="..."
```

### Modal Dict Key Not Found

Modal Dicts return `None` for missing keys (like Python dicts):

```python
metadata = vdp_dict.get("job:my-job:metadata")
if metadata is None:
    print("Job not found")
```

---

For more information, see:
- [Modal Volumes Documentation](https://modal.com/docs/guide/volumes)
- [Modal Dicts Documentation](https://modal.com/docs/guide/dicts)
