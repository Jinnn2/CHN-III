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
| `City +0xcc` | `population_or_stockpile` | Used as a production/population threshold; needs UI correlation. |
| `City +0xd6` | `collapse_delay_or_army_count` | Checked before removing an empty AI city; exact meaning unknown. |
| `City +0x16a..0x16f` | worker bucket names | Directions are clear from reallocation logic, but mapping to UI job labels needs image/text table correlation. |

## Country Fields

| Field | Current name | Why uncertain |
|---:|---|---|
| `Country +0x688` | `science_budget_or_treasury` | It pays for city upgrades; could be treasury, science, or a mixed resource. |
| `Country +0x698` | `population_or_score_total` | Receives removed-city stored value; exact aggregate label unknown. |
| `Country +0x714` | `country_state_mode` | A mode value used in city event conditions, not yet tied to UI labels. |
| `Country +0x9c4` | `build_or_draft_capacity` | Controls construction-worker allocation, but the exact strategic resource is unclear. |

## LandTile Fields

| Field | Current name | Why uncertain |
|---:|---|---|
| `LandTile +0x10` | `linked_count_or_city_count` | Count-like, but the counted object depends on load/repair branch. |
| `LandTile +0x28` | `army_or_city_ptrs_a` | Pointer list used during occupant repair; exact occupant type is branch-dependent. |
| `LandTile +0x50` | `army_count_or_occupant_count` | Strongly count-like; UI/gameplay meaning needs correlation with map rendering. |
| `LandTile +0x54` | `army_or_city_ptrs_b` | Secondary pointer list; exact role needs more battle/map tracing. |
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

## Next Productive Manual Pass

The most valuable next pass would be to correlate `UI_String.EMG`,
`UI_CITY.EMG`, and city screen text with the `City_0x1b8_plus` worker/stat
fields. That would let the ambiguous worker/stat labels become confirmed UI
labels instead of behavior-derived names.
