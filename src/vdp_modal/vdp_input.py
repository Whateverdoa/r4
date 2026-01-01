"""DataFrame ingestion for VDP workflows.

This module handles the transformation from raw data (Excel, CSV, DataFrame)
into clean, validated VDP job objects ready for rendering.

Architecture:
    DataFrame → Normalize → Validate → Transform → VDPBatch → Workers

Usage:
    import pandas as pd
    from vdp_modal.vdp_input import dataframe_to_vdp_batch, TemplateConfig, FieldMapping

    # Load data
    df = pd.read_excel("orders.xlsx")

    # Define template
    template = TemplateConfig(
        template_id="product_label_v2",
        label_width_mm=100,
        label_height_mm=150,
        fields=[
            FieldMapping(source_column="Article", target_name="product_code", transform="trim"),
            FieldMapping(source_column="Description", target_name="product_name"),
            FieldMapping(source_column="EAN", target_name="barcode", transform="ean13_check_digit"),
        ],
    )

    # Convert to VDP batch
    batch = dataframe_to_vdp_batch(df, template, job_id="job-001")

    # Send to Modal workers
    result = run_vdp_pipeline.remote(batch.to_modal_format())
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
import pandas as pd
from .transforms import apply_transform, TRANSFORMS


# ========================================================================
# PYDANTIC MODELS
# ========================================================================


class FieldMapping(BaseModel):
    """Maps a source DataFrame column to a VDP field."""

    source_column: str = Field(..., description="Source column name in DataFrame")
    target_name: str = Field(..., description="Target field name in VDP record")
    required: bool = Field(default=True, description="Is this field required?")
    default: Optional[str] = Field(default=None, description="Default value if missing")
    transform: Optional[str] = Field(default=None, description="Transform to apply")

    @field_validator("transform")
    @classmethod
    def validate_transform(cls, v: Optional[str]) -> Optional[str]:
        """Validate that transform exists in registry."""
        if v is not None and v not in TRANSFORMS:
            raise ValueError(f"Unknown transform: '{v}'. Available: {list(TRANSFORMS.keys())}")
        return v


class BarcodeConfig(BaseModel):
    """Configuration for a barcode field."""

    field_name: str = Field(..., description="Field name containing barcode data")
    barcode_type: str = Field(default="code128", description="Barcode symbology")
    format: str = Field(default="raster", description="Format: 'raster' or 'vector'")
    dpi: int = Field(default=300, description="Resolution for raster barcodes")
    scale: float = Field(default=2.0, description="Scale factor for vector barcodes")
    height: int = Field(default=50, description="Barcode height in modules")


class TemplateConfig(BaseModel):
    """VDP template configuration."""

    template_id: str = Field(..., description="Unique template identifier")
    label_width_mm: float = Field(..., description="Label width in millimeters")
    label_height_mm: float = Field(..., description="Label height in millimeters")
    dpi: int = Field(default=300, description="Resolution in DPI")
    fields: list[FieldMapping] = Field(..., description="Field mappings")
    barcodes: dict[str, BarcodeConfig] = Field(
        default_factory=dict, description="Barcode configurations"
    )
    layout: str = Field(default="single", description="Layout type: single, grid, roll")

    # Sheet layout (for grid layout)
    sheet_columns: int = Field(default=2, description="Columns per sheet")
    sheet_rows: int = Field(default=5, description="Rows per sheet")

    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class VDPRecord(BaseModel):
    """A single VDP record (one label/document)."""

    record_index: int = Field(..., description="Original row index from DataFrame")
    fields: dict[str, str] = Field(..., description="Normalized field data")
    artwork_id: Optional[str] = Field(default=None, description="Artwork/template variant ID")
    group_id: Optional[str] = Field(
        default=None, description="Group ID for combo labels (same artwork, multiple SKUs)"
    )
    quantity: int = Field(default=1, description="Number of copies to print")


class VDPBatch(BaseModel):
    """A complete VDP job batch."""

    job_id: str = Field(..., description="Unique job identifier")
    template: TemplateConfig = Field(..., description="Template configuration")
    records: list[VDPRecord] = Field(..., description="VDP records")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Job metadata")

    @property
    def total_labels(self) -> int:
        """Total number of labels (accounting for quantities)."""
        return sum(r.quantity for r in self.records)

    def to_modal_format(self) -> dict[str, Any]:
        """
        Convert to format expected by Modal workers.

        Returns:
            Dictionary with records and template suitable for run_vdp_pipeline()
        """
        return {
            "records": [r.fields for r in self.records],
            "template": {
                "title": self.template.template_id,
                "barcode_type": "code128",  # default, override via template
                "layout": self.template.layout,
                "sheet_columns": self.template.sheet_columns,
                "sheet_rows": self.template.sheet_rows,
            },
            "job_id": self.job_id,
            "metadata": self.metadata,
        }

    def expand_quantities(self) -> "VDPBatch":
        """
        Expand records based on quantity field.

        Example:
            Input: 1 record with quantity=5
            Output: 5 identical records with quantity=1

        Returns:
            New VDPBatch with expanded records
        """
        expanded_records = []

        for record in self.records:
            for _ in range(record.quantity):
                expanded = record.model_copy()
                expanded.quantity = 1
                expanded_records.append(expanded)

        return VDPBatch(
            job_id=self.job_id,
            template=self.template,
            records=expanded_records,
            metadata={**self.metadata, "quantity_expanded": True},
        )

    def chunk_for_workers(self, chunk_size: int = 100) -> list["VDPBatch"]:
        """
        Split into chunks for parallel processing.

        Args:
            chunk_size: Records per chunk

        Returns:
            List of VDPBatch objects (one per chunk)
        """
        chunks = []

        for i in range(0, len(self.records), chunk_size):
            chunk_records = self.records[i : i + chunk_size]

            chunk_batch = VDPBatch(
                job_id=f"{self.job_id}_chunk_{i // chunk_size}",
                template=self.template,
                records=chunk_records,
                metadata={
                    **self.metadata,
                    "parent_job_id": self.job_id,
                    "chunk_index": i // chunk_size,
                    "chunk_size": len(chunk_records),
                },
            )
            chunks.append(chunk_batch)

        return chunks


# ========================================================================
# DATAFRAME PROCESSING
# ========================================================================


class ValidationError(Exception):
    """VDP validation error with details."""

    def __init__(self, errors: list[dict[str, Any]]):
        self.errors = errors
        super().__init__(self._format_errors())

    def _format_errors(self) -> str:
        lines = ["VDP validation failed:"]
        for err in self.errors:
            lines.append(f"  Row {err['row']}: {err['message']}")
        return "\n".join(lines)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame column names.

    - Lowercase
    - Strip whitespace
    - Map common synonyms

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with normalized columns
    """
    df = df.copy()

    # Lowercase and strip
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Map common synonyms
    synonyms = {
        "artikel": "article",
        "article_code": "article",
        "artikelcode": "article",
        "description": "product_name",
        "qty": "quantity",
        "amount": "quantity",
    }

    df.columns = [synonyms.get(c, c) for c in df.columns]

    return df


