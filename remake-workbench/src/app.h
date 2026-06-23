#ifndef CHINA2EX_REBUILD_APP_H
#define CHINA2EX_REBUILD_APP_H

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

enum AppScreenState {
    APP_SCREEN_BOOT = 0,
    APP_SCREEN_IDLE = 1,
    APP_SCREEN_MAIN_MENU = 2,
    APP_SCREEN_GAME = 0x25,
    APP_SCREEN_POST_BOOT = 0x24
};

typedef struct AppConfig {
    int demo_mode_enabled;
    int load_exception_enabled;
    int editor_mode_enabled;
    int present_use_blt_mode;
} AppConfig;

typedef struct TmgImage {
    unsigned int width;
    unsigned int height;
    unsigned int *pixels;
} TmgImage;

typedef struct EmgFrame {
    unsigned int x;
    unsigned int y;
    unsigned int width;
    unsigned int height;
    unsigned int *pixels;
} EmgFrame;

typedef struct EmgGroup {
    unsigned int frame_count;
    unsigned int max_width;
    unsigned int max_height;
    unsigned int nonzero_frame_count;
    EmgFrame *frames;
} EmgGroup;

typedef struct EmgResource {
    unsigned int group_count;
    EmgGroup *groups;
} EmgResource;

typedef struct XmgGroupStat {
    unsigned int frame_count;
    unsigned int alt_frame_count;
    unsigned int min_width_field;
    unsigned int max_width_field;
} XmgGroupStat;

typedef struct XmgDiagnostic {
    unsigned int group_count;
    unsigned int trailing_size;
    unsigned int total_alt_frame_count;
    XmgGroupStat *groups;
} XmgDiagnostic;

typedef struct MainMenuLayoutEntry {
    int final_x;
    int final_y;
    int current_x;
    int current_y;
    int settled_flag;
    int enabled_flag;
    char label[80];
} MainMenuLayoutEntry;

typedef struct MainMenuLayout {
    unsigned int entry_count;
    unsigned int version_major;
    unsigned int version_minor;
    char title_text[48];
    char admin_text[32];
    MainMenuLayoutEntry entries[9];
} MainMenuLayout;

typedef struct AppState {
    HINSTANCE instance;
    HWND window;
    HANDLE singleton_mutex;
    AppConfig config;
    unsigned int screen_state;
    DWORD frame_tick;
    DWORD menu_action_tick;
    int running;
    TmgImage mainmenu_background;
    EmgResource menu_item_resource;
    EmgResource mainmenu_emg_resource;
    XmgDiagnostic mainmenu_xmg_diagnostic;
    MainMenuLayout mainmenu_layout;
    unsigned int menu_item_preview_group;
    unsigned int mainmenu_preview_group;
    unsigned int mainmenu_family_index;
    int mainmenu_selected_index;
    unsigned int mainmenu_hotspot_progress;
} AppState;

int App_Run(HINSTANCE instance, LPSTR command_line, int show_command);

#endif
