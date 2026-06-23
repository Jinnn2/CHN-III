#include "app.h"
#include "resources.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *kWindowClassName = "China2EXRebuildWindow";
static const char *kWindowTitle = "China2EX Rebuild Workbench";

static void LogLine(const char *text)
{
    OutputDebugStringA(text);
    OutputDebugStringA("\r\n");
}

static DWORD Get_Game_Tick(void)
{
    return GetTickCount();
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
    if (LoadTmgBackground("MAINMENU", &app->mainmenu_background)) {
        LogLine("MainMenu_Init: MAINMENU.TMG loaded");
    }
    if (LoadEmgResource("EMG\\MENU_ITEM.EMG", &app->menu_item_resource)) {
        LogLine("MainMenu_Init: MENU_ITEM.EMG loaded");
    }
    if (LoadEmgResource("EMG\\MAINMENU.EMG", &app->mainmenu_emg_resource)) {
        LogLine("MainMenu_Init: MAINMENU.EMG loaded");
    }
    if (LoadXmgDiagnostic("IMAGE\\MAINMENU.XMG", &app->mainmenu_xmg_diagnostic)) {
        LogLine("MainMenu_Init: MAINMENU.XMG diagnostic loaded");
    }
    app->menu_item_preview_group = 0;
    app->mainmenu_preview_group = 0;
    app->screen_state = APP_SCREEN_MAIN_MENU;
    app->frame_tick = Get_Game_Tick();
    app->menu_action_tick = app->frame_tick;
    LogLine("MainMenu_Init: logical main menu state entered");
    LogLine("MainMenu_Init: resource names MAINMENU, MENU_ITEM.EMG, MAINMENU.XMG");
}

static void DrawXrgb32Image(HDC dc, int x, int y, unsigned int width, unsigned int height, const unsigned int *pixels)
{
    BITMAPINFO bmi;

    ZeroMemory(&bmi, sizeof(bmi));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = (LONG)width;
    bmi.bmiHeader.biHeight = -(LONG)height;
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    StretchDIBits(
        dc,
        x,
        y,
        (int)width,
        (int)height,
        0,
        0,
        (int)width,
        (int)height,
        pixels,
        &bmi,
        DIB_RGB_COLORS,
        SRCCOPY);
}

static void DrawEmgGroupPreview(HDC dc, EmgResource *resource, unsigned int group_index, int origin_x, int origin_y, const char *label_prefix)
{
    if (resource->group_count > 0) {
        EmgGroup *group = &resource->groups[group_index % resource->group_count];
        if (group->frame_count > 0) {
            unsigned int frame_index;
            unsigned int max_width = 0;
            unsigned int max_height = 0;
            unsigned int *composed;

            for (frame_index = 0; frame_index < group->frame_count; ++frame_index) {
                EmgFrame *frame = &group->frames[frame_index];
                if (frame->x + frame->width > max_width) {
                    max_width = frame->x + frame->width;
                }
                if (frame->y + frame->height > max_height) {
                    max_height = frame->y + frame->height;
                }
            }

            composed = (unsigned int *)calloc((size_t)max_width * (size_t)max_height, sizeof(unsigned int));
            if (composed != NULL) {
                char label[160];

                for (frame_index = 0; frame_index < group->frame_count; ++frame_index) {
                    EmgFrame *frame = &group->frames[frame_index];
                    unsigned int x;
                    for (x = 0; x < frame->width; ++x) {
                        composed[(size_t)frame->y * max_width + frame->x + x] = frame->pixels[x];
                    }
                }

                DrawXrgb32Image(dc, origin_x, origin_y, max_width, max_height, composed);
                free(composed);

                snprintf(label, sizeof(label),
                         "%s group %u/%u (%u x %u)",
                         label_prefix,
                         group_index % resource->group_count,
                         resource->group_count - 1,
                         max_width,
                         max_height);
                TextOutA(dc, origin_x, origin_y - 20, label, (int)strlen(label));
            }
        }
    }
}

