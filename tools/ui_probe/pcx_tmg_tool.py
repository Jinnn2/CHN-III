#!/usr/bin/env python3
import argparse
import struct
from pathlib import Path


def _le16(data, offset):
    return data[offset] | (data[offset + 1] << 8)


def _put_le16(data, offset, value):
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF


def read_pcx24(path):
    raw = Path(path).read_bytes()
    if len(raw) < 128 or raw[0] != 0x0A:
        raise ValueError(f"{path} is not a PCX/TMG file")

    header = bytearray(raw[:128])
    xmin = _le16(header, 4)
    ymin = _le16(header, 6)
    xmax = _le16(header, 8)
    ymax = _le16(header, 10)
    width = xmax - xmin + 1
    height = ymax - ymin + 1
    planes = header[65]
    bpp = header[3]
    bytes_per_line = _le16(header, 66)

    if bpp != 8 or planes != 3:
        raise ValueError(f"{path} is {planes} planes / {bpp} bpp; expected 24-bit PCX")

    expected = height * planes * bytes_per_line
    decoded = bytearray()
    i = 128
    while i < len(raw) and len(decoded) < expected:
        byte = raw[i]
        i += 1
        if byte >= 0xC0:
            count = byte & 0x3F
            if i >= len(raw):
                break
            decoded.extend([raw[i]] * count)
            i += 1
        else:
            decoded.append(byte)

    if len(decoded) < expected:
        raise ValueError(f"{path} ended early while decoding")

    rgb = bytearray(width * height * 3)
    row_size = planes * bytes_per_line
    for y in range(height):
        row = y * row_size
        r = decoded[row:row + bytes_per_line]
        g = decoded[row + bytes_per_line:row + (bytes_per_line * 2)]
        b = decoded[row + (bytes_per_line * 2):row + (bytes_per_line * 3)]
        out = y * width * 3
        for x in range(width):
            rgb[out + x * 3 + 0] = r[x]
            rgb[out + x * 3 + 1] = g[x]
            rgb[out + x * 3 + 2] = b[x]

    return header, width, height, bytes_per_line, bytes(rgb)


def write_bmp24(path, width, height, rgb):
    row_stride = ((width * 3 + 3) // 4) * 4
    pixel_size = row_stride * height
    file_size = 14 + 40 + pixel_size
    out = bytearray()
    out += b"BM"
    out += struct.pack("<IHHI", file_size, 0, 0, 54)
    out += struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, pixel_size, 2835, 2835, 0, 0)
    padding = b"\x00" * (row_stride - width * 3)
    for y in range(height - 1, -1, -1):
        row = y * width * 3
        for x in range(width):
            r, g, b = rgb[row + x * 3:row + x * 3 + 3]
            out += bytes((b, g, r))
        out += padding
    Path(path).write_bytes(out)


def read_bmp24(path):
    raw = Path(path).read_bytes()
    if raw[:2] != b"BM":
        raise ValueError(f"{path} is not a BMP file")
    pixel_offset = struct.unpack_from("<I", raw, 10)[0]
    dib_size = struct.unpack_from("<I", raw, 14)[0]
    if dib_size < 40:
        raise ValueError("unsupported BMP DIB header")
    width, height, planes, bpp, compression = struct.unpack_from("<iiHHI", raw, 18)
    if planes != 1 or bpp != 24 or compression != 0:
        raise ValueError("only uncompressed 24-bit BMP is supported")

    flip = height > 0
    height = abs(height)
    row_stride = ((width * 3 + 3) // 4) * 4
    rgb = bytearray(width * height * 3)
    for src_y in range(height):
        y = height - 1 - src_y if flip else src_y
        src = pixel_offset + src_y * row_stride
        dst = y * width * 3
        for x in range(width):
            b, g, r = raw[src + x * 3:src + x * 3 + 3]
            rgb[dst + x * 3 + 0] = r
            rgb[dst + x * 3 + 1] = g
            rgb[dst + x * 3 + 2] = b
    return width, height, bytes(rgb)


def _rle_encode(data):
    out = bytearray()
    i = 0
    while i < len(data):
        value = data[i]
        count = 1
        while i + count < len(data) and data[i + count] == value and count < 63:
            count += 1
        if count > 1 or value >= 0xC0:
            out.append(0xC0 | count)
            out.append(value)
        else:
            out.append(value)
        i += count
    return out


def write_pcx24(path, template_path, bmp_path):
    header, old_width, old_height, old_bpl, _ = read_pcx24(template_path)
    width, height, rgb = read_bmp24(bmp_path)
    if width != old_width or height != old_height:
        raise ValueError(f"BMP is {width}x{height}; template is {old_width}x{old_height}")

    bytes_per_line = width if width % 2 == 0 else width + 1
    _put_le16(header, 66, bytes_per_line)
    planes = header[65]
    encoded = bytearray(header)
    pad = b"\x00" * (bytes_per_line - width)
    for y in range(height):
        row = rgb[y * width * 3:(y + 1) * width * 3]
        for channel in range(planes):
            plane = bytearray(row[channel::3])
            plane += pad
            encoded += _rle_encode(plane)
    Path(path).write_bytes(encoded)


def read_pcx24_info(path):
    raw = Path(path).read_bytes()
    if len(raw) < 128 or raw[0] != 0x0A:
        raise ValueError(f"{path} is not a PCX/TMG file")

    xmin = _le16(raw, 4)
    ymin = _le16(raw, 6)
    xmax = _le16(raw, 8)
    ymax = _le16(raw, 10)
    width = xmax - xmin + 1
    height = ymax - ymin + 1
    return {
        "width": width,
        "height": height,
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
        "bpp": raw[3],
        "planes": raw[65],
        "bytes_per_line": _le16(raw, 66),
    }


def cmd_export(args):
    header, width, height, bpl, rgb = read_pcx24(args.input)
    write_bmp24(args.output, width, height, rgb)
    print(f"exported {args.input} -> {args.output} ({width}x{height}, bpl={bpl})")


def cmd_import(args):
    write_pcx24(args.output, args.template, args.input)
    print(f"imported {args.input} -> {args.output} using {args.template}")


def cmd_info(args):
    for input_path in args.input:
        info = read_pcx24_info(input_path)
        print(
            f"{input_path}: {info['width']}x{info['height']}, "
            f"bbox=({info['xmin']},{info['ymin']})-({info['xmax']},{info['ymax']}), "
            f"bpp={info['bpp']}, planes={info['planes']}, bpl={info['bytes_per_line']}"
        )


def main():
    parser = argparse.ArgumentParser(description="Export/import 24-bit PCX-like .TMG UI backgrounds.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    info = sub.add_parser("info")
    info.add_argument("input", nargs="+")
    info.set_defaults(func=cmd_info)
    export = sub.add_parser("export")
    export.add_argument("input")
    export.add_argument("output")
    export.set_defaults(func=cmd_export)
    imp = sub.add_parser("import")
    imp.add_argument("template")
    imp.add_argument("input")
    imp.add_argument("output")
    imp.set_defaults(func=cmd_import)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
