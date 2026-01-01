"""Tests for barcode generation."""

import pytest
from vdp_modal.barcode import (
    generate_barcode,
    generate_qr_code,
    generate_gs1_128,
    batch_generate_barcodes,
)


def test_generate_code128():
    """Test Code128 barcode generation."""
    result = generate_barcode("TEST123", barcode_type="code128")
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result.startswith(b"\x89PNG")  # PNG header


def test_generate_qr_code():
    """Test QR code generation."""
    result = generate_qr_code("https://example.com")
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result.startswith(b"\x89PNG")


def test_generate_gs1_128():
    """Test GS1-128 barcode generation."""
    result = generate_gs1_128("01", "12345678901234")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_batch_generate():
    """Test batch barcode generation."""
    data_list = [f"SERIAL-{i:04d}" for i in range(10)]
    results = batch_generate_barcodes(data_list, barcode_type="code128")

    assert len(results) == 10
    assert all(isinstance(r, bytes) for r in results)
    assert all(len(r) > 0 for r in results)


def test_different_barcode_types():
    """Test different barcode types."""
    types = ["code128", "code39", "qr"]

    for barcode_type in types:
        result = generate_barcode("TEST", barcode_type=barcode_type)
        assert isinstance(result, bytes)
        assert len(result) > 0
