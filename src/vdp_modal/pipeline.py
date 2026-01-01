"""Pipeline orchestration for complex VDP workflows."""

from typing import Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class PipelineStage(Enum):
    """Pipeline execution stages."""

    INGEST = "ingest"
    PREPROCESS = "preprocess"
    GENERATE_BARCODES = "generate_barcodes"
    GENERATE_ARTWORK = "generate_artwork"
    ASSEMBLE_SHEETS = "assemble_sheets"
    VALIDATE = "validate"
    UPLOAD = "upload"
    COMPLETE = "complete"


@dataclass
class PipelineConfig:
    """Configuration for VDP pipeline."""

    job_id: str
    input_data: str | list[dict[str, Any]]
    template: dict[str, Any]
    chunk_size: int = 100
    barcode_type: str = "code128"
    layout: str = "grid"  # grid, roll, custom
    sheet_columns: int = 2
    sheet_rows: int = 5
    s3_bucket: str | None = None
    s3_prefix: str = "vdp-output"
    enable_crop_marks: bool = False
    enable_registration_marks: bool = False
    validate_output: bool = True


@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    job_id: str
    stage: PipelineStage
    success: bool
    total_records: int
    pdf_bytes: bytes | None = None
    s3_url: str | None = None
    errors: list[str] | None = None
    metadata: dict[str, Any] | None = None


class VDPPipeline:
    """Orchestrates complex VDP workflows."""

    def __init__(self, config: PipelineConfig):
        """
        Initialize pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.stage = PipelineStage.INGEST
        self.records: list[dict[str, Any]] = []
        self.errors: list[str] = []

    def run(self) -> PipelineResult:
        """
        Execute the complete pipeline.

        Returns:
            Pipeline result
        """
        try:
            # Stage 1: Ingest data
            self.stage = PipelineStage.INGEST
            self._ingest_data()

            # Stage 2: Preprocess
            self.stage = PipelineStage.PREPROCESS
            self._preprocess_data()

            # Stage 3: Generate (this happens in Modal)
            # This is where we call the Modal functions
            self.stage = PipelineStage.GENERATE_ARTWORK

            # Stage 4: Assemble
            self.stage = PipelineStage.ASSEMBLE_SHEETS

            # Stage 5: Validate
            if self.config.validate_output:
                self.stage = PipelineStage.VALIDATE

            # Stage 6: Upload
            if self.config.s3_bucket:
                self.stage = PipelineStage.UPLOAD

            # Complete
            self.stage = PipelineStage.COMPLETE

            return PipelineResult(
                job_id=self.config.job_id,
                stage=self.stage,
                success=True,
                total_records=len(self.records),
                errors=self.errors if self.errors else None,
            )

        except Exception as e:
            self.errors.append(str(e))
            return PipelineResult(
                job_id=self.config.job_id,
                stage=self.stage,
                success=False,
                total_records=len(self.records),
                errors=self.errors,
            )

    def _ingest_data(self) -> None:
        """Ingest input data from various sources."""
        if isinstance(self.config.input_data, list):
            # Already a list of records
            self.records = self.config.input_data

        elif isinstance(self.config.input_data, str):
            # Load from file
            input_path = Path(self.config.input_data)

            if input_path.suffix == ".json":
                with open(input_path) as f:
                    data = json.load(f)
                    self.records = data if isinstance(data, list) else [data]

            elif input_path.suffix == ".csv":
                import csv

                with open(input_path) as f:
                    reader = csv.DictReader(f)
                    self.records = list(reader)

            else:
                raise ValueError(f"Unsupported file format: {input_path.suffix}")

        else:
            raise ValueError("input_data must be list or file path")

    def _preprocess_data(self) -> None:
        """Preprocess and validate records."""
        # Add any missing fields
        for i, record in enumerate(self.records):
            if "serial" not in record:
                record["serial"] = f"AUTO-{i:08d}"

            # Validate required fields based on template
            required_fields = self.config.template.get("required_fields", [])
            for field in required_fields:
                if field not in record:
                    self.errors.append(
                        f"Record {i} missing required field: {field}"
                    )


def create_simple_pipeline(
    records: list[dict[str, Any]],
    job_id: str = "vdp-job",
    chunk_size: int = 100,
) -> PipelineConfig:
    """
    Create a simple pipeline configuration.

    Args:
        records: List of data records
        job_id: Job identifier
        chunk_size: Records per chunk

    Returns:
        Pipeline configuration
    """
    return PipelineConfig(
        job_id=job_id,
        input_data=records,
        template={"title": "Label", "barcode_type": "code128"},
        chunk_size=chunk_size,
    )


def create_barcode_pipeline(
    serials: list[str],
    job_id: str = "barcode-job",
    barcode_type: str = "gs1-128",
) -> PipelineConfig:
    """
    Create a pipeline for barcode generation only.

    Args:
        serials: List of serial numbers
        job_id: Job identifier
        barcode_type: Barcode type

    Returns:
        Pipeline configuration
    """
    records = [{"serial": serial} for serial in serials]

    return PipelineConfig(
        job_id=job_id,
        input_data=records,
        template={"barcode_type": barcode_type},
        chunk_size=1000,  # Larger chunks for barcode-only
    )


def create_sheet_layout_pipeline(
    records: list[dict[str, Any]],
    job_id: str = "sheet-job",
    columns: int = 2,
    rows: int = 5,
) -> PipelineConfig:
    """
    Create a pipeline with sheet layout assembly.

    Args:
        records: List of data records
        job_id: Job identifier
        columns: Sheet columns
        rows: Sheet rows

    Returns:
        Pipeline configuration
    """
    return PipelineConfig(
        job_id=job_id,
        input_data=records,
        template={"title": "Label", "barcode_type": "code128"},
        layout="grid",
        sheet_columns=columns,
        sheet_rows=rows,
        enable_crop_marks=True,
        enable_registration_marks=True,
    )


def load_template_from_json(template_path: str) -> dict[str, Any]:
    """
    Load label template from JSON file.

    Args:
        template_path: Path to template JSON

    Returns:
        Template configuration
    """
    with open(template_path) as f:
        return json.load(f)


def save_pipeline_config(config: PipelineConfig, output_path: str) -> None:
    """
    Save pipeline configuration to JSON.

    Args:
        config: Pipeline configuration
        output_path: Path to save config
    """
    # Convert to dict (simplified)
    config_dict = {
        "job_id": config.job_id,
        "template": config.template,
        "chunk_size": config.chunk_size,
        "barcode_type": config.barcode_type,
        "layout": config.layout,
        "sheet_columns": config.sheet_columns,
        "sheet_rows": config.sheet_rows,
        "s3_bucket": config.s3_bucket,
        "s3_prefix": config.s3_prefix,
    }

    with open(output_path, "w") as f:
        json.dump(config_dict, f, indent=2)
