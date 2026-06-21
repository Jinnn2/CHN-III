# Display Mode Pseudocode

This document covers the two confirmed `IDirectDraw::SetDisplayMode` call sites.

## Mode Table

Original values:

```c
uint32_t mode_index = 1;                  // VA 0x58940c
uint32_t mode_widths[3]  = {800, 1024, 1280};  // VA 0x589410
uint32_t mode_heights[3] = {600, 768, 1024};   // VA 0x58941c
```

Known test builds:

- `China2EX_modtest.exe`: `mode_index = 2`, mode 2 remains `1280x1024`.
- `China2EX_modtest_1600x1200.exe`: `mode_index = 2`, mode 2 becomes `1600x1200`.

## `set_display_mode_from_mode_table()`

Primary call site: `0x4f0b1f`.

```c
HRESULT set_display_mode_from_mode_table(void)
{
    uint32_t index = *(uint32_t *)0x58940c;
    uint32_t width = ((uint32_t *)0x589410)[index];
    uint32_t height = ((uint32_t *)0x58941c)[index];

    HRESULT hr = g_ddraw->SetDisplayMode(width, height, 16, 0, 0);
    if (FAILED(hr)) {
        report_set_display_mode_failure(hr);
        return hr;
    }

    *(uint32_t *)0x75cf7c = 0;
    *(uint32_t *)0x75cf78 = 0;
    *(uint32_t *)0x75cf80 = width;
    *(uint32_t *)0x75cf84 = height;
    return DD_OK;
}
```

## `reset_or_resize_display_mode()`

Secondary call site: `0x4f0f69`.

```c
HRESULT reset_or_resize_display_mode(void)
{
    uint32_t width = *(uint32_t *)0x589418;
    uint32_t height = *(uint32_t *)0x589424;

    HRESULT hr = g_ddraw->SetDisplayMode(width, height, 16, 0, 0);

    // The function then computes window/client rectangles using USER32 APIs,
    // including SetRect and AdjustWindowRectEx.
    adjust_host_window_rect();
    return hr;
}
```

## Interpretation

- The display mode path is successfully patchable.
- The 1600x1200 test showing a 1024x768 UI means the UI has a separate logical
  canvas or blit path that still uses 1024x768 content.
- The next reverse target is not another `SetDisplayMode` call. It is the surface
  or memory-buffer path that creates, draws, and blits the UI canvas.
