#include "app.h"

int WINAPI WinMain(HINSTANCE instance, HINSTANCE previous_instance, LPSTR command_line, int show_command)
{
    (void)previous_instance;
    return App_Run(instance, command_line, show_command);
}
