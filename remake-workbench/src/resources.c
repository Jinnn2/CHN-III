#include "resources.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

static unsigned int ExpandRgb565ToXrgb32(uint16_t pixel)
{
    unsigned int red = ((pixel >> 11) & 0x1Fu) * 255u / 31u;
    unsigned int green = ((pixel >> 5) & 0x3Fu) * 255u / 63u;
    unsigned int blue = (pixel & 0x1Fu) * 255u / 31u;
    return (red << 16) | (green << 8) | blue;
}

void FreeTmgImage(TmgImage *image)
{
    if (image->pixels != NULL) {
        free(image->pixels);
        image->pixels = NULL;
    }
    image->width = 0;
    image->height = 0;
}

int LoadTmgBackground(const char *name, TmgImage *out_image)
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
        return 0;
    }

    memcpy(&header, file_bytes, sizeof(header));
    width = (unsigned int)(header.x_max - header.x_min + 1u);
    height = (unsigned int)(header.y_max - header.y_min + 1u);

    if (header.manufacturer != 0x0A || header.version != 5 || header.encoding != 1 ||
        header.bits_per_pixel != 8 || header.planes != 3 || header.bytes_per_line < width) {
        free(file_bytes);
        return 0;
    }

    decoded_size = (size_t)header.bytes_per_line * (size_t)header.planes * (size_t)height;
    planar_bytes = (unsigned char *)malloc(decoded_size);
    out_image->pixels = (unsigned int *)malloc((size_t)width * (size_t)height * sizeof(unsigned int));
    if (planar_bytes == NULL || out_image->pixels == NULL) {
        free(file_bytes);
        free(planar_bytes);
        FreeTmgImage(out_image);
        return 0;
    }

    if (!DecodePcxRle(file_bytes + sizeof(TmgHeader), file_size - sizeof(TmgHeader), planar_bytes, decoded_size)) {
        free(file_bytes);
        free(planar_bytes);
        FreeTmgImage(out_image);
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
    return 1;
}

void FreeEmgResource(EmgResource *resource)
{
    unsigned int group_index;

    if (resource->groups != NULL) {
        for (group_index = 0; group_index < resource->group_count; ++group_index) {
            EmgGroup *group = &resource->groups[group_index];
            unsigned int frame_index;
            for (frame_index = 0; frame_index < group->frame_count; ++frame_index) {
                free(group->frames[frame_index].pixels);
                group->frames[frame_index].pixels = NULL;
            }
            free(group->frames);
            group->frames = NULL;
            group->frame_count = 0;
        }
        free(resource->groups);
        resource->groups = NULL;
    }
    resource->group_count = 0;
}

void FreeXmgDiagnostic(XmgDiagnostic *diagnostic)
{
    free(diagnostic->groups);
    diagnostic->groups = NULL;
    diagnostic->group_count = 0;
    diagnostic->trailing_size = 0;
    diagnostic->total_alt_frame_count = 0;
}

