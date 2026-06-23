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
    EmgFrame *frames;
} EmgGroup;

typedef struct EmgResource {
    unsigned int group_count;
    EmgGroup *groups;
} EmgResource;

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
    unsigned int menu_item_preview_group;
} AppState;

int App_Run(HINSTANCE instance, LPSTR command_line, int show_command);

#endif
