#include "app.h"

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *kWindowClassName = "China2EXRebuildWindow";
static const char *kWindowTitle = "China2EX Rebuild Workbench";

typedef struct TmgHeader {
    unsigned char manufacturer;
    unsigned char version;
    unsigned char encoding;
    unsigned char bits_per_pixel;
    uint16_t x_min;
    uint16_t y_min;
    uint16_t x_max;
    uint16_t y_max;
    unsigned char reserved_0[54];
    unsigned char planes;
    uint16_t bytes_per_line;
    unsigned char reserved_1[60];
} TmgHeader;

static void LogLine(const char *text)
{
    OutputDebugStringA(text);
    OutputDebugStringA("\r\n");
}

static void FreeTmgImage(TmgImage *image)
{
    if (image->pixels != NULL) {
        free(image->pixels);
        image->pixels = NULL;
    }
    image->width = 0;
    image->height = 0;
}

static DWORD Get_Game_Tick(void)
{
    return GetTickCount();
}

static int LoadFileBytes(const char *path, unsigned char **out_bytes, size_t *out_size)
{
    FILE *file;
    long size;
    unsigned char *bytes;

    *out_bytes = NULL;
    *out_size = 0;

    file = fopen(path, "rb");
    if (file == NULL) {
        return 0;
    }
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return 0;
    }
    size = ftell(file);
    if (size < 0 || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return 0;
    }

    bytes = (unsigned char *)malloc((size_t)size);
    if (bytes == NULL) {
        fclose(file);
        return 0;
    }
    if (fread(bytes, 1, (size_t)size, file) != (size_t)size) {
        free(bytes);
        fclose(file);
        return 0;
    }

    fclose(file);
    *out_bytes = bytes;
    *out_size = (size_t)size;
    return 1;
}

static int DecodePcxRle(const unsigned char *src, size_t src_size, unsigned char *dst, size_t dst_size)
{
    size_t src_index = 0;
    size_t dst_index = 0;

    while (src_index < src_size && dst_index < dst_size) {
        unsigned char value = src[src_index++];
        if ((value & 0xC0u) == 0xC0u) {
            size_t run_length = (size_t)(value & 0x3Fu);
            unsigned char run_value;
            size_t i;

            if (src_index >= src_size) {
                return 0;
            }
            run_value = src[src_index++];
            if (dst_index + run_length > dst_size) {
                return 0;
            }
            for (i = 0; i < run_length; ++i) {
                dst[dst_index++] = run_value;
            }
        } else {
            dst[dst_index++] = value;
        }
    }

    return dst_index == dst_size;
}

static unsigned int ExpandRgbToXrgb32(unsigned char red, unsigned char green, unsigned char blue)
{
    return ((unsigned int)red << 16) | ((unsigned int)green << 8) | (unsigned int)blue;
}

static int LoadTmgBackground(const char *name, TmgImage *out_image)
{
    char path[MAX_PATH];
    unsigned char *file_bytes = NULL;
    unsigned char *planar_bytes = NULL;
    size_t file_size = 0;
    size_t decoded_size;
    TmgHeader header;
    unsigned int width;
    unsigned int height;
    unsigned int y;

    snprintf(path, sizeof(path), "..\\GRAPH\\%s.TMG", name);
    FreeTmgImage(out_image);

    if (!LoadFileBytes(path, &file_bytes, &file_size) || file_size < sizeof(TmgHeader)) {
        LogLine("LoadTmgBackground: failed to read TMG file");
        return 0;
    }

    memcpy(&header, file_bytes, sizeof(header));
    width = (unsigned int)(header.x_max - header.x_min + 1u);
    height = (unsigned int)(header.y_max - header.y_min + 1u);

    if (header.manufacturer != 0x0A || header.version != 5 || header.encoding != 1 ||
        header.bits_per_pixel != 8 || header.planes != 3 || header.bytes_per_line < width) {
        free(file_bytes);
        LogLine("LoadTmgBackground: unsupported TMG header");
        return 0;
    }

    decoded_size = (size_t)header.bytes_per_line * (size_t)header.planes * (size_t)height;
    planar_bytes = (unsigned char *)malloc(decoded_size);
    out_image->pixels = (unsigned int *)malloc((size_t)width * (size_t)height * sizeof(unsigned int));
    if (planar_bytes == NULL || out_image->pixels == NULL) {
        free(file_bytes);
        free(planar_bytes);
        FreeTmgImage(out_image);
        LogLine("LoadTmgBackground: out of memory");
        return 0;
    }

    if (!DecodePcxRle(file_bytes + sizeof(TmgHeader), file_size - sizeof(TmgHeader), planar_bytes, decoded_size)) {
        free(file_bytes);
        free(planar_bytes);
        FreeTmgImage(out_image);
        LogLine("LoadTmgBackground: decode failed");
        return 0;
    }

    out_image->width = width;
    out_image->height = height;

    for (y = 0; y < height; ++y) {
        const unsigned char *row = planar_bytes + (size_t)y * (size_t)header.bytes_per_line * 3u;
        const unsigned char *plane_r = row;
        const unsigned char *plane_g = row + header.bytes_per_line;
        const unsigned char *plane_b = row + header.bytes_per_line * 2u;
        unsigned int x;

        for (x = 0; x < width; ++x) {
            out_image->pixels[(size_t)y * width + x] =
                ExpandRgbToXrgb32(plane_r[x], plane_g[x], plane_b[x]);
        }
    }

    free(file_bytes);
    free(planar_bytes);
    LogLine("LoadTmgBackground: MAINMENU background loaded");
    return 1;
}