def apply_mapping_to_row(
    row: pd.Series, template: TemplateConfig, row_index: int
) -> tuple[dict[str, str], list[str]]:
    """
    Apply field mappings to a single DataFrame row.

    Args:
        row: DataFrame row
        template: Template configuration
        row_index: Row index for error reporting

    Returns:
        Tuple of (field_data, errors)
    """
    result: dict[str, str] = {}
    errors: list[str] = []

    for fm in template.fields:
        src = fm.source_column.lower()

        # Check if column exists
        if src not in row.index:
            if fm.required and fm.default is None:
                errors.append(f"Missing required column '{fm.source_column}'")
                continue
            value = fm.default
        else:
            value = row[src]

        # Handle NaN/None
        if pd.isna(value):
            if fm.required and fm.default is None:
                errors.append(f"Empty value in required field '{fm.source_column}'")
                continue
            value = fm.default

        # Apply transform if specified
        if fm.transform and value is not None:
            try:
                value = apply_transform(fm.transform, value)
            except Exception as e:
                errors.append(f"Transform '{fm.transform}' failed on '{fm.source_column}': {e}")
                continue

        # Cast to string for VDP pipeline
        result[fm.target_name] = "" if value is None else str(value)

    return result, errors


def dataframe_to_vdp_batch(
    df: pd.DataFrame,
    template: TemplateConfig,
    job_id: str,
    metadata: Optional[dict[str, Any]] = None,
    quantity_column: Optional[str] = None,
    artwork_column: Optional[str] = None,
    group_column: Optional[str] = None,
    skip_validation_errors: bool = False,
) -> VDPBatch:
    """
    Convert DataFrame to VDPBatch.

    Args:
        df: Input DataFrame
        template: Template configuration
        job_id: Unique job identifier
        metadata: Optional job metadata
        quantity_column: Column name for print quantity (default: 1)
        artwork_column: Column name for artwork ID
        group_column: Column name for group ID
        skip_validation_errors: If True, skip rows with errors instead of raising

    Returns:
        VDPBatch ready for workers

    Raises:
        ValidationError: If validation fails and skip_validation_errors=False
    """
    # Normalize column names
    df_norm = normalize_columns(df)

    records: list[VDPRecord] = []
    validation_errors: list[dict[str, Any]] = []

    for idx, row in df_norm.iterrows():
        # Apply field mappings
        field_data, errors = apply_mapping_to_row(row, template, idx)

        if errors:
            for error in errors:
                validation_errors.append({"row": idx, "message": error})

            if not skip_validation_errors:
                continue

        # Extract quantity
        quantity = 1
        if quantity_column:
            qty_col = quantity_column.lower()
            if qty_col in row.index and not pd.isna(row[qty_col]):
                try:
                    quantity = int(row[qty_col])
                except (ValueError, TypeError):
                    validation_errors.append(
                        {"row": idx, "message": f"Invalid quantity: {row[qty_col]}"}
                    )

        # Extract artwork_id
        artwork_id = None
        if artwork_column:
            art_col = artwork_column.lower()
            if art_col in row.index and not pd.isna(row[art_col]):
                artwork_id = str(row[art_col])

        # Extract group_id
        group_id = None
        if group_column:
            grp_col = group_column.lower()
            if grp_col in row.index and not pd.isna(row[grp_col]):
                group_id = str(row[grp_col])

        # Create record
        record = VDPRecord(
            record_index=int(idx),
            fields=field_data,
            artwork_id=artwork_id,
            group_id=group_id,
            quantity=quantity,
        )
        records.append(record)

    # Check for validation errors
    if validation_errors and not skip_validation_errors:
        raise ValidationError(validation_errors)

    # Create batch
    batch = VDPBatch(
        job_id=job_id,
        template=template,
        records=records,
        metadata=metadata or {},
    )

    return batch


