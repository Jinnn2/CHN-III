#include "resources.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAINMENU_LAYOUT_ENTRY_COUNT 9u
#define MAINMENU_LAYOUT_VA_BASE 0x400000u
#define MAINMENU_LAYOUT_RECORDS_VA 0x00575b68u
#define MAINMENU_LAYOUT_VERSION_MAJOR_VA 0x00575b50u
#define MAINMENU_LAYOUT_VERSION_MINOR_VA 0x00575b54u
#define MAINMENU_LAYOUT_TITLE_VA 0x00575f20u
#define MAINMENU_LAYOUT_ADMIN_VA 0x00575f3cu
#define MAINMENU_LAYOUT_SHORT_LABELS_VA 0x00575bb8u

typedef struct PeSectionHeader {
    uint32_t virtual_size;
    uint32_t virtual_address;
    uint32_t size_of_raw_data;
    uint32_t pointer_to_raw_data;
} PeSectionHeader;

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

static int DecodeBig5String(const unsigned char *src, size_t src_size, char *dst, size_t dst_size)
{
    int wide_count;
    wchar_t *wide_text;
    int utf8_count;

    if (dst == NULL || dst_size == 0) {
        return 0;
    }

    dst[0] = '\0';
    wide_count = MultiByteToWideChar(950, 0, (const char *)src, (int)src_size, NULL, 0);
    if (wide_count <= 0) {
        return 0;
    }

    wide_text = (wchar_t *)calloc((size_t)wide_count + 1u, sizeof(wchar_t));
    if (wide_text == NULL) {
        return 0;
    }

    if (MultiByteToWideChar(950, 0, (const char *)src, (int)src_size, wide_text, wide_count) <= 0) {
        free(wide_text);
        return 0;
    }

    utf8_count = WideCharToMultiByte(CP_UTF8, 0, wide_text, wide_count, dst, (int)dst_size - 1, NULL, NULL);
    free(wide_text);
    if (utf8_count <= 0) {
        dst[0] = '\0';
        return 0;
    }
    dst[utf8_count] = '\0';
    return 1;
}

static int ReadU16LE(const unsigned char *bytes, size_t file_size, size_t offset, uint16_t *out_value)
{
    if (offset + 2 > file_size) {
        return 0;
    }
    *out_value = (uint16_t)(bytes[offset] | (bytes[offset + 1] << 8));
    return 1;
}

static int ReadU32LE(const unsigned char *bytes, size_t file_size, size_t offset, uint32_t *out_value)
{
    if (offset + 4 > file_size) {
        return 0;
    }
    *out_value = (uint32_t)(bytes[offset] |
        ((uint32_t)bytes[offset + 1] << 8) |
        ((uint32_t)bytes[offset + 2] << 16) |
        ((uint32_t)bytes[offset + 3] << 24));
    return 1;
}

static int ReadS32LE(const unsigned char *bytes, size_t file_size, size_t offset, int *out_value)
{
    uint32_t value;

    if (!ReadU32LE(bytes, file_size, offset, &value)) {
        return 0;
    }
    *out_value = (int)value;
    return 1;
}

static int LoadPeSections(const unsigned char *bytes, size_t file_size, size_t *out_section_count, PeSectionHeader **out_sections)
{
    uint32_t pe_offset;
    uint16_t section_count;
    uint16_t optional_header_size;
    size_t section_offset;
    PeSectionHeader *sections;
    unsigned int index;

    *out_section_count = 0;
    *out_sections = NULL;

    if (!ReadU32LE(bytes, file_size, 0x3c, &pe_offset) || pe_offset + 24 > file_size) {
        return 0;
    }
    if (!ReadU16LE(bytes, file_size, (size_t)pe_offset + 6, &section_count) ||
        !ReadU16LE(bytes, file_size, (size_t)pe_offset + 20, &optional_header_size)) {
        return 0;
    }

    section_offset = (size_t)pe_offset + 24u + (size_t)optional_header_size;
    if (section_offset + (size_t)section_count * 40u > file_size) {
        return 0;
    }

    sections = (PeSectionHeader *)calloc(section_count, sizeof(PeSectionHeader));
    if (sections == NULL) {
        return 0;
    }

    for (index = 0; index < section_count; ++index) {
        size_t header_offset = section_offset + (size_t)index * 40u;
        if (!ReadU32LE(bytes, file_size, header_offset + 8, &sections[index].virtual_size) ||
            !ReadU32LE(bytes, file_size, header_offset + 12, &sections[index].virtual_address) ||
            !ReadU32LE(bytes, file_size, header_offset + 16, &sections[index].size_of_raw_data) ||
            !ReadU32LE(bytes, file_size, header_offset + 20, &sections[index].pointer_to_raw_data)) {
            free(sections);
            return 0;
        }
    }

    *out_section_count = section_count;
    *out_sections = sections;
    return 1;
}