static int ContainsTokenCaseInsensitive(const char *haystack, const char *needle)
{
    size_t haystack_len;
    size_t needle_len;
    size_t i;
    size_t j;

    if (haystack == NULL || needle == NULL) {
        return 0;
    }

    haystack_len = strlen(haystack);
    needle_len = strlen(needle);
    if (needle_len == 0 || haystack_len < needle_len) {
        return 0;
    }

    for (i = 0; i + needle_len <= haystack_len; ++i) {
        for (j = 0; j < needle_len; ++j) {
            unsigned char a = (unsigned char)haystack[i + j];
            unsigned char b = (unsigned char)needle[j];
            if (tolower(a) != tolower(b)) {
                break;
            }
        }
        if (j == needle_len) {
            return 1;
        }
    }

    return 0;
}

static void Process_CommandLine_Args(AppState *app, const char *command_line)
{
    app->config.present_use_blt_mode = 1;
    if (command_line == NULL) {
        return;
    }

    if (ContainsTokenCaseInsensitive(command_line, "DEMO")) {
        app->config.demo_mode_enabled = 1;
    }
    if (ContainsTokenCaseInsensitive(command_line, "LOAD")) {
        app->config.load_exception_enabled = 1;
    }
    if (ContainsTokenCaseInsensitive(command_line, "EDIT")) {
        app->config.editor_mode_enabled = 1;
    }
}

static void Init_SetUp(AppState *app)
{
    (void)app;
    LogLine("Init_SetUp: placeholder runtime initialization");
    LogLine("Init_SetUp: future work includes DirectDraw/resource startup");
}

static void MainMenu_Init(AppState *app)
{
    LoadTmgBackground("MAINMENU", &app->mainmenu_background);
    app->screen_state = APP_SCREEN_MAIN_MENU;
    app->frame_tick = Get_Game_Tick();
    app->menu_action_tick = app->frame_tick;
    LogLine("MainMenu_Init: logical main menu state entered");
    LogLine("MainMenu_Init: resource names MAINMENU, MENU_ITEM.EMG, MAINMENU.XMG");
}

static void DrawFrame(AppState *app, HDC dc)
{
    RECT rect;
    const char *mode_text;
    COLORREF background;
    COLORREF foreground;

    GetClientRect(app->window, &rect);
    if (app->screen_state == APP_SCREEN_GAME) {
        background = RGB(24, 32, 52);
        foreground = RGB(230, 235, 245);
        mode_text = "Game frame pump placeholder";
    } else {
        background = RGB(236, 223, 188);
        foreground = RGB(28, 20, 10);
        mode_text = "Main menu frame pump placeholder";
    }

    if (app->screen_state != APP_SCREEN_GAME && app->mainmenu_background.pixels != NULL) {
        BITMAPINFO bmi;
        int draw_x;
        int draw_y;

        ZeroMemory(&bmi, sizeof(bmi));
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        bmi.bmiHeader.biWidth = (LONG)app->mainmenu_background.width;
        bmi.bmiHeader.biHeight = -(LONG)app->mainmenu_background.height;
        bmi.bmiHeader.biPlanes = 1;
        bmi.bmiHeader.biBitCount = 32;
        bmi.bmiHeader.biCompression = BI_RGB;

        draw_x = (rect.right - (LONG)app->mainmenu_background.width) / 2;
        draw_y = (rect.bottom - (LONG)app->mainmenu_background.height) / 2;
        StretchDIBits(
            dc,
            draw_x,
            draw_y,
            (int)app->mainmenu_background.width,
            (int)app->mainmenu_background.height,
            0,
            0,
            (int)app->mainmenu_background.width,
            (int)app->mainmenu_background.height,
            app->mainmenu_background.pixels,
            &bmi,
            DIB_RGB_COLORS,
            SRCCOPY);
    } else {
        HBRUSH brush = CreateSolidBrush(background);
        FillRect(dc, &rect, brush);
        DeleteObject(brush);
    }

    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, foreground);

    TextOutA(dc, 24, 24, kWindowTitle, (int)strlen(kWindowTitle));
    TextOutA(dc, 24, 56, mode_text, (int)strlen(mode_text));
    TextOutA(dc, 24, 88,
             "Recovered boot path: WinMain -> args -> setup -> frame pump",
             59);
}

