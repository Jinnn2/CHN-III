#!/usr/bin/env python3
import argparse
import json
import struct
from pathlib import Path


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def parse_emg(path):
    data = Path(path).read_bytes()
    if len(data) < 2:
        raise ValueError("file too small")

    group_count = u16(data, 0)
    offset = 2
    groups = []
    for group_index in range(group_count):
        if offset + 2 > len(data):
            raise ValueError(f"group {group_index}: missing frame count at 0x{offset:x}")
        frame_count = u16(data, offset)
        group_offset = offset
        offset += 2
        frames = []
        for frame_index in range(frame_count):
            if offset + 6 > len(data):
                raise ValueError(f"group {group_index} frame {frame_index}: missing header at 0x{offset:x}")
            x, y, width = struct.unpack_from("<HHH", data, offset)
            frame_offset = offset
            offset += 6
            payload_size = width * 2
            if offset + payload_size > len(data):
                raise ValueError(
                    f"group {group_index} frame {frame_index}: payload overruns file at 0x{offset:x}"
                )
            payload = data[offset:offset + payload_size]
            offset += payload_size
            frames.append({
                "index": frame_index,
                "offset": frame_offset,
                "x": x,
                "y": y,
                "width_words": width,
                "payload_size": payload_size,
                "payload_hex": payload[:32].hex(),
            })
        groups.append({
            "index": group_index,
            "offset": group_offset,
            "frame_count": frame_count,
            "frames": frames,
        })

    return {
        "path": str(path),
        "size": len(data),
        "group_count": group_count,
        "parsed_size": offset,
        "trailing_size": len(data) - offset,
        "groups": groups,
    }


def unpack_frame_pixels(payload):
    pixels = []
    for i in range(0, len(payload), 2):
        value = payload[i] | (payload[i + 1] << 8)
        r = ((value >> 11) & 0x1f) * 255 // 31
        g = ((value >> 5) & 0x3f) * 255 // 63
        b = (value & 0x1f) * 255 // 31
        pixels.append((r, g, b))
    return pixels


def write_bmp24(path, width, height, rgb):
    row_stride = ((width * 3 + 3) // 4) * 4
    pixel_size = row_stride * height
    out = bytearray()
    out += b"BM"
    out += struct.pack("<IHHI", 14 + 40 + pixel_size, 0, 0, 54)
    out += struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, pixel_size, 2835, 2835, 0, 0)
    pad = b"\x00" * (row_stride - width * 3)
    for y in range(height - 1, -1, -1):
        row = y * width * 3
        for x in range(width):
            r, g, b = rgb[row + x * 3:row + x * 3 + 3]
            out += bytes((b, g, r))
        out += pad
    Path(path).write_bytes(out)


def render_group_sheet(input_path, output_path, group_index, columns=8, scale=1):
    data = Path(input_path).read_bytes()
    parsed = parse_emg(input_path)
    group = parsed["groups"][group_index]
    frames = group["frames"]
    if not frames:
        raise ValueError("group has no frames")

    widths = [frame["width_words"] for frame in frames]
    max_w = max(widths)
    cell_w = max_w
    cell_h = 1
    rows = (len(frames) + columns - 1) // columns
    sheet_w = cell_w * columns
    sheet_h = cell_h * rows
    rgb = bytearray([0x20, 0x20, 0x20] * sheet_w * sheet_h)

    for idx, frame in enumerate(frames):
        payload_offset = frame["offset"] + 6
        payload = data[payload_offset:payload_offset + frame["payload_size"]]
        pixels = unpack_frame_pixels(payload)
        col = idx % columns
        row = idx // columns
        dst_x = col * cell_w
        dst_y = row * cell_h
        for x, (r, g, b) in enumerate(pixels):
            p = ((dst_y * sheet_w) + dst_x + x) * 3
            rgb[p:p + 3] = bytes((r, g, b))

    if scale != 1:
        scaled_w = sheet_w * scale
        scaled_h = sheet_h * scale
        scaled = bytearray(scaled_w * scaled_h * 3)
        for y in range(sheet_h):
            for x in range(sheet_w):
                src = (y * sheet_w + x) * 3
                for yy in range(scale):
                    for xx in range(scale):
                        dst = ((y * scale + yy) * scaled_w + x * scale + xx) * 3
                        scaled[dst:dst + 3] = rgb[src:src + 3]
        sheet_w, sheet_h, rgb = scaled_w, scaled_h, scaled

    write_bmp24(output_path, sheet_w, sheet_h, bytes(rgb))


def cmd_info(args):
    parsed = parse_emg(args.input)
    groups = parsed["groups"]
    print(f"{parsed['path']}: groups={parsed['group_count']} size={parsed['size']} parsed={parsed['parsed_size']} trailing={parsed['trailing_size']}")
    for group in groups[:args.limit]:
        widths = [frame["width_words"] for frame in group["frames"]]
        print(
            f"  group {group['index']:03d} @0x{group['offset']:04x}: "
            f"frames={group['frame_count']} widths={widths[:12]}"
        )


def cmd_json(args):
    parsed = parse_emg(args.input)
    if args.no_payload:
        for group in parsed["groups"]:
            for frame in group["frames"]:
                frame.pop("payload_hex", None)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))


def cmd_sheet(args):
    render_group_sheet(args.input, args.output, args.group, args.columns, args.scale)
    print(f"wrote {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Probe China2 EMG resource containers.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    info = sub.add_parser("info")
    info.add_argument("input")
    info.add_argument("--limit", type=int, default=20)
    info.set_defaults(func=cmd_info)

    js = sub.add_parser("json")
    js.add_argument("input")
    js.add_argument("--no-payload", action="store_true")
    js.set_defaults(func=cmd_json)

    sheet = sub.add_parser("sheet")
    sheet.add_argument("input")
    sheet.add_argument("output")
    sheet.add_argument("--group", type=int, default=0)
    sheet.add_argument("--columns", type=int, default=8)
    sheet.add_argument("--scale", type=int, default=4)
    sheet.set_defaults(func=cmd_sheet)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
