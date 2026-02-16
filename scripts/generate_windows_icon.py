#!/usr/bin/env python3
"""Generate OCC desktop branding icon assets without external dependencies."""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path


def _png_chunk(tag: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def build_brand_png(width: int = 256, height: int = 256) -> bytes:
    if width <= 0 or height <= 0:
        raise ValueError("Invalid icon dimensions.")

    rows = bytearray()
    cx = width // 2
    cy = height // 2

    for y in range(height):
        rows.append(0)  # PNG filter type 0
        for x in range(width):
            r = int(8 + (24 * y / max(height - 1, 1)))
            g = int(24 + (92 * x / max(width - 1, 1)))
            b = int(44 + (146 * y / max(height - 1, 1)))
            a = 255

            dx = x - cx
            dy = y - cy
            radius = (dx * dx + dy * dy) ** 0.5

            # Bright ring around the center "O"
            if width * 0.22 <= radius <= width * 0.34:
                r, g, b = 56, 189, 248

            # Inner disk
            if radius < width * 0.20:
                r, g, b = 15, 23, 42

            # Horizontal bar across the center to stylize OCC glyph
            if abs(dy) < max(2, height // 28) and abs(dx) < width * 0.28:
                r, g, b = 245, 248, 255

            rows.extend((r, g, b, a))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    data = zlib.compress(bytes(rows), level=9)
    signature = b"\x89PNG\r\n\x1a\n"
    return (
        signature
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", data)
        + _png_chunk(b"IEND", b"")
    )


def write_ico_from_png(png_data: bytes, out_path: Path, width: int, height: int) -> None:
    if not png_data:
        raise ValueError("PNG data is empty.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    width_field = 0 if width >= 256 else width
    height_field = 0 if height >= 256 else height

    icon_dir = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        width_field,
        height_field,
        0,
        0,
        1,
        32,
        len(png_data),
        6 + 16,
    )
    out_path.write_bytes(icon_dir + entry + png_data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OCC desktop icon assets (PNG + ICO).")
    parser.add_argument("--ico-out", default="build/occ_desktop.ico", help="Output ICO path.")
    parser.add_argument("--png-out", default="", help="Optional output PNG path.")
    parser.add_argument("--size", type=int, default=256, help="Square size in pixels.")
    args = parser.parse_args()

    size = int(args.size)
    png = build_brand_png(size, size)
    ico_path = Path(args.ico_out).resolve()
    write_ico_from_png(png, ico_path, size, size)

    if args.png_out:
        png_path = Path(args.png_out).resolve()
        png_path.parent.mkdir(parents=True, exist_ok=True)
        png_path.write_bytes(png)

    print(ico_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
