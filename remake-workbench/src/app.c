#include "app.h"
#include "resources.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *kWindowClassName = "China2EXRebuildWindow";
static const char *kWindowTitle = "China2EX Rebuild Workbench";

#define MAINMENU_ITEM_COUNT 9u
#define MAINMENU_HIGHLIGHT_FRAME_COUNT 10u

typedef struct MainMenuActionInfo {
    const char *label;
    unsigned int target_screen_state;
    int sets_transition_flag;
    int refreshes_ticks_only;
    int frees_mainmenu_resources;
    const char *notes;
} MainMenuActionInfo;

typedef struct MainMenuHotspotStep {
    unsigned int min_x_exclusive;
    unsigned int max_x_exclusive;
    unsigned int min_y_exclusive;
    unsigned int max_y_exclusive;
    unsigned int next_progress_value;
    const char *label;
} MainMenuHotspotStep;

static const MainMenuActionInfo kMainMenuActions[9] = {
    {"Item 0", 0x04, 0, 0, 0, "MLR_MainMenu case 0: direct transition"},
    {"Item 1", 0x0b, 1, 0, 0, "MLR_MainMenu case 1: sets DAT_005153ac"},
    {"Item 2", 0x0e, 1, 0, 0, "MLR_MainMenu case 2: sets DAT_005153ac"},
    {"Item 3", 0x11, 0, 0, 0, "MLR_MainMenu case 3: enters Load_MAINMENU_EMG path"},
    {"Item 4", 0x14, 0, 0, 0, "MLR_MainMenu case 4: AVI play path"},
    {"Item 5", 0x18, 1, 1, 0, "MLR_MainMenu case 5: resets DAT_00707568 and ticks"},
    {"Item 6", 0x15, 0, 1, 0, "MLR_MainMenu case 6: refreshes ticks and calls FUN_004d0dd0"},
    {"Item 7", 0x02, 0, 0, 0, "MLR_MainMenu case 7: ShellExecute to http://www.double2.com.tw"},
    {"Item 8", 0x2a, 0, 0, 1, "MLR_MainMenu case 8: frees menu resources before exit path"}
};

static const MainMenuHotspotStep kMainMenuHotspotSteps[3] = {
    {0x20c, 0x240, 0x13, 0x47, 1, "Step 1: right-top zone sets DAT_00707f84=1"},
    {0x1da, 0x20e, 0x13, 0x47, 2, "Step 2: middle-top zone advances DAT_00707f84=2"},
    {0x1a8, 0x1dc, 0x13, 0x47, 0, "Step 3: left-top zone triggers DAT_0075593e=1 if progress==2"}
};

typedef struct MainMenuXmgBankRef {
    unsigned int bank_index;
    const char *label;
} MainMenuXmgBankRef;

static void LogLine(const char *text)
{
    OutputDebugStringA(text);
    OutputDebugStringA("\r\n");
}

static void TextOutUtf8(HDC dc, int x, int y, const char *utf8_text)
{
    int wide_len;
    wchar_t *wide_text;

    if (utf8_text == NULL || utf8_text[0] == '\0') {
        return;
    }

    wide_len = MultiByteToWideChar(CP_UTF8, 0, utf8_text, -1, NULL, 0);
    if (wide_len <= 1) {
        return;
    }

    wide_text = (wchar_t *)calloc((size_t)wide_len, sizeof(wchar_t));
    if (wide_text == NULL) {
        return;
    }

    if (MultiByteToWideChar(CP_UTF8, 0, utf8_text, -1, wide_text, wide_len) > 0) {
        TextOutW(dc, x, y, wide_text, wide_len - 1);
    }
    free(wide_text);
}

static void DrawTextUtf8Box(HDC dc, RECT *rect, const char *utf8_text, UINT format)
{
    int wide_len;
    wchar_t *wide_text;

    if (utf8_text == NULL || utf8_text[0] == '\0') {
        return;
    }

    wide_len = MultiByteToWideChar(CP_UTF8, 0, utf8_text, -1, NULL, 0);
    if (wide_len <= 1) {
        return;
    }

    wide_text = (wchar_t *)calloc((size_t)wide_len, sizeof(wchar_t));
    if (wide_text == NULL) {
        return;
    }

    if (MultiByteToWideChar(CP_UTF8, 0, utf8_text, -1, wide_text, wide_len) > 0) {
        DrawTextW(dc, wide_text, -1, rect, format);
    }
    free(wide_text);
}

