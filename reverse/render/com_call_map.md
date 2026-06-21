# COM Call Map

Generated and maintained with:

`python tools\reverse_probe\scan_com_calls.py --markdown`

COM call names are candidates. Some offsets are shared by different interfaces,
so local context decides whether a row is `IDirectDraw`, `IDirectDrawSurface`,
or another COM object.

## High-Value Calls

| Address | Offset | Candidate method | Why it matters |
|---:|---:|---|---|
| `0x46d4a3` | `0x50` | `IDirectDraw::SetCooperativeLevel` | DirectDraw setup. |
| `0x46d4dd` | `0x18` | `IDirectDraw::CreateSurface` | First surface creation. |
| `0x4f0b1f` | `0x54` | `IDirectDraw::SetDisplayMode` | Primary display mode change. |
| `0x4f0f69` | `0x54` | `IDirectDraw::SetDisplayMode` | Display reset/resize path. |
| `0x4f8216` | `0x58` | `IDirectDrawSurface::GetSurfaceDesc` | Reads pitch/surface description. |
| `0x4f82a5` | `0x54` | `IDirectDrawSurface::GetPixelFormat` | Pixel format / conversion state, not display mode. |
| `0x4f0030` | `0x64` | `IDirectDrawSurface::Lock` | Locks `0x5dff98`, the CPU-drawn back/logical surface. |
| `0x4f0070` | `0x80` | `IDirectDrawSurface::Unlock` | Unlocks `0x5dff98`. |
| `0x4f03b0` | `0x14` | `IDirectDrawSurface::Blt` | Present path from `0x5dff98` to `0x5dff94`. |
| `0x4f0490` | `0x14` | `IDirectDrawSurface::Blt` | Clipped present path. |
| `0x4f0578` | `0x14` | `IDirectDrawSurface::Blt` | Clipped present path. |
| `0x4f05a9` | `0x1c` | `IDirectDrawSurface::BltFast` | Fast present path. |
| `0x4f0661` | `0x1c` | `IDirectDrawSurface::BltFast` | Clipped fast present path. |
| `0x4f0725` | `0x1c` | `IDirectDrawSurface::BltFast` | Clipped fast present path. |

## Next Scan Target

Find calls with surface offsets:

- `0x14`: `IDirectDrawSurface::Blt`
- `0x1c`: `IDirectDrawSurface::BltFast`
- `0x2c`: `IDirectDrawSurface::Flip`
- `0x64`: `IDirectDrawSurface::Lock`
- `0x80`: `IDirectDrawSurface::Unlock`

Those are the likely bridge between the 1024x768 logical UI canvas and the
larger DirectDraw display mode.
