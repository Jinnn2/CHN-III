# `init_directdraw_runtime()` Pseudocode

Address range: approximately `0x46d310` to `0x46d665`.

This function is not original source. It is a working reconstruction from strings,
imports, and COM vtable calls.

## Evidence

- Error strings near `0x574250` to `0x57438c` include:
  - `DirectDrawCreate`
  - `DDRAW.DLL`
  - `Couldn't LoadLibrary DDraw`
  - `Couldn't create DDraw`
  - `Couldn't QI DDraw2`
  - `Couldn't Set coop level`
  - `Couldn't CreateSurface`
- `0x46d4a3` calls `[edx + 0x50]`, consistent with `IDirectDraw::SetCooperativeLevel`.
- `0x46d4dd` calls `[edx + 0x18]`, consistent with `IDirectDraw::CreateSurface`.

## Pseudocode

```c
int init_directdraw_runtime(void)
{
    HMODULE ddraw = LoadLibraryA("DDRAW.DLL");
    if (!ddraw) {
        return 0;
    }

    DirectDrawCreateFn create = GetProcAddress(ddraw, "DirectDrawCreate");
    if (!create) {
        FreeLibrary(ddraw);
        show_error("Couldn't LoadLibrary DDraw");
        return 0;
    }

    IDirectDraw *ddraw1 = NULL;
    HRESULT hr = create(NULL, &ddraw1, NULL);
    if (FAILED(hr)) {
        show_error("Couldn't create DDraw");
        return 0;
    }

    IDirectDraw2 *ddraw2 = NULL;
    hr = ddraw1->QueryInterface(IID_IDirectDraw2, (void **)&ddraw2);
    ddraw1->Release();
    if (FAILED(hr)) {
        show_error("Couldn't QI DDraw2");
        return 0x100;
    }

    hr = ddraw2->SetCooperativeLevel(hwnd, flags);
    if (FAILED(hr)) {
        ddraw2->Release();
        show_error("Couldn't Set coop level");
        return 0;
    }

    DDSURFACEDESC desc = {0};
    desc.dwSize = sizeof(desc);       // observed: 0x6c
    desc.dwFlags = DDSD_CAPS;         // observed: 1
    desc.ddsCaps.dwCaps = 0x200;      // likely primary-surface caps in this build

    IDirectDrawSurface *surface = NULL;
    hr = ddraw2->CreateSurface(&desc, &surface, NULL);
    if (FAILED(hr)) {
        ddraw2->Release();
        show_error("Couldn't CreateSurface");
        return 0;
    }

    // Additional QueryInterface / DirectMusic / DirectInput initialization follows.
    return nonzero_on_success;
}
```

## Notes

- This function creates the first DirectDraw surface, but the current 1024x768 UI
  limit is probably not here. The observed `DDSURFACEDESC` does not directly set
  width and height at this call site.
- The next target is to find later offscreen surface creation and blit paths.
