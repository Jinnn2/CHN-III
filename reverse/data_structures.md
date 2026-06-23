# Data Structures

These are working structure sketches, not original source headers. Field names
are evidence-based where possible; uncertain fields should stay `unknown_*`
until a caller, editor label, file format, or trace string proves the meaning.

## MapTile / `LandTile_0x100`

Evidence: `Load_Dat` copies tile records in `0x100`-byte strides; map editor,
decode, city, resource, and battle paths read these offsets.

```c
struct LandTile_0x100 {
    /* +0x00 */ uint8_t terrain_kind;
    /* +0x01 */ uint8_t terrain_layer_or_special_flag; // still broad
    /* +0x02 */ uint8_t alternate_battle_terrain_kind;
    /* +0x03 */ uint8_t terrain_detail_or_battle_mode;
    /* +0x04 */ uint16_t terrain_sprite_id; // inferred from decode paths
    /* +0x06 */ uint8_t unknown_06[0x0d];
    /* +0x13 */ uint8_t road_or_bridge_state; // maybe road/bridge overlay
    /* +0x14 */ uint8_t road_detail_sprite_id_a;
    /* +0x15 */ uint8_t road_detail_sprite_id_b;
    /* +0x16 */ uint8_t battle_resource_or_feature_id;
    /* +0x17 */ uint8_t city_resource_or_feature_id;
    /* +0x18 */ uint8_t city_resource_or_feature_stockpile; // exact width needs verification
    /* +0x19 */ uint8_t unknown_19;
    /* +0x1a */ uint8_t map_work_kind;
    /* +0x1b */ uint8_t map_work_progress_or_state;
    /* +0x1c */ uint8_t unknown_1c[0x08];
    /* +0x24 */ uint8_t long_wall_state;
    /* +0x25 */ uint8_t unknown_25[0x0b];
    /* +0x30 */ void *linked_record; // city/object pointer in many paths
    /* +0x34 */ void *unknown_ptr_34;
    /* +0x38 */ void *army_or_city_ptrs_a[10];
    /* +0x60 */ void *army_or_city_ptrs_b[10];
    /* +0x88 */ uint8_t army_count_or_occupant_count;
    /* +0x89 */ uint8_t owner_country_or_visibility_a; // tool 9 likely proves this later
    /* +0x8a */ uint8_t owner_country_or_visibility_b; // tool 9 likely proves this later
    /* +0x8b */ uint8_t unknown_8b[0x2d];
    /* +0xb8 */ int16_t editor_named_point_index_a;
    /* +0xba */ int16_t editor_named_point_index_b;
    /* +0xbc */ uint8_t unknown_bc[0x3c];
    /* +0xf8 */ uint8_t city_resource_stockpile_or_amount;
    /* +0xf9 */ uint8_t unknown_f9[0x07];
};
```

## City / `City_0x1b8_plus`

Evidence: `Do_City` traverses the city linked list; `Load_Dat` links records
through `+0x1b4`; x/y live at `+0x16/+0x18`; names start near `+0x03`.

```c
struct City_0x1b8_plus {
    /* +0x00 */ uint8_t status_or_id;
    /* +0x01 */ uint8_t owner_country_id;
    /* +0x02 */ uint8_t unknown_02;
    /* +0x03 */ char name[0x13]; // approximate, verify terminator/encoding
    /* +0x16 */ uint16_t tile_x;
    /* +0x18 */ uint16_t tile_y;
    /* +0x1a */ uint8_t unknown_1a[0x4e];
    /* +0x68 */ int32_t income_or_turn_delta; // candidate family
    /* +0x6c */ int32_t food_or_turn_delta; // candidate family
    /* +0x70 */ int32_t resource_or_turn_delta; // candidate family
    /* +0x74 */ uint8_t unknown_74[0x140];
    /* +0x1b4 */ struct City_0x1b8_plus *next_city;
};
```

## Country / `CountryState_0xe68`

Evidence: `Load_Dat` copies/iterates `0xe68`-byte country records; active
country pointer is `g_country_states + g_active_country_index * 0xe68`.

```c
struct CountryState_0xe68 {
    /* +0x000 */ uint8_t status_or_enabled;
    /* +0x001 */ uint8_t country_id;
    /* +0x002 */ uint8_t unknown_002;
    /* +0x003 */ uint8_t profile_id; // indexes CountryProfileDef_0x7c
    /* +0x004 */ uint8_t unknown_004[0x69d];
    /* +0x6a1 */ uint8_t efficiency_level_a;
    /* +0x6a2 */ uint8_t efficiency_level_b;
    /* +0x6a3 */ uint8_t efficiency_level_c;
    /* +0x6a4 */ uint8_t unknown_6a4[0x7c4];
};
```