static DWORD Get_Game_Tick(void)
{
    return GetTickCount();
}

static int StepTowardCoordinate(int current, int target)
{
    int delta = current - target;

    if (delta > 0) {
        if (delta < 0x1f) {
            return current - delta;
        }
        return current - 0x1e;
    }
    if (delta < 0) {
        if (delta > -0x1f) {
            return current - delta;
        }
        return current + 0x1e;
    }
    return current;
}

static void ResetMainMenuRuntimeState(AppState *app)
{
    unsigned int index;

    app->mainmenu_anim_state = 0;
    app->mainmenu_intro_spawn_index = 1;
    app->mainmenu_intro_completed_count = 0;
    app->mainmenu_highlight_frame = 0;

    for (index = 0; index < app->mainmenu_layout.entry_count; ++index) {
        app->mainmenu_layout.entries[index].current_x = app->mainmenu_layout.entries[index].start_x;
        app->mainmenu_layout.entries[index].current_y = app->mainmenu_layout.entries[index].start_y;
        app->mainmenu_layout.entries[index].settled_flag = 0;
        app->mainmenu_layout.entries[index].intro_counter = -1;
    }
    if (app->mainmenu_layout.entry_count > 0) {
        app->mainmenu_layout.entries[0].intro_counter = 0;
    }
}

static void UpdateMainMenuAnimation(AppState *app)
{
    unsigned int index;
    int all_settled = 1;

    if (app->mainmenu_layout.entry_count == 0) {
        return;
    }

    if (app->mainmenu_anim_state == 0) {
        for (index = 0; index < app->mainmenu_layout.entry_count; ++index) {
            MainMenuLayoutEntry *entry = &app->mainmenu_layout.entries[index];
            if (entry->settled_flag == 0) {
                int next_x = StepTowardCoordinate(entry->current_x, entry->final_x);
                int next_y = StepTowardCoordinate(entry->current_y, entry->final_y);
                entry->current_x = next_x;
                entry->current_y = next_y;
                if (entry->current_x == entry->final_x && entry->current_y == entry->final_y) {
                    entry->settled_flag = 1;
                } else {
                    all_settled = 0;
                }
            }
        }

        if (all_settled) {
            app->mainmenu_anim_state = 1;
            app->mainmenu_intro_spawn_index = 1;
            app->mainmenu_intro_completed_count = 0;
            app->mainmenu_highlight_frame = 0;
            for (index = 0; index < app->mainmenu_layout.entry_count; ++index) {
                app->mainmenu_layout.entries[index].intro_counter = -1;
            }
            app->mainmenu_layout.entries[0].intro_counter = 0;
        }
        return;
    }

    if (app->mainmenu_anim_state == 1) {
        for (index = 0; index < app->mainmenu_layout.entry_count; ++index) {
            MainMenuLayoutEntry *entry = &app->mainmenu_layout.entries[index];
            if (entry->intro_counter >= 0 && entry->intro_counter < (int)MAINMENU_HIGHLIGHT_FRAME_COUNT) {
                entry->intro_counter += 1;
                if (entry->intro_counter == (int)MAINMENU_HIGHLIGHT_FRAME_COUNT) {
                    app->mainmenu_intro_completed_count += 1;
                    if (app->mainmenu_intro_completed_count == app->mainmenu_layout.entry_count) {
                        app->mainmenu_anim_state = 2;
                        app->mainmenu_highlight_frame = 0;
                    }
                } else if (entry->intro_counter == 3 && app->mainmenu_intro_spawn_index < app->mainmenu_layout.entry_count) {
                    app->mainmenu_layout.entries[app->mainmenu_intro_spawn_index].intro_counter = 0;
                    app->mainmenu_intro_spawn_index += 1;
                }
            }
        }
        return;
    }

    if (app->mainmenu_anim_state == 2 && app->mainmenu_selected_index >= 0) {
        app->mainmenu_highlight_frame = (app->mainmenu_highlight_frame + 1) % MAINMENU_HIGHLIGHT_FRAME_COUNT;
    }
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
    if (LoadMainMenuLayoutFromExe("China2EX_fontfix8.exe", &app->mainmenu_layout)) {
        LogLine("MainMenu_Init: recovered main menu layout table loaded from exe");
    }
    app->menu_item_preview_group = 0;
    app->mainmenu_preview_group = 0;
    app->mainmenu_family_index = 0;
    app->mainmenu_selected_index = -1;
    app->mainmenu_hotspot_progress = 0;
    ResetMainMenuRuntimeState(app);
    app->screen_state = APP_SCREEN_MAIN_MENU;
    app->frame_tick = Get_Game_Tick();
    app->menu_action_tick = app->frame_tick;
    LogLine("MainMenu_Init: logical main menu state entered");
    LogLine("MainMenu_Init: resource names MAINMENU, MENU_ITEM.EMG, MAINMENU.XMG");
}

