# Surface Present And Blit Pseudocode

This document covers the high-value surface present path around `0x4f02d0`.

## Working Names

| Address | Working name | Evidence |
|---:|---|---|
| `0x4f0030` | `lock_back_surface()` | Calls surface method `+0x64` (`IDirectDrawSurface::Lock`) on `0x5dff98`. |
| `0x4f0070` | `unlock_back_surface()` | Calls surface method `+0x80` (`IDirectDrawSurface::Unlock`) on `0x5dff98`. |
| `0x4f02d0` | `present_dirty_rects()` | Calls `Blt`/`BltFast` from `0x5dff98` to `0x5dff94`, with clipping. |
| `0x4f03b0` | `Surface::Blt` call | Uses destination rect `0x75cf18`, source rect `0x75cf50`, source surface `0x5dff98`, destination surface `0x5dff94`. |
| `0x4f0490` | `Surface::Blt` call | Clipped dirty-rect variant. |
| `0x4f0578` | `Surface::Blt` call | Second clipped dirty-rect variant. |
| `0x4f05a9` | `Surface::BltFast` call | Fast path with direct x/y source arguments. |
| `0x4f0661` | `Surface::BltFast` call | Clipped fast path. |
| `0x4f0725` | `Surface::BltFast` call | Second clipped fast path. |

## Important Globals

| Address | Working name | Meaning |
|---:|---|---|
| `0x5dff94` | `g_primary_or_front_surface` | Destination surface for present calls. |
| `0x5dff98` | `g_back_or_logic_surface` | Source surface locked for CPU drawing and blitted to front. |
| `0x75cf18` | `g_dst_rect.left` | Destination rectangle used by `Blt`. |
| `0x75cf1c` | `g_dst_rect.top` | Destination rectangle used by `Blt`. |
| `0x75cf20` | `g_dst_rect.right` | Destination rectangle used by `Blt`. |
| `0x75cf24` | `g_dst_rect.bottom` | Destination rectangle used by `Blt`. |
| `0x75cf50` | `g_src_rect.left` | Source rectangle used by `Blt`. |
| `0x75cf54` | `g_src_rect.top` | Source rectangle used by `Blt`. |
| `0x75cf58` | `g_src_rect.right` | Source rectangle used by `Blt`. |
| `0x75cf5c` | `g_src_rect.bottom` | Source rectangle used by `Blt`. |
| `0x75cf68..0x75cf74` | `g_clip_rect` | Clipped source rectangle for dirty rect paths. |
| `0x734c08` | `g_client_width` | Clip boundary used by present logic. |
| `0x734c14` | `g_client_height` | Clip boundary used by present logic. |
| `0x75cf78` | `g_dest_offset_y` | Added to destination top/bottom. |
| `0x75cf7c` | `g_dest_offset_x` | Added to destination left/right. |
| `0x75cf80` | `g_present_width` | Set from mode table after `SetDisplayMode`. |
| `0x75cf84` | `g_present_height` | Set from mode table after `SetDisplayMode`. |

## Surface Creation Around `0x4f0c99`

The larger display mode is not the only size-bearing path. After setting display
mode, the game creates two important surfaces:

```c
// At 0x4f0ce0.
DDSURFACEDESC desc = {0};
desc.dwSize = 0x7c;
desc.dwFlags = 1;
desc.ddsCaps.dwCaps = 0x4200;
g_ddraw->CreateSurface(&desc, &g_primary_or_front_surface, NULL);

// At 0x4f0de0.
DDSURFACEDESC back = {0};
back.dwSize = 0x7c;
back.dwFlags = 7;
back.dwHeight = mode_heights[mode_index];
back.dwWidth = mode_widths[mode_index];
back.ddsCaps.dwCaps = variable_caps;
g_ddraw->CreateSurface(&back, &g_back_or_logic_surface, NULL);
```

This means the DirectDraw back surface is already being created at the patched
mode size in the 1600x1200 test. The reason the visible UI remains 1024x768 is
therefore likely upstream: the game draws 1024x768 UI content into the surface,
or only marks/blits a 1024x768 dirty region.

## `present_dirty_rects()` Pseudocode

Address range: approximately `0x4f02d0` to `0x4f0774`.

```c
void present_dirty_rects(int x, int y)
{
    if (!g_directdraw_ready || !g_back_or_logic_surface) {
        return;
    }

    if (g_surface_locked_ptr) {
        unlock_back_surface();
    }

    if (present_mode == PRESENT_BLT_RECT) {
        dst.left   = g_dest_offset_y + y;
        dst.top    = g_dest_offset_x + x;
        dst.right  = g_present_width + y;
        dst.bottom = g_present_height + x;

        src = g_source_rect;
        g_primary_or_front_surface->Blt(&dst, g_back_or_logic_surface, &src, DDBLT_WAIT, NULL);
        return;
    }

    if (present_mode == PRESENT_BLTFAST) {
        g_primary_or_front_surface->BltFast(x, y, g_back_or_logic_surface, &src, flags);
        return;
    }

    // Other branches clip dirty rectangles against g_client_width/g_client_height,
    // then call either Blt or BltFast.
}
```

## Interpretation For The 1600x1200 Test

- The back surface creation path uses the patched mode size.
- The present path can blit larger rectangles because `0x75cf80/0x75cf84` are set from the mode table.
- The remaining 1024x768 behavior likely comes from one or more higher-level UI draw bounds:
  - dirty rect globals such as `0x57d078..0x57d084`;
  - client-size globals `0x734c08/0x734c14`;
  - resource dimensions in `GRAPH`, `EMG`, `XMG`, or layout constants;
  - main menu draw code that only paints a 1024x768 region.

## Next Reverse Target

Track writes to:

- `0x734c08`
- `0x734c14`
- `0x57d078`
- `0x57d07c`
- `0x57d080`
- `0x57d084`
- `0x75cf38`
- `0x75cf3c`

These values influence clipping and source/destination rectangles before the
final surface blit.