static void DrawMainmenuResourcePanel(AppState *app, HDC dc, RECT *client_rect)
{
    RECT panel_rect;
    HBRUSH panel_brush;
    char line[192];

    panel_rect.left = 16;
    panel_rect.top = 136;
    panel_rect.right = 420;
    panel_rect.bottom = client_rect->bottom - 16;
    panel_brush = CreateSolidBrush(RGB(16, 18, 24));
    FillRect(dc, &panel_rect, panel_brush);
    DeleteObject(panel_brush);

    SetTextColor(dc, RGB(228, 232, 240));
    TextOutA(dc, 28, 148, "Main menu resource diagnostics", 30);
    TextOutA(dc, 28, 172, "LEFT/RIGHT: MENU_ITEM.EMG, UP/DOWN: MAINMENU.EMG", 48);

    snprintf(line, sizeof(line),
             "MENU_ITEM.EMG groups=%u current=%u",
             app->menu_item_resource.group_count,
             app->menu_item_resource.group_count ? (app->menu_item_preview_group % app->menu_item_resource.group_count) : 0);
    TextOutA(dc, 28, 204, line, (int)strlen(line));

    snprintf(line, sizeof(line),
             "MAINMENU.EMG groups=%u current=%u",
             app->mainmenu_emg_resource.group_count,
             app->mainmenu_emg_resource.group_count ? (app->mainmenu_preview_group % app->mainmenu_emg_resource.group_count) : 0);
    TextOutA(dc, 28, 228, line, (int)strlen(line));

    snprintf(line, sizeof(line),
             "MAINMENU.XMG groups=%u alt_frames=%u trailing=%u",
             app->mainmenu_xmg_diagnostic.group_count,
             app->mainmenu_xmg_diagnostic.total_alt_frame_count,
             app->mainmenu_xmg_diagnostic.trailing_size);
    TextOutA(dc, 28, 252, line, (int)strlen(line));

    if (app->mainmenu_xmg_diagnostic.group_count > 0) {
        unsigned int group_index = app->mainmenu_preview_group % app->mainmenu_xmg_diagnostic.group_count;
        XmgGroupStat *group = &app->mainmenu_xmg_diagnostic.groups[group_index];
        snprintf(line, sizeof(line),
                 "XMG group %u: frames=%u alt=%u min_field=%u max_field=%u",
                 group_index,
                 group->frame_count,
                 group->alt_frame_count,
                 group->min_width_field,
                 group->max_width_field);
        TextOutA(dc, 28, 276, line, (int)strlen(line));
    }
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
        int draw_x = (rect.right - (LONG)app->mainmenu_background.width) / 2;
        int draw_y = (rect.bottom - (LONG)app->mainmenu_background.height) / 2;
        DrawXrgb32Image(dc, draw_x, draw_y,
                        app->mainmenu_background.width,
                        app->mainmenu_background.height,
                        app->mainmenu_background.pixels);
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
    if (app->screen_state == APP_SCREEN_MAIN_MENU) {
        TextOutA(dc, 24, 112,
                 "Resource preview and diagnostics for MAINMENU assets",
                 52);
        DrawMainmenuResourcePanel(app, dc, &rect);
        DrawEmgGroupPreview(dc, &app->menu_item_resource, app->menu_item_preview_group, rect.right - 264, 160, "MENU_ITEM.EMG");
        DrawEmgGroupPreview(dc, &app->mainmenu_emg_resource, app->mainmenu_preview_group, rect.right - 664, 352, "MAINMENU.EMG");
    }
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
    case WM_KEYDOWN:
        if (app != NULL && app->screen_state == APP_SCREEN_MAIN_MENU) {
            if (wparam == VK_RIGHT && app->menu_item_resource.group_count > 0) {
                app->menu_item_preview_group = (app->menu_item_preview_group + 1) % app->menu_item_resource.group_count;
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_LEFT && app->menu_item_resource.group_count > 0) {
                if (app->menu_item_preview_group == 0) {
                    app->menu_item_preview_group = app->menu_item_resource.group_count - 1;
                } else {
                    app->menu_item_preview_group -= 1;
                }
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_DOWN && app->mainmenu_emg_resource.group_count > 0) {
                app->mainmenu_preview_group = (app->mainmenu_preview_group + 1) % app->mainmenu_emg_resource.group_count;
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_UP && app->mainmenu_emg_resource.group_count > 0) {
                if (app->mainmenu_preview_group == 0) {
                    app->mainmenu_preview_group = app->mainmenu_emg_resource.group_count - 1;
                } else {
                    app->mainmenu_preview_group -= 1;
                }
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
        }
        break;
    case WM_DESTROY:
        if (app != NULL) {
            FreeTmgImage(&app->mainmenu_background);
            FreeEmgResource(&app->menu_item_resource);
            FreeEmgResource(&app->mainmenu_emg_resource);
            FreeXmgDiagnostic(&app->mainmenu_xmg_diagnostic);
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
