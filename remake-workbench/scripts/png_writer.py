#!/usr/bin/env python3
import binascii
import struct
import zlib


def png_chunk(kind, payload):
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)


def write_png_rgb(path, width, height, pixels):
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        start = y * stride
        raw.extend(pixels[start:start + stride])
    payload = [
        b"\x89PNG\r\n\x1a\n",
        png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
        png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9)),
        png_chunk(b"IEND", b""),
    ]
    path.write_bytes(b"".join(payload))
