---
name: "{{NAME}}"
aliases: []
type: city
parent: ""
coordinates: {}
climate: ""
population: ""
faction: ""
notable_characters: []
routes:
  # - to: "other-location"
  #   route_type: major
  #   bidirectional: true
  #   methods:             # mode uses the enum in _schema.yaml; economy trade_routes use the same
  #     - mode: horse
  #       travel_time: "2 days"
  #       distance: "80 miles"
  #       danger_level: low
  #     - mode: walking
  #       travel_time: "5 days"
  #       distance: "80 miles"
  #       danger_level: moderate
transport_hub: {}
resources: []          # strings, or { name: "iron-ore", category: raw-material, rarity: common, notes: "" }
dangers: []

# ─── PHYSICAL GEOGRAPHY AND CLIMATE (optional; see geography-and-climate skill) ─
# terrain: ""               # dominant terrain
# elevation_m: 0
# area_km2: 0
# climate_profile:
#   zone: temperate
#   temperature_c: { summer: [14, 24], winter: [-2, 6] }
#   precipitation_mm: 700
#   rain_pattern: even
#   seasons: [{ name: winter, length: "4 months", character: "cold, snow above 500 m" }]
#   growing_season_days: 180
#   hazards: [{ name: "winter gales", season: winter, frequency: yearly, effect: "ports close" }]
#   drivers: ["mid latitude", "westerly winds off the warm current"]
# hydrology: { flows_to: "", freshwater: abundant }
# flora:
#   - { name: "winter wheat", role: staple-crop }
# fauna:
#   - { name: "wolves", role: apex-predator }

# heraldry:
#   sigil:
#     description: ""
#     blazon: ""
#     shape: ""
#   colors:
#     primary: ""
#     secondary: ""
#     accent: ""
#   motto: ""
#   words: ""
#   banner_description: ""

# ─── REGIONAL DEFAULTS ────────────────────────────────────────────────────────
# Characters from this location inherit these traits unless they override them.
# Most useful for cities, towns, regions, kingdoms. Leave empty for landmarks/structures.
regional_defaults:
  ethnicity: ""
  appearance:
    skin_tone: ""           # e.g. "fair", "olive", "dark brown"
    hair: ""                # e.g. "red, often curly", "dark and straight"
    build: ""               # e.g. "stocky", "tall and lean"
    distinguishing: ""      # e.g. "freckles common", "ritual scarification"
  voice:
    accent: ""             # e.g. "Scottish", "Southern drawl", "clipped aristocratic"
    dialect: ""            # e.g. "formal", "archaic", "street slang"
    tags: []               # default voice tags

# ─── DESCRIPTIONS ─────────────────────────────────────────────────────────────
descriptions:
  machine:
    architecture: ""
    atmosphere: ""
    notable_features: ""
  human: ""
  image_prompt: ""

first_appearance: ""
tags: []
---

## Description
<!-- Sights, sounds, smells — what's the vibe? -->


## History


## Geography & Layout


## Culture & Customs


## Points of Interest


## Transport & Access
<!-- How do people get here? What routes connect to this place? -->


## Secrets & Hidden Features


## Notes