static const char *DescribeScreenState(unsigned int screen_state)
{
    switch (screen_state) {
    case APP_SCREEN_MAIN_MENU:
        return "MainMenu steady state";
    case APP_SCREEN_GAME:
        return "Game/map frame pump";
    case APP_SCREEN_POST_BOOT:
        return "Post-boot loader";
    case 0x04:
        return "Menu branch state 0x04";
    case 0x0b:
        return "Menu branch state 0x0b";
    case 0x0e:
        return "Menu branch state 0x0e";
    case 0x11:
        return "Load_MAINMENU_EMG dispatcher";
    case 0x12:
        return "MAINMENU.EMG loaded state";
    case 0x14:
        return "Main menu AVI path";
    case 0x15:
        return "Menu branch state 0x15";
    case 0x18:
        return "Load_UI_String_EMG_XMG path";
    case 0x2a:
        return "Exit / teardown path";
    default:
        return "Unlabeled state";
    }
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
            unsigned int *composed;

            composed = (unsigned int *)calloc((size_t)group->max_width * (size_t)group->max_height, sizeof(unsigned int));
            if (composed != NULL) {
                char label[160];

                for (frame_index = 0; frame_index < group->frame_count; ++frame_index) {
                    EmgFrame *frame = &group->frames[frame_index];
                    unsigned int x;
                    for (x = 0; x < frame->width; ++x) {
                        composed[(size_t)frame->y * group->max_width + frame->x + x] = frame->pixels[x];
                    }
                }

                DrawXrgb32Image(dc, origin_x, origin_y, group->max_width, group->max_height, composed);
                free(composed);

                snprintf(label, sizeof(label),
                         "%s group %u/%u (%u x %u, nonzero=%u/%u)",
                         label_prefix,
                         group_index % resource->group_count,
                         resource->group_count - 1,
                         group->max_width,
                         group->max_height,
                         group->nonzero_frame_count,
                         group->frame_count);
                TextOutA(dc, origin_x, origin_y - 20, label, (int)strlen(label));
            }
        }
    }
}

