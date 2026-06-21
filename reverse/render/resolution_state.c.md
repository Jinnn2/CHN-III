# Resolution State And Logical Offsets

This document tracks the globals that connect the mode table, logical drawing
area, dirty rectangles, and present path.

## `apply_resolution_mode(index, update_screen)`

Address range: approximately `0x4c2da0` to `0x4c2ef4`.

This routine is important because it writes the client/logical size globals used
by the present path.

## Pseudocode

```c
void apply_resolution_mode(int index, bool skip_redraw)
{
    if (index == mode_index) {
        return;
    }

    uint32_t width = mode_widths[index];       // 0x589410[index]
    uint32_t height = mode_heights[index];     // 0x58941c[index]

    mode_index = index;                        // 0x58940c
    g_client_width = width;                    // 0x734c08
    g_client_height = height;                  // 0x734c14
    g_max_x = width - 1;                       // 0x588b98
    g_max_y = height - 1;                      // 0x588b9c
    g_framebuffer_bytes = (width + 1) * (height + 1) * 2; // 0x734c1c

    if (!skip_redraw) {
        begin_redraw_or_lock();
    }

    set_mode_by_index(mode_index);             // 0x4f09d0

    if (!skip_redraw) {
        end_redraw_or_unlock();
    }

    recreate_or_resize_aux_surface();          // 0x4c2c20

    g_center_offset_x = (width - 800) / 2;      // 0x734c10
    g_center_offset_y = (height - 600) / 2;     // 0x734c0c

    clamp_open_windows_to_new_bounds();
}
```

## Key Finding

The game is not purely 1024x768 internally. It explicitly computes offsets from
an `800x600` baseline:

```c
g_center_offset_x = (width - 800) / 2;
g_center_offset_y = (height - 600) / 2;
```

For known modes:

| Mode | Size | Offset from 800x600 |
|---|---:|---:|
| 0 | 800x600 | 0, 0 |
| 1 | 1024x768 | 112, 84 |
| 2 | 1280x1024 | 240, 212 |
| test | 1600x1200 | 400, 300 |

This explains why higher internal display modes can run while UI content appears
at a fixed logical size: some interface elements are probably still painted from
fixed-size resources or fixed dirty rectangles, but the coordinate system has
partial support for larger canvases.

## Active Present Bounds

| Address | Meaning |
|---:|---|
| `0x734c08` | Active logical/client width. |
| `0x734c14` | Active logical/client height. |
| `0x734c10` | Horizontal center offset from 800-wide baseline. |
| `0x734c0c` | Vertical center offset from 600-high baseline. |
| `0x734c1c` | Approximate framebuffer byte count. |
| `0x588b98` | Maximum x index. |
| `0x588b9c` | Maximum y index. |

## Dirty Rect Writers

Observed dirty rect globals:

| Address | Writer | Meaning |
|---:|---:|---|
| `0x57d080` | `0x48b752` | Dirty rect x or left coordinate. |
| `0x57d084` | `0x48b75a` | Dirty rect y or top coordinate. |

These values are consumed by `present_dirty_rects()` at `0x4f02d0`.

## Next Targets

1. Reverse `0x48b4f0`, `0x48b5a0`, `0x48b6e0`, and `0x48b780`; these appear to be cursor/dirty-rect update helpers.
2. Find `MAINMENU.EMG` and `MAINMENU.XMG` load/draw callers to see whether main menu content is fixed at 1024x768 or centered within the active logical area.
3. Track usage of `0x734c10` and `0x734c0c`; those are likely layout offsets used to center old 800x600-era UI.