## Army / Unit

Evidence: map tile occupant arrays point to army-like records; battle and order
paths use `ArmyUnit_0x164_plus`; static unit definitions are
`ArmyTypeDef_0x400[91]`.

```c
struct ArmyUnit_0x164_plus {
    /* +0x000 */ uint8_t status_or_presence;
    /* +0x001 */ uint8_t owner_country_id;
    /* +0x002 */ uint8_t army_type_id;
    /* +0x003 */ uint8_t map_presence_or_cargo_state;
    /* +0x004 */ uint8_t unknown_004[0x20];
    /* +0x024 */ uint16_t tile_x;
    /* +0x026 */ uint16_t tile_y;
    /* +0x028 */ uint8_t unknown_028[0x20];
    /* +0x048 */ uint8_t mission_action_id;
    /* +0x049 */ uint8_t order_event_or_result;
    /* +0x04a */ uint8_t direction;
    /* +0x04b */ uint8_t unknown_04b[0x19];
    /* +0x064 */ struct ArmyUnit_0x164_plus *transport_parent;
    /* +0x068 */ struct ArmyUnit_0x164_plus *related_army;
    /* +0x06c */ uint8_t unknown_06c[0xf8];
};

struct ArmyTypeDef_0x400 {
    /* +0x000 */ uint8_t enabled_or_id;
    /* +0x001 */ uint8_t unit_class; // 0 land, 1 air-like, other special in battle code
    /* +0x002 */ uint8_t unknown_002[0x3fe];
};
```

## Resource

Evidence: `Load_Dat` copies 40 `0xd8` records from `g_city_resource_defs`;
`Resource_Able`, map editor tool `6`, and `Cal_City_Resource` index the table.

```c
struct CityResourceDef_0xd8 {
    /* +0x00 */ uint8_t enabled_or_id;
    /* +0x01 */ uint8_t placement_or_resource_class;
    /* +0x02 */ uint8_t requires_battle_feature_or_clearable;
    /* +0x03 */ uint8_t unknown_03;
    /* +0x04 */ uint8_t terrain_compatibility_by_kind[0x10]; // approximate
    /* +0x14 */ uint8_t unknown_14[0xc4];
};
```

## Building

Evidence: building table begins at `0x005997b8`; UI/editor/city production use
`building_id * 0x200`.

```c
struct BuildingDef_0x200 {
    /* +0x000 */ uint8_t enabled_or_id;
    /* +0x001 */ uint8_t unknown_001[0x1ff];
};
```

## Technology

Evidence: science table begins at `0x005817a8`; records use `0x88` stride;
science editor and `Science_Next` expose prerequisites and priority weights.

```c
struct ScienceDef_0x88 {
    /* +0x00 */ uint8_t enabled_or_id;
    /* +0x01 */ uint8_t prerequisite_id_a;
    /* +0x02 */ uint8_t prerequisite_id_b;
    /* +0x03 */ uint8_t unknown_03[0x85];
};
```

## Government

Evidence: `Load_Dat` copies `0x3a0` bytes, 8 records of `0x74`;
`Before_Edit_Goverment` binds editor controls to this table.

```c
struct GovernmentDef_0x74 {
    /* +0x00 */ uint8_t enabled_or_id;
    /* +0x01 */ uint8_t unknown_01[0x73];
};
```

## Ground / Terrain

Evidence: `Load_Dat` copies `0x21c` bytes, 15 records of `0x24`;
`Before_Edit_Ground` edits this table.

```c
struct GroundDef_0x24 {
    /* +0x00 */ uint8_t terrain_kind;
    /* +0x01 */ uint8_t unknown_01[0x23];
};
```

## UIWindow / UIButton / UISprite

Evidence: data-format list functions operate on linked UI/control records;
EMG/XMG image banks feed `g_draw_sprite_fn`. Exact object shapes are not ready.

```c
struct DataFormatNode {
    /* +0x00 */ struct DataFormatNode *prev_or_next_a;
    /* +0x04 */ struct DataFormatNode *prev_or_next_b;
    /* +0x08 */ uint8_t unknown_08[0x18];
};

struct SpriteBankHandle {
    /* +0x00 */ void *resource_or_group_table;
    /* +0x04 */ int32_t group_count_or_handle;
    /* +0x08 */ void *frame_table_or_pixels;
};
```