static void DrawMenuLayoutOverlay(AppState *app, HDC dc, RECT *client_rect)
{
    unsigned int index;
    int background_x = (client_rect->right - (int)app->mainmenu_background.width) / 2;
    int background_y = (client_rect->bottom - (int)app->mainmenu_background.height) / 2;

    if (app->mainmenu_layout.entry_count == 0) {
        return;
    }

    SetBkMode(dc, TRANSPARENT);
    for (index = 0; index < app->mainmenu_layout.entry_count; ++index) {
        MainMenuLayoutEntry *entry = &app->mainmenu_layout.entries[index];
        RECT box;
        COLORREF stroke;
        COLORREF fill;
        int draw_x = background_x + (app->mainmenu_anim_state == 2 ? entry->final_x : entry->current_x);
        int draw_y = background_y + (app->mainmenu_anim_state == 2 ? entry->final_y : entry->current_y);
        int text_width = 190;
        int text_height = 34;
        int highlight = (int)index == app->mainmenu_selected_index;
        RECT text_rect;

        box.left = draw_x - 10;
        box.top = draw_y - 10;
        box.right = draw_x + text_width;
        box.bottom = draw_y + text_height;

        if (highlight) {
            fill = RGB(245, 227, 123);
            stroke = RGB(111, 66, 7);
            SetTextColor(dc, RGB(39, 24, 6));
        } else {
            fill = RGB(31, 37, 50);
            stroke = RGB(120, 140, 176);
            SetTextColor(dc, RGB(234, 238, 246));
        }

        {
            HBRUSH brush = CreateSolidBrush(fill);
            HPEN pen = CreatePen(PS_SOLID, 1, stroke);
            HGDIOBJ old_brush = SelectObject(dc, brush);
            HGDIOBJ old_pen = SelectObject(dc, pen);
            RoundRect(dc, box.left, box.top, box.right, box.bottom, 8, 8);
            SelectObject(dc, old_brush);
            SelectObject(dc, old_pen);
            DeleteObject(brush);
            DeleteObject(pen);
        }

        text_rect.left = draw_x + 8;
        text_rect.top = draw_y + 5;
        text_rect.right = box.right - 8;
        text_rect.bottom = box.bottom - 4;
        DrawTextUtf8Box(dc, &text_rect, entry->short_label[0] != '\0' ? entry->short_label : entry->long_label,
                        DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);

        if (highlight) {
            char hint[96];
            snprintf(hint, sizeof(hint),
                     "base=%u selected=%u hl=%u",
                     index,
                     index + MAINMENU_ITEM_COUNT,
                     MAINMENU_ITEM_COUNT * 2u + app->mainmenu_highlight_frame);
            SetTextColor(dc, RGB(86, 52, 5));
            TextOutA(dc, draw_x + 4, draw_y + 18, hint, (int)strlen(hint));
        } else if (app->mainmenu_anim_state == 1 && entry->intro_counter >= 0 && entry->intro_counter < (int)MAINMENU_HIGHLIGHT_FRAME_COUNT) {
            char intro_hint[64];
            snprintf(intro_hint, sizeof(intro_hint),
                     "intro=%d bank=%u",
                     entry->intro_counter,
                     MAINMENU_ITEM_COUNT * 2u + (unsigned int)entry->intro_counter);
            SetTextColor(dc, RGB(203, 225, 255));
            TextOutA(dc, draw_x + 4, draw_y + 18, intro_hint, (int)strlen(intro_hint));
        }
    }

    SetTextColor(dc, RGB(224, 231, 239));
    TextOutUtf8(dc, background_x + 725, background_y + 742, app->mainmenu_layout.title_text);
    if (app->mainmenu_hotspot_progress == 2) {
        TextOutUtf8(dc, background_x + 0, background_y + 741, app->mainmenu_layout.admin_text);
    }
}

static void DrawMainMenuXmgTriplet(AppState *app, HDC dc, int origin_x, int origin_y)
{
    MainMenuXmgBankRef refs[3];
    unsigned int index;
    RECT panel;

    if (app->mainmenu_selected_index < 0 || app->mainmenu_selected_index >= (int)MAINMENU_ITEM_COUNT ||
        app->mainmenu_xmg_diagnostic.group_count < MAINMENU_ITEM_COUNT * 3u + 1u) {
        return;
    }

    refs[0].bank_index = (unsigned int)app->mainmenu_selected_index;
    refs[0].label = "Base";
    refs[1].bank_index = (unsigned int)app->mainmenu_selected_index + MAINMENU_ITEM_COUNT;
    refs[1].label = "Selected";
    refs[2].bank_index = MAINMENU_ITEM_COUNT * 2u + app->mainmenu_highlight_frame;
    refs[2].label = "Highlight";

    panel.left = origin_x;
    panel.top = origin_y;
    panel.right = origin_x + 338;
    panel.bottom = origin_y + 176;
    {
        HBRUSH brush = CreateSolidBrush(RGB(20, 23, 31));
        FillRect(dc, &panel, brush);
        DeleteObject(brush);
    }

    SetTextColor(dc, RGB(232, 236, 243));
    TextOutA(dc, origin_x + 10, origin_y + 8, "Recovered MAINMENU.XMG bank triplet", 34);

    for (index = 0; index < 3; ++index) {
        XmgGroupStat *group = &app->mainmenu_xmg_diagnostic.groups[refs[index].bank_index];
        RECT bank_box;
        RECT sample_box;
        char line[160];
        char detail[192];
        unsigned int box_x = origin_x + 10 + index * 108;
        unsigned int box_y = origin_y + 34;

        bank_box.left = (LONG)box_x;
        bank_box.top = (LONG)box_y;
        bank_box.right = (LONG)box_x + 98;
        bank_box.bottom = (LONG)box_y + 132;
        sample_box.left = bank_box.left + 8;
        sample_box.top = bank_box.top + 20;
        sample_box.right = bank_box.right - 8;
        sample_box.bottom = bank_box.top + 84;

        {
            HBRUSH brush = CreateSolidBrush(index == 1 ? RGB(59, 70, 89) : RGB(39, 45, 58));
            HPEN pen = CreatePen(PS_SOLID, 1, index == 2 ? RGB(220, 175, 92) : RGB(103, 119, 144));
            HGDIOBJ old_brush = SelectObject(dc, brush);
            HGDIOBJ old_pen = SelectObject(dc, pen);
            Rectangle(dc, bank_box.left, bank_box.top, bank_box.right, bank_box.bottom);
            SelectObject(dc, old_brush);
            SelectObject(dc, old_pen);
            DeleteObject(brush);
            DeleteObject(pen);
        }

        snprintf(line, sizeof(line), "%s #%u", refs[index].label, refs[index].bank_index);
        SetTextColor(dc, RGB(236, 239, 245));
        TextOutA(dc, bank_box.left + 6, bank_box.top + 4, line, (int)strlen(line));

        {
            HBRUSH brush = CreateSolidBrush(group->alt_frame_count > 0 ? RGB(71, 95, 124) : RGB(124, 94, 53));
            FillRect(dc, &sample_box, brush);
            DeleteObject(brush);
        }

        snprintf(detail, sizeof(detail),
                 "bbox %u..%u\n%u..%u\nframes %u\nalt %u\nwords %u..%u",
                 group->min_x,
                 group->max_x,
                 group->min_y,
                 group->max_y,
                 group->frame_count,
                 group->alt_frame_count,
                 group->min_payload_words,
                 group->max_payload_words);
        DrawTextA(dc, detail, -1, &sample_box, DT_CENTER | DT_VCENTER | DT_WORDBREAK);

        snprintf(line, sizeof(line), "payload=%u mask=%u", group->total_payload_words, group->total_mask_bytes);
        SetTextColor(dc, RGB(201, 209, 222));
        TextOutA(dc, bank_box.left + 6, bank_box.bottom - 18, line, (int)strlen(line));
    }
}