def dataframe_to_vdp_batches_multi_template(
    df: pd.DataFrame,
    templates: dict[str, TemplateConfig],
    template_column: str,
    job_id_prefix: str = "job",
    **kwargs,
) -> list[VDPBatch]:
    """
    Convert DataFrame with multiple templates to multiple VDPBatches.

    Use when your DataFrame has a column that specifies which template to use
    for each row.

    Args:
        df: Input DataFrame
        templates: Dictionary of template_key -> TemplateConfig
        template_column: Column name containing template key
        job_id_prefix: Prefix for job IDs
        **kwargs: Additional arguments for dataframe_to_vdp_batch()

    Returns:
        List of VDPBatch objects (one per template)
    """
    df_norm = normalize_columns(df)
    template_col = template_column.lower()

    if template_col not in df_norm.columns:
        raise ValueError(f"Template column '{template_column}' not found in DataFrame")

    batches = []

    # Group by template
    for template_key, group_df in df_norm.groupby(template_col):
        if template_key not in templates:
            raise ValueError(f"Unknown template key: '{template_key}'")

        template = templates[template_key]
        job_id = f"{job_id_prefix}_{template_key}"

        batch = dataframe_to_vdp_batch(
            df=group_df,
            template=template,
            job_id=job_id,
            **kwargs,
        )
        batches.append(batch)

    return batches


# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================


def load_excel_to_vdp_batch(
    filepath: str,
    template: TemplateConfig,
    job_id: str,
    sheet_name: str | int = 0,
    **kwargs,
) -> VDPBatch:
    """
    Load Excel file and convert to VDPBatch.

    Args:
        filepath: Path to Excel file
        template: Template configuration
        job_id: Job identifier
        sheet_name: Sheet name or index
        **kwargs: Additional arguments for dataframe_to_vdp_batch()

    Returns:
        VDPBatch
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    return dataframe_to_vdp_batch(df, template, job_id, **kwargs)


def load_csv_to_vdp_batch(
    filepath: str,
    template: TemplateConfig,
    job_id: str,
    **kwargs,
) -> VDPBatch:
    """
    Load CSV file and convert to VDPBatch.

    Args:
        filepath: Path to CSV file
        template: Template configuration
        job_id: Job identifier
        **kwargs: Additional arguments for dataframe_to_vdp_batch()

    Returns:
        VDPBatch
    """
    df = pd.read_csv(filepath)
    return dataframe_to_vdp_batch(df, template, job_id, **kwargs)
