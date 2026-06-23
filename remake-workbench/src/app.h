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
    unsigned int min_x;
    unsigned int max_x;
    unsigned int min_y;
    unsigned int max_y;
    unsigned int min_payload_words;
    unsigned int max_payload_words;
    unsigned int total_payload_words;
    unsigned int total_mask_bytes;
} XmgGroupStat;

typedef struct XmgDiagnostic {
    unsigned int group_count;
    unsigned int trailing_size;
    unsigned int total_alt_frame_count;
    XmgGroupStat *groups;
} XmgDiagnostic;

typedef struct XmgFrame {
    unsigned int x;
    unsigned int y;
    unsigned int width;
    unsigned int height;
    int has_alt_mask;
    unsigned int *pixels;
    unsigned char *mask_bytes;
} XmgFrame;

typedef struct XmgGroup {
    unsigned int frame_count;
    unsigned int max_width;
    unsigned int max_height;
    unsigned int alt_frame_count;
    unsigned int nonzero_frame_count;
    XmgFrame *frames;
} XmgGroup;

typedef struct XmgResource {
    unsigned int group_count;
    XmgGroup *groups;
} XmgResource;

typedef struct MainMenuLayoutEntry {
    int final_x;
    int final_y;
    int start_x;
    int start_y;
    int current_x;
    int current_y;
    int settled_flag;
    int enabled_flag;
    int intro_counter;
    char long_label[80];
    char short_label[32];
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
    XmgResource mainmenu_xmg_resource;
    MainMenuLayout mainmenu_layout;
    unsigned int menu_item_preview_group;
    unsigned int mainmenu_preview_group;
    unsigned int mainmenu_family_index;
    unsigned int mainmenu_anim_state;
    unsigned int mainmenu_intro_spawn_index;
    unsigned int mainmenu_intro_completed_count;
    unsigned int mainmenu_highlight_frame;
    int mainmenu_selected_index;
    unsigned int mainmenu_hotspot_progress;
} AppState;

int App_Run(HINSTANCE instance, LPSTR command_line, int show_command);

#endif