static int SameMainmenuFamily(EmgGroup *group, unsigned int family_index)
{
    static const struct {
        unsigned int width;
        unsigned int height;
    } families[] = {
        {309, 273},
        {322, 456},
        {272, 111},
        {426, 523},
        {174, 245},
        {528, 480}
    };

    if (family_index >= sizeof(families) / sizeof(families[0])) {
        return 0;
    }
    return group->max_width == families[family_index].width && group->max_height == families[family_index].height;
}

static void JumpMainmenuPreviewByFamily(AppState *app, int direction)
{
    unsigned int count = app->mainmenu_emg_resource.group_count;
    unsigned int attempts = 0;

    if (count == 0) {
        return;
    }

    while (attempts < count) {
        if (direction > 0) {
            app->mainmenu_preview_group = (app->mainmenu_preview_group + 1) % count;
        } else {
            if (app->mainmenu_preview_group == 0) {
                app->mainmenu_preview_group = count - 1;
            } else {
                app->mainmenu_preview_group -= 1;
            }
        }

        if (SameMainmenuFamily(&app->mainmenu_emg_resource.groups[app->mainmenu_preview_group], app->mainmenu_family_index)) {
            return;
        }
        attempts += 1;
    }
}

static void DrawMainmenuResourcePanel(AppState *app, HDC dc, RECT *client_rect)
{
    RECT panel_rect;
    RECT detail_rect;
    HBRUSH panel_brush;
    char line[192];
    const MainMenuActionInfo *action;

    panel_rect.left = 16;
    panel_rect.top = 136;
    panel_rect.right = 420;
    panel_rect.bottom = client_rect->bottom - 16;
    panel_brush = CreateSolidBrush(RGB(16, 18, 24));
    FillRect(dc, &panel_rect, panel_brush);
    DeleteObject(panel_brush);

    SetTextColor(dc, RGB(228, 232, 240));
    TextOutA(dc, 28, 148, "Main menu resource diagnostics", 30);
    TextOutA(dc, 28, 172, "LEFT/RIGHT: MENU_ITEM, UP/DOWN: MAINMENU, TAB: family, [ ]: select", 67);
    TextOutA(dc, 28, 196, "ENTER: inspect MLR action, H: advance hidden top-hotspot chain", 59);

    snprintf(line, sizeof(line),
             "MENU_ITEM.EMG groups=%u current=%u",
             app->menu_item_resource.group_count,
             app->menu_item_resource.group_count ? (app->menu_item_preview_group % app->menu_item_resource.group_count) : 0);
    TextOutA(dc, 28, 228, line, (int)strlen(line));

    snprintf(line, sizeof(line),
             "MAINMENU.EMG groups=%u current=%u",
             app->mainmenu_emg_resource.group_count,
             app->mainmenu_emg_resource.group_count ? (app->mainmenu_preview_group % app->mainmenu_emg_resource.group_count) : 0);
    TextOutA(dc, 28, 252, line, (int)strlen(line));

    if (app->mainmenu_emg_resource.group_count > 0) {
        EmgGroup *group = &app->mainmenu_emg_resource.groups[app->mainmenu_preview_group % app->mainmenu_emg_resource.group_count];
        snprintf(line, sizeof(line),
                 "MAINMENU family=%u size=%u x %u nonzero=%u/%u",
                 app->mainmenu_family_index,
                 group->max_width,
                 group->max_height,
                 group->nonzero_frame_count,
                 group->frame_count);
        TextOutA(dc, 28, 276, line, (int)strlen(line));
    }

    snprintf(line, sizeof(line),
             "MAINMENU.XMG groups=%u alt_frames=%u trailing=%u",
             app->mainmenu_xmg_diagnostic.group_count,
             app->mainmenu_xmg_diagnostic.total_alt_frame_count,
             app->mainmenu_xmg_diagnostic.trailing_size);
    TextOutA(dc, 28, 300, line, (int)strlen(line));

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
        TextOutA(dc, 28, 324, line, (int)strlen(line));
    }

    if (app->mainmenu_selected_index >= 0 && app->mainmenu_selected_index < 9) {
        action = &kMainMenuActions[app->mainmenu_selected_index];
        snprintf(line, sizeof(line),
                 "MLR select=%d -> state=0x%02x (%s)",
                 app->mainmenu_selected_index,
                 action->target_screen_state,
                 DescribeScreenState(action->target_screen_state));
        TextOutA(dc, 28, 360, line, (int)strlen(line));

        snprintf(line, sizeof(line),
                 "XMG bank offsets: base=%d selected=%d highlight=%u",
                 app->mainmenu_selected_index,
                 app->mainmenu_selected_index + MAINMENU_ITEM_COUNT,
                 MAINMENU_ITEM_COUNT * 2u + app->mainmenu_highlight_frame);
        TextOutA(dc, 28, 384, line, (int)strlen(line));

        snprintf(line, sizeof(line),
                 "Flags: transition=%s tick-refresh=%s free-resources=%s",
                 action->sets_transition_flag ? "yes" : "no",
                 action->refreshes_ticks_only ? "yes" : "no",
                 action->frees_mainmenu_resources ? "yes" : "no");
        TextOutA(dc, 28, 408, line, (int)strlen(line));

        TextOutA(dc, 28, 432, action->notes, (int)strlen(action->notes));
        detail_rect.left = 28;
        detail_rect.top = 456;
        detail_rect.right = 408;
        detail_rect.bottom = 516;
        DrawTextUtf8Box(dc, &detail_rect,
                        app->mainmenu_layout.entries[app->mainmenu_selected_index].long_label,
                        DT_WORDBREAK | DT_NOPREFIX);

        if (app->mainmenu_xmg_diagnostic.group_count >= MAINMENU_ITEM_COUNT * 3u) {
            XmgGroupStat *base_group = &app->mainmenu_xmg_diagnostic.groups[app->mainmenu_selected_index];
            XmgGroupStat *selected_group = &app->mainmenu_xmg_diagnostic.groups[app->mainmenu_selected_index + MAINMENU_ITEM_COUNT];
            XmgGroupStat *highlight_group = &app->mainmenu_xmg_diagnostic.groups[MAINMENU_ITEM_COUNT * 2u + app->mainmenu_highlight_frame];
            snprintf(line, sizeof(line),
                     "bbox base=%u..%u/%u..%u sel=%u..%u/%u..%u hl=%u..%u/%u..%u",
                     base_group->min_x, base_group->max_x, base_group->min_y, base_group->max_y,
                     selected_group->min_x, selected_group->max_x, selected_group->min_y, selected_group->max_y,
                     highlight_group->min_x, highlight_group->max_x, highlight_group->min_y, highlight_group->max_y);
            TextOutA(dc, 28, 518, line, (int)strlen(line));
        }
    } else {
        TextOutA(dc, 28, 360, "MLR select=-1: no menu item selected", 35);
        TextOutA(dc, 28, 384, "PutScreen_Mainmenu uses XMG base bank when item is not selected", 61);
    }

    snprintf(line, sizeof(line),
             "Hidden hotspot chain progress=%u reveal=%s",
             app->mainmenu_hotspot_progress,
             app->mainmenu_hotspot_progress == 0 ? "off" : (app->mainmenu_hotspot_progress == 2 ? "armed" : "mid-chain"));
    TextOutA(dc, 28, 532, line, (int)strlen(line));

    snprintf(line, sizeof(line),
             "Recovered exe layout: entries=%u version=%u.%u",
             app->mainmenu_layout.entry_count,
             app->mainmenu_layout.version_major,
             app->mainmenu_layout.version_minor);
    TextOutA(dc, 28, 556, line, (int)strlen(line));

    TextOutA(dc, 28, 580, kMainMenuHotspotSteps[0].label, (int)strlen(kMainMenuHotspotSteps[0].label));
    TextOutA(dc, 28, 604, kMainMenuHotspotSteps[1].label, (int)strlen(kMainMenuHotspotSteps[1].label));
    TextOutA(dc, 28, 628, kMainMenuHotspotSteps[2].label, (int)strlen(kMainMenuHotspotSteps[2].label));
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
        DrawMenuLayoutOverlay(app, dc, &rect);
        DrawMainmenuResourcePanel(app, dc, &rect);
        DrawMainMenuXmgTriplet(app, dc, rect.right - 376, rect.bottom - 206);
        DrawEmgGroupPreview(dc, &app->menu_item_resource, app->menu_item_preview_group, rect.right - 264, 160, "MENU_ITEM.EMG");
        DrawEmgGroupPreview(dc, &app->mainmenu_emg_resource, app->mainmenu_preview_group, rect.right - 664, 352, "MAINMENU.EMG");
    }
}