## Load DAT Memory Stream / SaveGame

Evidence: `Load_Dat` contains decompression/memory-buffer strings and rebuilds
land, city, army, country, named-point, and static-definition tables. The file
container is not yet modeled as a single struct. The best current model is a
gzip-style payload with a fixed-order memory stream.

```c
struct LoadDatMemoryStream_candidate {
    /* +0x000000 */ ScienceDef_0x88 science_defs[200];
    /* +0x006a40 */ ArmyTypeDef_0x400 army_type_defs[91];
    /* +0x01d640 */ uint8_t building_defs_block[0xc000]; // stride/count still being reconciled
    /* +0x029640 */ CountryProfileDef_0x7c country_profile_defs[100];
    /* +0x02c6b0 */ GovernmentDef_0x74 government_defs[8];
    /* +0x02ca50 */ GroundDef_0x24 ground_defs[15];
    /* +0x02cc6c */ CityResourceDef_0xd8 city_resource_defs[40];
    /* +0x02ee2c */ uint8_t flag_image_blocks[100][0x100];
    /* +varies */ LandTile_0x100 land_tiles[map_width * map_height];
    /* +varies */ int32_t view_center_x;
    /* +varies */ int32_t view_center_y;
    /* +varies */ int32_t land_record_count;
    /* +varies */ EmpireCountryDef_0x200 empire_country_defs[100];
    /* +varies */ CountryState_0xe68 country_states[22]; // Load_Dat copies 22 records
    /* +varies */ int32_t unknown_country_or_turn_fields[2];
    /* +varies */ int32_t human_country_index;
    /* +varies */ uint8_t city_section_marker[5];
    /* +varies */ int32_t expected_city_count;
    /* +varies */ CityFileRecord_0x200 city_records[];
    /* +varies */ uint8_t army_section_marker[5];
    /* +varies */ int32_t expected_army_count;
    /* +varies */ ArmyFileRecord_0x200 army_records_and_cargo[];
    /* +varies */ uint8_t die_section_marker[5];
    /* +varies */ int32_t die_record_count;
    /* +varies */ DieRecord_0x20 die_records[];
    /* +varies */ uint8_t business_section_marker[5];
    /* +varies */ int32_t business_record_count;
    /* +varies */ BusinessRecord_0x100 business_records[];
    /* +varies */ int32_t map_bookmark_slots[20];
};

struct DieRecord_0x20 {
    /* +0x00 */ uint8_t unknown_00[0x20];
    /* +0x18 */ uint32_t runtime_next_or_link; // cleared by Load_Dat
    /* +0x1c */ uint32_t runtime_aux_or_link;  // cleared by Load_Dat
};

struct BusinessRecord_0x100 {
    /* +0x00 */ uint32_t unknown_00;
    /* +0x04 */ City_0x1b8_plus *source_city; // resolved from source tile
    /* +0x08 */ City_0x1b8_plus *dest_city;   // resolved from destination tile
    /* +0x0c */ uint8_t unknown_0c[0xd0];
    /* +0xdc */ struct BusinessRecord_0x100 *next_business_candidate;
    /* +0xe0 */ uint8_t unknown_e0[0x20];
};
```

Open questions:

- The direct header/check data before the compressed payload is not yet
  structurally modeled.
- `g_country_states` reserves more space elsewhere, but `Load_Dat` copies
  `0x13cf0` bytes, exactly 22 `0xe68` records.
- City and army file records are read as `0x200` bytes even when runtime
  structures use only part of that space plus cleared pointer fields.

## EMG / XMG Resource

Evidence: `STRUCTURE_NOTES.md` currently describes EMG/XMG as group/frame
containers; `Load_EMG_Resource`, `Load_XMG_Resource`, and `emg_probe.py` are
the best references.

```c
struct EmgResource_candidate {
    /* +0x00 */ uint16_t group_count;
    /* +0x02 */ uint16_t unknown_02;
    /* varies */ /* group headers and frame records */
};
```

## Next Structure Work

- Trace map editor tool `9` before naming owner/visibility bytes in
  `LandTile_0x100`.
- Use editor table setup functions to replace `unknown_*` fields in static
  definitions with UI-label-backed names.
- For each future function note, record globals read, globals written, and key
  calls before changing structure names.