int LoadEmgResource(const char *relative_path, EmgResource *out_resource)
{
    char path[MAX_PATH];
    unsigned char *bytes = NULL;
    size_t file_size = 0;
    size_t offset = 0;
    uint16_t group_count;
    unsigned int group_index;

    snprintf(path, sizeof(path), "..\\%s", relative_path);
    FreeEmgResource(out_resource);

    if (!LoadFileBytes(path, &bytes, &file_size) || file_size < 2) {
        return 0;
    }

    group_count = (uint16_t)(bytes[0] | (bytes[1] << 8));
    offset = 2;
    out_resource->groups = (EmgGroup *)calloc(group_count, sizeof(EmgGroup));
    if (out_resource->groups == NULL) {
        free(bytes);
        return 0;
    }
    out_resource->group_count = group_count;

    for (group_index = 0; group_index < group_count; ++group_index) {
        uint16_t frame_count;
        EmgGroup *group;
        unsigned int frame_index;
        unsigned int max_width = 0;
        unsigned int max_height = 0;

        if (offset + 2 > file_size) {
            free(bytes);
            FreeEmgResource(out_resource);
            return 0;
        }
        frame_count = (uint16_t)(bytes[offset] | (bytes[offset + 1] << 8));
        offset += 2;

        group = &out_resource->groups[group_index];
        group->frame_count = frame_count;
        group->frames = (EmgFrame *)calloc(frame_count, sizeof(EmgFrame));
        if (group->frames == NULL) {
            free(bytes);
            FreeEmgResource(out_resource);
            return 0;
        }

        for (frame_index = 0; frame_index < frame_count; ++frame_index) {
            EmgFrame *frame = &group->frames[frame_index];
            uint16_t x;
            uint16_t y;
            uint16_t width_words;

            if (offset + 6 > file_size) {
                free(bytes);
                FreeEmgResource(out_resource);
                return 0;
            }

            x = (uint16_t)(bytes[offset] | (bytes[offset + 1] << 8));
            y = (uint16_t)(bytes[offset + 2] | (bytes[offset + 3] << 8));
            width_words = (uint16_t)(bytes[offset + 4] | (bytes[offset + 5] << 8));
            offset += 6;

            frame->x = x;
            frame->y = y;
            frame->width = width_words;
            frame->height = 1;
            frame->pixels = (unsigned int *)malloc((size_t)width_words * sizeof(unsigned int));
            if (frame->pixels == NULL || offset + (size_t)width_words * 2 > file_size) {
                free(bytes);
                FreeEmgResource(out_resource);
                return 0;
            }

            {
                unsigned int pixel_index;
                const unsigned char *payload = bytes + offset;
                int frame_has_nonzero = 0;
                for (pixel_index = 0; pixel_index < width_words; ++pixel_index) {
                    uint16_t pixel = (uint16_t)(payload[pixel_index * 2] | (payload[pixel_index * 2 + 1] << 8));
                    frame->pixels[pixel_index] = ExpandRgb565ToXrgb32(pixel);
                    if (pixel != 0) {
                        frame_has_nonzero = 1;
                    }
                }
                if (frame_has_nonzero) {
                    group->nonzero_frame_count += 1;
                }
            }
            offset += (size_t)width_words * 2;

            if (frame->width > max_width) {
                max_width = frame->width;
            }
            if (frame->y + 1u > max_height) {
                max_height = frame->y + 1u;
            }
        }

        for (frame_index = 0; frame_index < frame_count; ++frame_index) {
            group->frames[frame_index].height = max_height;
            if (group->frames[frame_index].width == 0) {
                group->frames[frame_index].width = max_width;
            }
        }
        group->max_width = max_width;
        group->max_height = max_height;
    }

    free(bytes);
    return offset == file_size;
}

int LoadXmgDiagnostic(const char *relative_path, XmgDiagnostic *out_diagnostic)
{
    char path[MAX_PATH];
    unsigned char *bytes = NULL;
    size_t file_size = 0;
    size_t offset = 0;
    uint16_t group_count;
    unsigned int group_index;

    snprintf(path, sizeof(path), "..\\%s", relative_path);
    FreeXmgDiagnostic(out_diagnostic);

    if (!LoadFileBytes(path, &bytes, &file_size) || file_size < 2) {
        return 0;
    }

    group_count = (uint16_t)(bytes[0] | (bytes[1] << 8));
    offset = 2;
    out_diagnostic->groups = (XmgGroupStat *)calloc(group_count, sizeof(XmgGroupStat));
    if (out_diagnostic->groups == NULL) {
        free(bytes);
        return 0;
    }
    out_diagnostic->group_count = group_count;

    for (group_index = 0; group_index < group_count; ++group_index) {
        uint16_t frame_count;
        unsigned int frame_index;
        XmgGroupStat *group;

        if (offset + 2 > file_size) {
            free(bytes);
            FreeXmgDiagnostic(out_diagnostic);
            return 0;
        }

        frame_count = (uint16_t)(bytes[offset] | (bytes[offset + 1] << 8));
        offset += 2;
        group = &out_diagnostic->groups[group_index];
        group->frame_count = frame_count;
        group->min_width_field = 0xffffffffu;
        group->max_width_field = 0;

        for (frame_index = 0; frame_index < frame_count; ++frame_index) {
            uint16_t width_field;

            if (offset + 6 > file_size) {
                free(bytes);
                FreeXmgDiagnostic(out_diagnostic);
                return 0;
            }

            width_field = (uint16_t)(bytes[offset + 4] | (bytes[offset + 5] << 8));
            if (width_field < group->min_width_field) {
                group->min_width_field = width_field;
            }
            if (width_field > group->max_width_field) {
                group->max_width_field = width_field;
            }

            if ((width_field & 0x8000u) != 0) {
                unsigned int payload_words = width_field & 0x7fffu;
                group->alt_frame_count += 1;
                out_diagnostic->total_alt_frame_count += 1;
                offset += ((size_t)payload_words + 2u) * 3u;
            } else {
                offset += 6u + (size_t)width_field * 2u;
            }

            if (offset > file_size) {
                free(bytes);
                FreeXmgDiagnostic(out_diagnostic);
                return 0;
            }
        }

        if (group->min_width_field == 0xffffffffu) {
            group->min_width_field = 0;
        }
    }

    out_diagnostic->trailing_size = (unsigned int)(file_size - offset);
    free(bytes);
    return 1;
}
