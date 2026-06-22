# Remaining Uncertainties

This is the current list of fields and naming choices that remain uncertain
after the first semantic recovery pass. They are intentionally kept separate
from `STRUCTURE_NOTES.md` so the applied names stay evidence-grounded.

## City Fields

These names are useful but not yet final:

| Field | Current name | Why uncertain |
|---:|---|---|
| `City +0x2e` | `owner_or_active_flag` | It indexes threshold tables and is set to `1` for AI processing, so it may be owner, city status, or resource mode rather than a pure owner id. |
| `City +0x30` | `growth_or_industry_score` | Used with business/safety thresholds for events, but exact UI label is not confirmed. |
| `City +0x4c` | `business_score` | Strongly supported by `City_Business` strings and thresholds, but could be broader economy/prosperity. |
| `City +0x50` | `safety_score` | Paired with `City_Safe_Change`; exact label may be public order/security. |
| `City +0x54` | `science_or_resource_score` | Used in upgrade/worker logic; exact label remains unclear. |
| `City +0x64..0xa4` | `building_status` | The array shape and completed value are strongly supported, but individual building IDs still need correlation with `DAT_005998..` tables or UI labels. |
| `City +0xa5..0xbd` | `special_project_status` | The array shape is strong; whether these are wonders, global projects, or another special city-building class needs UI/table correlation. |
| `City +0xbe` | `has_special_capability` | It gates special construction/production classes, but the exact gameplay label is unknown. |
| `City +0xcc` | `population_or_stockpile` | Used as a production/population threshold; needs UI correlation. |
| `City +0xd4` | `building_income_yield` | Strongly behaves like a city income/yield subtotal from completed buildings, but the exact resource column is not confirmed. |
| `City +0xd8..0xff` | build queue fields | The queue shape and shifting are clear, but whether the two byte arrays are map coordinates, placement slots, or UI selector coordinates varies by queue item type. |
| `City +0xd6` | `collapse_delay_or_army_count` | Checked before removing an empty AI city; exact meaning unknown. |
| `City +0x16a..0x16f` | worker bucket names | Directions are clear from reallocation logic, but mapping to UI job labels needs image/text table correlation. |

## Country Fields

| Field | Current name | Why uncertain |
|---:|---|---|
| `Country +0x688` | `science_budget_or_treasury` | It pays for city upgrades; could be treasury, science, or a mixed resource. |
| `Country +0x698` | `population_or_score_total` | Receives removed-city stored value; exact aggregate label unknown. |
| `Country +0x6a0..0x6a3` | efficiency/resource level names | They clearly scale or index resource, construction, research, and positive cash/resource deltas, but the exact UI/stat labels are not confirmed. |
| `Country +0x6a4..0x713` | `science_status` | Value `2` means completed/unlocked. The typed prefix covers early entries; later science ids are still reached by raw country-base arithmetic because the full 200-entry logical table overlaps other confirmed country fields in the decompiler type view. |
| `Country +0x714` | `country_state_mode` | A mode value used in city event conditions, not yet tied to UI labels. |
| `Country +0x9d4..0xa14` | `available_building_flags` | Strongly per-building availability, but individual IDs and the relation to science/building tables are still inferred. |
| `Country +0xa15..0xa2d` | `available_special_project_flags` | Strong special-project availability shape, exact project class/name not confirmed. |
| `Country +0xa2f..0xa86` | `trainable_army_flags` | Clearly indexed by army/unit build mode, but exact state values need more production UI tracing. |

## LandTile Fields

| Field | Current name | Why uncertain |
|---:|---|---|
| `LandTile +0x10` | `linked_count_or_city_count` | Count-like, but the counted object depends on load/repair branch. |
| `LandTile +0x28` | `army_or_city_ptrs_a` | Pointer list used during occupant repair; exact occupant type is branch-dependent. |
| `LandTile +0x50` | `army_count_or_occupant_count` | Strongly count-like; UI/gameplay meaning needs correlation with map rendering. |
| `LandTile +0x54` | `army_or_city_ptrs_b` | Secondary pointer list; exact role needs more battle/map tracing. |
| `LandTile +0x7c` | `secondary_occupant_count` | Count-like and paired with the primary occupant count, but whether it means defenders, queued units, or a second occupant class is not fully proven. |
| `LandTile +0x88` | `linked_record` | Dereferenced during load repair; target struct not fully identified. |

## Battle Types

- `BattleUnit_approx` only names the fields directly proven by battle-grid
  indexing: `battle_x`, `battle_y`, and `army_type`.
- The two grids named `g_battle_grid_front_units` and
  `g_battle_grid_back_units` are known to be 24-wide from repeated `0x18`
  indexing, but exact dimensions and cell structure are not fully recovered.
- `g_army_type_table` has a stable `0x100` stride, but only a few offsets have
  been correlated from battle/load code.

## UI And Render Types

- DirectDraw globals are named, but COM interface types are still represented
  as `void *` because this export does not import/apply DirectDraw type
  libraries.
- `g_draw_sprite_fn` is named from call behavior. Its exact function signature
  is still inferred from call sites and should be formalized after reviewing
  `.EMG`/`.XMG` resource structs.
- Resource helper names such as `Load_EMG_Resource`, `Load_XMG_Resource`,
  `Free_EMG_Resource`, and `Free_XMG_Resource` are behavior-derived from
  filename arguments and paired free calls; their exact resource-handle structs
  remain unrecovered.
- `Format_Text` is almost certainly a sprintf-style formatter from broad call
  shape, but its varargs signature is not expressible in the current recovered
  type pass.

## Next Productive Manual Pass

The most valuable next pass would be to extract table labels around
`DAT_005998..`, `DAT_005a1a..`, `DAT_005817..`, `UI_String.EMG`, and
`UI_CITY.EMG`. That would let the building/science/special-project arrays and
the ambiguous worker/stat labels become confirmed UI labels instead of
behavior-derived names.