static int VirtualAddressToFileOffset(uint32_t virtual_address, const PeSectionHeader *sections, size_t section_count, size_t file_size, size_t *out_offset)
{
    uint32_t rva = virtual_address - MAINMENU_LAYOUT_VA_BASE;
    size_t index;

    for (index = 0; index < section_count; ++index) {
        uint32_t span = sections[index].virtual_size > sections[index].size_of_raw_data
            ? sections[index].virtual_size
            : sections[index].size_of_raw_data;
        if (rva >= sections[index].virtual_address && rva < sections[index].virtual_address + span) {
            size_t offset = (size_t)sections[index].pointer_to_raw_data + (size_t)(rva - sections[index].virtual_address);
            if (offset > file_size) {
                return 0;
            }
            *out_offset = offset;
            return 1;
        }
    }

    return 0;
}

static int ReadNullTerminatedBig5String(const unsigned char *bytes, size_t file_size, size_t offset, size_t max_size, char *dst, size_t dst_size)
{
    size_t length = 0;

    while (length < max_size && offset + length < file_size && bytes[offset + length] != 0) {
        length += 1;
    }

    return DecodeBig5String(bytes + offset, length, dst, dst_size);
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

void FreeXmgResource(XmgResource *resource)
{
    unsigned int group_index;

    if (resource->groups != NULL) {
        for (group_index = 0; group_index < resource->group_count; ++group_index) {
            XmgGroup *group = &resource->groups[group_index];
            unsigned int frame_index;
            for (frame_index = 0; frame_index < group->frame_count; ++frame_index) {
                free(group->frames[frame_index].pixels);
                group->frames[frame_index].pixels = NULL;
                free(group->frames[frame_index].mask_bytes);
                group->frames[frame_index].mask_bytes = NULL;
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

void FreeMainMenuLayout(MainMenuLayout *layout)
{
    ZeroMemory(layout, sizeof(*layout));
}

int LoadMainMenuLayoutFromExe(const char *exe_relative_path, MainMenuLayout *out_layout)
{
    char path[MAX_PATH];
    unsigned char *bytes = NULL;
    size_t file_size = 0;
    size_t section_count = 0;
    PeSectionHeader *sections = NULL;
    size_t offset;
    unsigned int index;

    snprintf(path, sizeof(path), "..\\%s", exe_relative_path);
    FreeMainMenuLayout(out_layout);

    if (!LoadFileBytes(path, &bytes, &file_size) || !LoadPeSections(bytes, file_size, &section_count, &sections)) {
        free(bytes);
        return 0;
    }

    if (!VirtualAddressToFileOffset(MAINMENU_LAYOUT_VERSION_MAJOR_VA, sections, section_count, file_size, &offset) ||
        !ReadU32LE(bytes, file_size, offset, &out_layout->version_major) ||
        !VirtualAddressToFileOffset(MAINMENU_LAYOUT_VERSION_MINOR_VA, sections, section_count, file_size, &offset) ||
        !ReadU32LE(bytes, file_size, offset, &out_layout->version_minor) ||
        !VirtualAddressToFileOffset(MAINMENU_LAYOUT_TITLE_VA, sections, section_count, file_size, &offset) ||
        !ReadNullTerminatedBig5String(bytes, file_size, offset, 31, out_layout->title_text, sizeof(out_layout->title_text)) ||
        !VirtualAddressToFileOffset(MAINMENU_LAYOUT_ADMIN_VA, sections, section_count, file_size, &offset) ||
        !ReadNullTerminatedBig5String(bytes, file_size, offset, 31, out_layout->admin_text, sizeof(out_layout->admin_text)) ||
        !VirtualAddressToFileOffset(MAINMENU_LAYOUT_RECORDS_VA, sections, section_count, file_size, &offset)) {
        free(sections);
        free(bytes);
        FreeMainMenuLayout(out_layout);
        return 0;
    }

    out_layout->entry_count = MAINMENU_LAYOUT_ENTRY_COUNT;
    for (index = 0; index < MAINMENU_LAYOUT_ENTRY_COUNT; ++index) {
        size_t record_offset = offset + (size_t)index * 0x60u;
        MainMenuLayoutEntry *entry = &out_layout->entries[index];
        if (!ReadS32LE(bytes, file_size, record_offset + 0x00, &entry->final_x) ||
            !ReadS32LE(bytes, file_size, record_offset + 0x04, &entry->final_y) ||
            !ReadS32LE(bytes, file_size, record_offset + 0x08, &entry->current_x) ||
            !ReadS32LE(bytes, file_size, record_offset + 0x0c, &entry->current_y) ||
            !ReadS32LE(bytes, file_size, record_offset + 0x10, &entry->settled_flag) ||
            !ReadS32LE(bytes, file_size, record_offset + 0x14, &entry->enabled_flag) ||
            !ReadNullTerminatedBig5String(bytes, file_size, record_offset + 0x18, 0x34u, entry->long_label, sizeof(entry->long_label)) ||
            !ReadS32LE(bytes, file_size, record_offset + 0x4c, &entry->intro_counter) ||
            !ReadNullTerminatedBig5String(bytes, file_size, record_offset + 0x50, 0x10u, entry->short_label, sizeof(entry->short_label))) {
            free(sections);
            free(bytes);
            FreeMainMenuLayout(out_layout);
            return 0;
        }
        entry->start_x = entry->current_x;
        entry->start_y = entry->current_y;
    }

    free(sections);
    free(bytes);
    return 1;
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

int LoadXmgResource(const char *relative_path, XmgResource *out_resource)
{
    char path[MAX_PATH];
    unsigned char *bytes = NULL;
    size_t file_size = 0;
    size_t offset = 0;
    uint16_t group_count;
    unsigned int group_index;

    snprintf(path, sizeof(path), "..\\%s", relative_path);
    FreeXmgResource(out_resource);

    if (!LoadFileBytes(path, &bytes, &file_size) || file_size < 2) {
        return 0;
    }

    group_count = (uint16_t)(bytes[0] | (bytes[1] << 8));
    offset = 2;
    out_resource->groups = (XmgGroup *)calloc(group_count, sizeof(XmgGroup));
    if (out_resource->groups == NULL) {
        free(bytes);
        return 0;
    }
    out_resource->group_count = group_count;

    for (group_index = 0; group_index < group_count; ++group_index) {
        uint16_t frame_count;
        XmgGroup *group;
        unsigned int frame_index;
        unsigned int max_width = 0;
        unsigned int max_height = 0;

        if (offset + 2 > file_size) {
            free(bytes);
            FreeXmgResource(out_resource);
            return 0;
        }

        frame_count = (uint16_t)(bytes[offset] | (bytes[offset + 1] << 8));
        offset += 2;

        group = &out_resource->groups[group_index];
        group->frame_count = frame_count;
        group->frames = (XmgFrame *)calloc(frame_count, sizeof(XmgFrame));
        if (group->frames == NULL) {
            free(bytes);
            FreeXmgResource(out_resource);
            return 0;
        }

        for (frame_index = 0; frame_index < frame_count; ++frame_index) {
            XmgFrame *frame = &group->frames[frame_index];
            uint16_t x;
            uint16_t y;
            uint16_t width_field;
            unsigned int payload_words;
            int has_nonzero = 0;

            if (offset + 6 > file_size) {
                free(bytes);
                FreeXmgResource(out_resource);
                return 0;
            }

            x = (uint16_t)(bytes[offset] | (bytes[offset + 1] << 8));
            y = (uint16_t)(bytes[offset + 2] | (bytes[offset + 3] << 8));
            width_field = (uint16_t)(bytes[offset + 4] | (bytes[offset + 5] << 8));
            payload_words = width_field & 0x7fffu;
            offset += 6;

            frame->x = x;
            frame->y = y;
            frame->width = payload_words;
            frame->height = 1;
            frame->has_alt_mask = (width_field & 0x8000u) != 0;
            frame->pixels = (unsigned int *)calloc(payload_words, sizeof(unsigned int));
            if (frame->pixels == NULL || offset + (size_t)payload_words * 2u > file_size) {
                free(bytes);
                FreeXmgResource(out_resource);
                return 0;
            }

            {
                unsigned int pixel_index;
                const unsigned char *payload = bytes + offset;
                for (pixel_index = 0; pixel_index < payload_words; ++pixel_index) {
                    uint16_t pixel = (uint16_t)(payload[pixel_index * 2] | (payload[pixel_index * 2 + 1] << 8));
                    unsigned int rgb = ExpandRgb565ToXrgb32(pixel);
                    frame->pixels[pixel_index] = rgb;
                    if (pixel != 0) {
                        has_nonzero = 1;
                    }
                }
            }
            offset += (size_t)payload_words * 2u;

            if (frame->has_alt_mask) {
                unsigned int pixel_index;
                if (offset + payload_words > file_size) {
                    free(bytes);
                    FreeXmgResource(out_resource);
                    return 0;
                }
                frame->mask_bytes = (unsigned char *)malloc(payload_words);
                if (frame->mask_bytes == NULL) {
                    free(bytes);
                    FreeXmgResource(out_resource);
                    return 0;
                }
                memcpy(frame->mask_bytes, bytes + offset, payload_words);
                for (pixel_index = 0; pixel_index < payload_words; ++pixel_index) {
                    unsigned char mask = frame->mask_bytes[pixel_index];
                    if (mask == 0) {
                        frame->pixels[pixel_index] = 0;
                    } else {
                        unsigned int rgb = frame->pixels[pixel_index];
                        unsigned int red = (rgb >> 16) & 0xffu;
                        unsigned int green = (rgb >> 8) & 0xffu;
                        unsigned int blue = rgb & 0xffu;
                        red = (red * (unsigned int)mask) / 255u;
                        green = (green * (unsigned int)mask) / 255u;
                        blue = (blue * (unsigned int)mask) / 255u;
                        frame->pixels[pixel_index] = (red << 16) | (green << 8) | blue;
                    }
                }
                offset += payload_words;
                group->alt_frame_count += 1;
            }

            if (has_nonzero) {
                group->nonzero_frame_count += 1;
            }

            if (frame->x + frame->width > max_width) {
                max_width = frame->x + frame->width;
            }
            if (frame->y + 1u > max_height) {
                max_height = frame->y + 1u;
            }
        }

        group->max_width = max_width;
        group->max_height = max_height;
        for (frame_index = 0; frame_index < frame_count; ++frame_index) {
            group->frames[frame_index].height = max_height;
        }
    }

    free(bytes);
    return offset <= file_size;
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
        group->min_payload_words = 0xffffffffu;
        group->min_x = 0xffffffffu;
        group->min_y = 0xffffffffu;
        group->max_width_field = 0;
        group->max_payload_words = 0;
        group->max_x = 0;
        group->max_y = 0;

        for (frame_index = 0; frame_index < frame_count; ++frame_index) {
            uint16_t x;
            uint16_t y;
            uint16_t width_field;
            unsigned int payload_words;

            if (offset + 6 > file_size) {
                free(bytes);
                FreeXmgDiagnostic(out_diagnostic);
                return 0;
            }

            x = (uint16_t)(bytes[offset] | (bytes[offset + 1] << 8));
            y = (uint16_t)(bytes[offset + 2] | (bytes[offset + 3] << 8));
            width_field = (uint16_t)(bytes[offset + 4] | (bytes[offset + 5] << 8));
            payload_words = width_field & 0x7fffu;
            if (width_field < group->min_width_field) {
                group->min_width_field = width_field;
            }
            if (width_field > group->max_width_field) {
                group->max_width_field = width_field;
            }
            if (payload_words < group->min_payload_words) {
                group->min_payload_words = payload_words;
            }
            if (payload_words > group->max_payload_words) {
                group->max_payload_words = payload_words;
            }
            if (x < group->min_x) {
                group->min_x = x;
            }
            if (x > group->max_x) {
                group->max_x = x;
            }
            if (y < group->min_y) {
                group->min_y = y;
            }
            if (y > group->max_y) {
                group->max_y = y;
            }
            group->total_payload_words += payload_words;

            if ((width_field & 0x8000u) != 0) {
                group->alt_frame_count += 1;
                out_diagnostic->total_alt_frame_count += 1;
                group->total_mask_bytes += payload_words;
                offset += 6u + (size_t)payload_words * 3u;
            } else {
                offset += 6u + (size_t)payload_words * 2u;
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
        if (group->min_payload_words == 0xffffffffu) {
            group->min_payload_words = 0;
        }
        if (group->min_x == 0xffffffffu) {
            group->min_x = 0;
        }
        if (group->min_y == 0xffffffffu) {
            group->min_y = 0;
        }
    }

    out_diagnostic->trailing_size = (unsigned int)(file_size - offset);
    free(bytes);
    return 1;
}
