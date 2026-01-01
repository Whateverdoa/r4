"""Transform functions for VDP field processing.

This module provides a registry of transform functions that can be applied
to DataFrame columns during VDP ingestion.

Usage:
    from vdp_modal.transforms import apply_transform

    result = apply_transform("uppercase", "hello world")  # "HELLO WORLD"
"""

from typing import Any, Callable
import re


# Transform registry: name -> function
TRANSFORMS: dict[str, Callable[[Any], Any]] = {}


def register_transform(name: str):
    """Decorator to register a transform function."""

    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        TRANSFORMS[name] = func
        return func

    return decorator


# ========================================================================
# STRING TRANSFORMS
# ========================================================================


@register_transform("trim")
def transform_trim(value: Any) -> str:
    """Remove leading/trailing whitespace."""
    return value.strip() if isinstance(value, str) else str(value)


@register_transform("uppercase")
def transform_uppercase(value: Any) -> str:
    """Convert to uppercase."""
    return value.upper() if isinstance(value, str) else str(value)


@register_transform("lowercase")
def transform_lowercase(value: Any) -> str:
    """Convert to lowercase."""
    return value.lower() if isinstance(value, str) else str(value)


@register_transform("title")
def transform_title(value: Any) -> str:
    """Convert to title case."""
    return value.title() if isinstance(value, str) else str(value)


@register_transform("remove_spaces")
def transform_remove_spaces(value: Any) -> str:
    """Remove all spaces."""
    return value.replace(" ", "") if isinstance(value, str) else str(value)


@register_transform("alphanumeric_only")
def transform_alphanumeric_only(value: Any) -> str:
    """Keep only alphanumeric characters."""
    if not isinstance(value, str):
        value = str(value)
    return re.sub(r"[^a-zA-Z0-9]", "", value)


# ========================================================================
# NUMERIC TRANSFORMS
# ========================================================================


@register_transform("zero_pad_6")
def transform_zero_pad_6(value: Any) -> str:
    """Zero-pad to 6 digits."""
    return str(value).zfill(6)


@register_transform("zero_pad_8")
def transform_zero_pad_8(value: Any) -> str:
    """Zero-pad to 8 digits."""
    return str(value).zfill(8)


@register_transform("zero_pad_12")
def transform_zero_pad_12(value: Any) -> str:
    """Zero-pad to 12 digits."""
    return str(value).zfill(12)


@register_transform("format_decimal_2")
def transform_format_decimal_2(value: Any) -> str:
    """Format as decimal with 2 places."""
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return str(value)


# ========================================================================
# BARCODE TRANSFORMS
# ========================================================================


@register_transform("ean13_check_digit")
def transform_ean13_check_digit(value: Any) -> str:
    """
    Add EAN-13 check digit.

    Input: 12-digit code
    Output: 13-digit code with check digit
    """
    code = str(value).strip()

    # Remove check digit if already present
    if len(code) == 13:
        code = code[:12]

    if len(code) != 12:
        raise ValueError(f"EAN-13 requires 12 digits, got {len(code)}")

    # Calculate check digit
    odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code[i]) for i in range(1, 12, 2))
    total = odd_sum + (even_sum * 3)
    check_digit = (10 - (total % 10)) % 10

    return code + str(check_digit)


@register_transform("ean8_check_digit")
def transform_ean8_check_digit(value: Any) -> str:
    """
    Add EAN-8 check digit.

    Input: 7-digit code
    Output: 8-digit code with check digit
    """
    code = str(value).strip()

    if len(code) == 8:
        code = code[:7]

    if len(code) != 7:
        raise ValueError(f"EAN-8 requires 7 digits, got {len(code)}")

    # Calculate check digit
    odd_sum = sum(int(code[i]) for i in range(1, 7, 2))
    even_sum = sum(int(code[i]) for i in range(0, 7, 2))
    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10

    return code + str(check_digit)


@register_transform("sscc18_from_base")
def transform_sscc18_from_base(value: Any) -> str:
    """
    Generate SSCC-18 from base serial.

    Input: Base serial number
    Output: 18-digit SSCC with check digit
    """
    serial = str(value).strip()

    # Pad to 17 digits
    if len(serial) < 17:
        serial = serial.zfill(17)
    elif len(serial) > 17:
        serial = serial[:17]

    # Calculate check digit
    odd_sum = sum(int(serial[i]) for i in range(1, 17, 2))
    even_sum = sum(int(serial[i]) for i in range(0, 17, 2))
    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10

    return serial + str(check_digit)


@register_transform("gtin_check_digit")
def transform_gtin_check_digit(value: Any) -> str:
    """
    Add GTIN check digit (works for GTIN-8, GTIN-12, GTIN-13, GTIN-14).

    Input: N-1 digits
    Output: N digits with check digit
    """
    code = str(value).strip()

    # Calculate check digit
    odd_sum = sum(int(code[i]) for i in range(len(code) - 1, -1, -2))
    even_sum = sum(int(code[i]) for i in range(len(code) - 2, -1, -2))
    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10

    return code + str(check_digit)


# ========================================================================
# DATE/TIME TRANSFORMS
# ========================================================================


@register_transform("date_yyyymmdd")
def transform_date_yyyymmdd(value: Any) -> str:
    """Format date as YYYY-MM-DD."""
    import pandas as pd

    if pd.isna(value):
        return ""

    try:
        dt = pd.to_datetime(value)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(value)


@register_transform("date_ddmmyyyy")
def transform_date_ddmmyyyy(value: Any) -> str:
    """Format date as DD/MM/YYYY."""
    import pandas as pd

    if pd.isna(value):
        return ""

    try:
        dt = pd.to_datetime(value)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


@register_transform("date_mmddyyyy")
def transform_date_mmddyyyy(value: Any) -> str:
    """Format date as MM/DD/YYYY."""
    import pandas as pd

    if pd.isna(value):
        return ""

    try:
        dt = pd.to_datetime(value)
        return dt.strftime("%m/%d/%Y")
    except Exception:
        return str(value)


# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================


def apply_transform(transform_name: str, value: Any) -> Any:
    """
    Apply a registered transform to a value.

    Args:
        transform_name: Name of registered transform
        value: Value to transform

    Returns:
        Transformed value

    Raises:
        KeyError: If transform not found
    """
    if transform_name not in TRANSFORMS:
        raise KeyError(f"Unknown transform: '{transform_name}'")

    transform_fn = TRANSFORMS[transform_name]
    return transform_fn(value)


def list_transforms() -> list[str]:
    """Get list of registered transform names."""
    return sorted(TRANSFORMS.keys())


def get_transform_help() -> dict[str, str]:
    """Get help text for all transforms."""
    help_text = {}
    for name, func in TRANSFORMS.items():
        doc = func.__doc__ or "No description available"
        help_text[name] = doc.strip()
    return help_text
