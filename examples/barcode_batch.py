"""
Barcode batch generation - Generate 10,000 GS1-128 barcodes in parallel.

Run with: modal run examples/barcode_batch.py
"""

import modal
from vdp_modal import vdp_app


def main():
    """Generate 10,000 GS1-128 barcodes."""

    # Generate serial numbers
    NUM_BARCODES = 10000
    serial_numbers = [f"1234567890{i:06d}" for i in range(NUM_BARCODES)]

    print(f"Generating {len(serial_numbers):,} GS1-128 barcodes in parallel")

    from vdp_modal.app import batch_generate_barcodes

    with modal.runner.deploy_app(vdp_app):
        # Generate barcodes in parallel
        barcodes = batch_generate_barcodes.remote(
            serial_numbers=serial_numbers,
            barcode_type="gs1-128",
            dpi=300,
        )

        print(f"\n=== Generation Complete ===")
        print(f"Total Barcodes: {len(barcodes):,}")
        print(f"Average Size: {sum(len(b) for b in barcodes) // len(barcodes):,} bytes")

        # Save first 10 as samples
        import os

        os.makedirs("/tmp/barcodes", exist_ok=True)

        for i, barcode_bytes in enumerate(barcodes[:10]):
            output_path = f"/tmp/barcodes/barcode_{i:06d}.png"
            with open(output_path, "wb") as f:
                f.write(barcode_bytes)

        print(f"\nFirst 10 barcodes saved to: /tmp/barcodes/")
        print("✓ Success!")


if __name__ == "__main__":
    main()