static void App_Frame_Pump(AppState *app)
{
    app->frame_tick = Get_Game_Tick();
    if (app->screen_state == APP_SCREEN_MAIN_MENU) {
        UpdateMainMenuAnimation(app);
    }
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
                JumpMainmenuPreviewByFamily(app, 1);
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_UP && app->mainmenu_emg_resource.group_count > 0) {
                JumpMainmenuPreviewByFamily(app, -1);
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_TAB) {
                app->mainmenu_family_index = (app->mainmenu_family_index + 1) % 6;
                if (app->mainmenu_emg_resource.group_count > 0 &&
                    !SameMainmenuFamily(&app->mainmenu_emg_resource.groups[app->mainmenu_preview_group], app->mainmenu_family_index)) {
                    unsigned int attempts = 0;
                    while (attempts < app->mainmenu_emg_resource.group_count) {
                        if (SameMainmenuFamily(&app->mainmenu_emg_resource.groups[app->mainmenu_preview_group], app->mainmenu_family_index)) {
                            break;
                        }
                        app->mainmenu_preview_group = (app->mainmenu_preview_group + 1) % app->mainmenu_emg_resource.group_count;
                        attempts += 1;
                    }
                }
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_OEM_4) {
                if (app->mainmenu_selected_index < 0) {
                    app->mainmenu_selected_index = 8;
                } else {
                    app->mainmenu_selected_index = (app->mainmenu_selected_index + 8) % 9;
                }
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_OEM_6) {
                app->mainmenu_selected_index = (app->mainmenu_selected_index + 1) % 9;
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == VK_RETURN && app->mainmenu_selected_index >= 0 && app->mainmenu_selected_index < 9) {
                const MainMenuActionInfo *action = &kMainMenuActions[app->mainmenu_selected_index];
                char line_buffer[160];
                snprintf(line_buffer, sizeof(line_buffer),
                         "MLR_MainMenu diagnostic: select=%d target=0x%02x note=%s",
                         app->mainmenu_selected_index,
                         action->target_screen_state,
                         action->notes);
                LogLine(line_buffer);
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == 'H') {
                if (app->mainmenu_hotspot_progress == 0) {
                    app->mainmenu_hotspot_progress = 1;
                } else if (app->mainmenu_hotspot_progress == 1) {
                    app->mainmenu_hotspot_progress = 2;
                } else {
                    app->mainmenu_hotspot_progress = 0;
                }
                InvalidateRect(window, NULL, FALSE);
                return 0;
            }
            if (wparam == 'R') {
                ResetMainMenuRuntimeState(app);
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
            FreeMainMenuLayout(&app->mainmenu_layout);
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
