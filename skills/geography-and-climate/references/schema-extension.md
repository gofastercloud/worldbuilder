# Location schema extension: climate, flora, fauna, resources

All fields are optional and added to the existing location schema (`assets/templates/locations/_schema.yaml`; commented examples in `_template.md`). Existing fields keep their meaning. The legacy `climate` string (for example `"cool temperate"`) stays valid and should continue to hold a short human summary; `climate_profile` is the structured version.

## New fields

| Field | Type | Meaning |
|---|---|---|
| `terrain` | string | Dominant terrain: plains, hills, mountain, desert, wetland, forest, coast, ice, volcanic... |
| `elevation_m` | number | Typical height in metres above sea level |
| `area_km2` | number | Approximate area (for carrying capacity) |
| `climate_profile` | object | See below |
| `hydrology` | object | `flows_to` (slug of river, lake or sea), `freshwater` (abundant, seasonal, scarce), `source_of` |
| `flora`, `fauna` | list | Entries with `species` (slug) or `name`, plus `role`, `notes` |
| `resources` | list | Existing string list; items may also be objects `{name, category, rarity, notes}` (economy enums) |

### climate_profile

```yaml
climate_profile:
  zone: continental            # tropical, arid, semi-arid, mediterranean, temperate, continental, subarctic, polar, alpine, custom
  temperature_c: { spring: [2, 12], summer: [14, 26], autumn: [3, 13], winter: [-12, -2] }
  precipitation_mm: 550        # mean annual
  rain_pattern: summer-wet     # even, summer-wet, winter-wet, monsoon, storm-track, rain-shadow, none
  seasons:
    - { name: "long winter", length: "5 months", character: "snow cover, rivers frozen" }
  growing_season_days: 130     # frost-free days
  hazards:
    - { name: "blizzard", season: winter, frequency: "most years", effect: "passes closed 2 to 6 weeks" }
  drivers:                     # WHY: causes, so the result can be checked
    - "latitude 52 degrees"
    - "interior of the continent, 1100 km from the sea"
    - "rain shadow of the Greywall range (westerlies)"
```

Rules: temperatures are ranges `[low, high]` of mean daily temperature per season in degrees Celsius (or the world's stated scale, noted once in `project.yaml`). Seasons follow the world's `physics.seasons` flag; when the flag says `none`, omit `seasons` and keep the temperature range narrow. `drivers` should name concrete things that exist in the world (a range, a current, a parent) and must be consistent with those entities.

### flora and fauna

```yaml
flora:
  - { name: "winter rye", role: staple-crop }
  - { species: "silverbark-pine", role: timber, notes: "above 400 m" }
fauna:
  - { species: "ridge-wolf", role: apex-predator }
  - { name: "grain weevil", role: pest, notes: "after wet summers" }
  - { species: "plains-ox", role: domesticate }
```

- Use `species:` with the slug of an existing species entity when the organism is an entity; the validator warns about a dangling `species:` slug. That dangling-reference check covers the slugs in `climate_profile`, `hydrology`, `flora` and `fauna` only; it does not check `resources` names or free text. Otherwise use `name:` with a short label.
- Roles: flora `staple-crop, cash-crop, timber, forage, medicinal, resource, hazard, invasive, keystone, ornamental`; fauna `apex-predator, predator, prey, pest, domesticate, draft-animal, game, fishery, resource, hazard, keystone, migratory`.
- Keep lists short (3 to 8 meaningful entries); list what matters for people, food, danger and trade.

### resources (agricultural and mineral)

```yaml
resources:
  - "salt"                                  # legacy form still works
  - { name: "iron-ore", category: raw-material, rarity: common, notes: "Greywall foothills" }
  - { name: "winter-wheat", category: food, rarity: abundant }
```

This is the ONE resource shape, shared with the economy skill. `category` is one of `raw-material, food, luxury, strategic, magical, knowledge, labor, currency, fuel, custom`; `rarity` is one of `abundant, common, uncommon, rare, very-rare, unique` (definitions in `assets/templates/economy/_schema.yaml`). Use the economy resource slug as `name` where an economy file defines it. The older `kind` and `abundance` fields are not written any more (mapping: mineral or timber to raw-material, agricultural to food, energy to fuel; surplus to abundant, rich to common, scarce to rare). `magical` is only for worlds where `magic.present` is true.

## Inheritance

A location without its own `climate_profile` inherits its parent's. A location that sets one overrides only what it states (children do not need to repeat every key). Always write `drivers` for what you override: for example, a mountain town sets `temperature_c` lower than its parent and drivers `["altitude 1800 m, about 11 C below the plain"]`.

## Consistency expectations

- `elevation_m` of a child is plausible against its parent and against neighbours; a river's `flows_to` has a lower or equal `elevation_m` (the validator warns when it does not) and `flows_to` chains never loop (the validator reports a cycle as an error).
- `growing_season_days` and `temperature_c` agree (a winter low below -10 C with a 300-day season is a mismatch).
- `precipitation_mm` and `zone` agree (a `tropical` zone with 150 mm is wrong unless justified in drivers).
- `fauna` roles contain prey before predators; predators do not outnumber prey entries.
