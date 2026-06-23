#!/usr/bin/env python3
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def rgb565_to_rgb(pixel):
    red = (pixel >> 11) & 0x1F
    green = (pixel >> 5) & 0x3F
    blue = pixel & 0x1F
    return (
        (red << 3) | (red >> 2),
        (green << 2) | (green >> 4),
        (blue << 3) | (blue >> 2),
    )


def rgb555_to_rgb(pixel):
    red = (pixel >> 10) & 0x1F
    green = (pixel >> 5) & 0x1F
    blue = pixel & 0x1F
    return (
        (red << 3) | (red >> 2),
        (green << 3) | (green >> 2),
        (blue << 3) | (blue >> 2),
    )


def resolve_workspace_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return ROOT / path


def parse_emg(path, max_groups=None):
    data = resolve_workspace_path(path).read_bytes()
    if len(data) < 2:
        raise ValueError("EMG file is too short")
    group_count = struct.unpack_from("<H", data, 0)[0]
    if max_groups is not None and group_count > max_groups:
        raise ValueError(f"EMG group count {group_count} exceeds max {max_groups}")
    offset = 2
    groups = []
    for index in range(group_count):
        if offset + 2 > len(data):
            raise ValueError(f"group {index} header overruns file")
        segment_count = struct.unpack_from("<H", data, offset)[0]
        group_offset = offset
        offset += 2
        segments = []
        min_x = min_y = 1 << 30
        max_x = max_y = -(1 << 30)
        pixel_count = 0
        for _ in range(segment_count):
            if offset + 6 > len(data):
                raise ValueError(f"group {index} segment header overruns file")
            x, y, width = struct.unpack_from("<HHH", data, offset)
            offset += 6
            byte_width = width * 2
            if offset + byte_width > len(data):
                raise ValueError(f"group {index} segment pixels overrun file")
            pixels = struct.unpack_from("<" + "H" * width, data, offset) if width else ()
            offset += byte_width
            segments.append({"x": x, "y": y, "width": width, "pixels": pixels})
            if width:
                min_x = min(min_x, x)
                max_x = max(max_x, x + width - 1)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                pixel_count += width
        if pixel_count:
            bbox = [min_x, min_y, max_x, max_y]
        else:
            bbox = [0, 0, -1, -1]
        groups.append({
            "index": index,
            "offset": group_offset,
            "segment_count": segment_count,
            "pixel_count": pixel_count,
            "bbox": bbox,
            "segments": segments,
        })
    if offset != len(data):
        raise ValueError(f"EMG trailing bytes: {len(data) - offset}")
    return {"path": str(resolve_workspace_path(path)), "group_count": group_count, "groups": groups}


def sprite_dimensions(sprite):
    min_x, min_y, max_x, max_y = sprite["bbox"]
    if max_x < min_x or max_y < min_y:
        return 0, 0
    return max_x - min_x + 1, max_y - min_y + 1


def draw_sprite(canvas, canvas_width, canvas_height, sprite, x, y, color_mode="565"):
    converter = rgb565_to_rgb if color_mode == "565" else rgb555_to_rgb
    for segment in sprite["segments"]:
        dst_y = y + segment["y"]
        if dst_y < 0 or dst_y >= canvas_height:
            continue
        dst_x = x + segment["x"]
        start = 0
        end = segment["width"]
        if dst_x < 0:
            start = -dst_x
            dst_x = 0
        if dst_x + (end - start) > canvas_width:
            end = start + (canvas_width - dst_x)
        if end <= start:
            continue
        pos = (dst_y * canvas_width + dst_x) * 3
        for pixel in segment["pixels"][start:end]:
            canvas[pos:pos + 3] = bytes(converter(pixel))
            pos += 3