static void App_Frame_Pump(AppState *app)
{
    app->frame_tick = Get_Game_Tick();
    InvalidateRect(app->window, NULL, FALSE);
    Sleep(16);
}

static void Game_Frame_Pump(AppState *app)
{
    app->frame_tick = Get_Game_Tick();
    InvalidateRect(app->window, NULL, FALSE);
    Sleep(16);
}

static LRESULT CALLBACK App_WndProc(HWND window, UINT message, WPARAM wparam, LPARAM lparam)
{
    AppState *app = (AppState *)GetWindowLongPtrA(window, GWLP_USERDATA);

    switch (message) {
    case WM_NCCREATE: {
        CREATESTRUCTA *create = (CREATESTRUCTA *)lparam;
        SetWindowLongPtrA(window, GWLP_USERDATA, (LONG_PTR)create->lpCreateParams);
        return DefWindowProcA(window, message, wparam, lparam);
    }
    case WM_PAINT: {
        if (app != NULL) {
            PAINTSTRUCT ps;
            HDC dc = BeginPaint(window, &ps);
            DrawFrame(app, dc);
            EndPaint(window, &ps);
            return 0;
        }
        break;
    }
    case WM_DESTROY:
        if (app != NULL) {
            FreeTmgImage(&app->mainmenu_background);
        }
        PostQuitMessage(0);
        return 0;
    }

    return DefWindowProcA(window, message, wparam, lparam);
}

static int RegisterWindowClass(HINSTANCE instance)
{
    WNDCLASSA wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.lpfnWndProc = App_WndProc;
    wc.hInstance = instance;
    wc.lpszClassName = kWindowClassName;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    return RegisterClassA(&wc) != 0;
}

static int CreateMainWindow(AppState *app, int show_command)
{
    DWORD style = WS_OVERLAPPEDWINDOW;
    RECT rect = {0, 0, 1024, 768};

    AdjustWindowRect(&rect, style, FALSE);
    app->window = CreateWindowExA(
        0,
        kWindowClassName,
        kWindowTitle,
        style,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        rect.right - rect.left,
        rect.bottom - rect.top,
        NULL,
        NULL,
        app->instance,
        app);

    if (app->window == NULL) {
        return 0;
    }

    ShowWindow(app->window, show_command);
    UpdateWindow(app->window);
    return 1;
}

static int AcquireSingletonMutex(AppState *app)
{
    app->singleton_mutex = CreateMutexA(NULL, TRUE, "CHINA2EX_REBUILD_MUTEX");
    if (app->singleton_mutex == NULL) {
        return 0;
    }
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        return 0;
    }
    return 1;
}

int App_Run(HINSTANCE instance, LPSTR command_line, int show_command)
{
    MSG message;
    AppState app;

    ZeroMemory(&app, sizeof(app));
    app.instance = instance;
    app.screen_state = APP_SCREEN_BOOT;
    app.running = 1;

    if (!AcquireSingletonMutex(&app)) {
        MessageBoxA(NULL, "Another rebuild instance is already running.", kWindowTitle, MB_OK | MB_ICONINFORMATION);
        return 0;
    }

    if (!RegisterWindowClass(instance) || !CreateMainWindow(&app, show_command)) {
        return 1;
    }

    Process_CommandLine_Args(&app, command_line);
    Init_SetUp(&app);

    app.screen_state = APP_SCREEN_IDLE;
    if (app.config.editor_mode_enabled || app.config.load_exception_enabled || app.config.demo_mode_enabled) {
        app.screen_state = APP_SCREEN_POST_BOOT;
    } else {
        MainMenu_Init(&app);
    }

    app.menu_action_tick = Get_Game_Tick();
    app.frame_tick = app.menu_action_tick;

    while (app.running) {
        while (PeekMessageA(&message, NULL, 0, 0, PM_REMOVE)) {
            if (message.message == WM_QUIT) {
                app.running = 0;
                break;
            }
            TranslateMessage(&message);
            DispatchMessageA(&message);
        }

        if (!app.running) {
            break;
        }

        if (app.screen_state == APP_SCREEN_GAME) {
            Game_Frame_Pump(&app);
        } else {
            App_Frame_Pump(&app);
        }
    }

    if (app.singleton_mutex != NULL) {
        ReleaseMutex(app.singleton_mutex);
        CloseHandle(app.singleton_mutex);
    }
    return (int)message.wParam;
}
