#ifndef CHINA2EX_REBUILD_RESOURCES_H
#define CHINA2EX_REBUILD_RESOURCES_H

#include "app.h"

int LoadTmgBackground(const char *name, TmgImage *out_image);
void FreeTmgImage(TmgImage *image);

int LoadEmgResource(const char *relative_path, EmgResource *out_resource);
void FreeEmgResource(EmgResource *resource);

#endif
