# Viewer data format (version 1)

`viz_data.build_viz_data(project_dir)` returns one JSON object. `build_viewer.py` embeds it in the page in place of the marker `/*__WORLD_DATA__*/null` (so the viewer reads it as a JS object, for example `const WORLD = /*__WORLD_DATA__*/null;`). `--json-only` writes the same object to `viz.json`. Lists are sorted by id so builds are reproducible. `null` means "not in the files"; the viewer must treat every optional field as possibly null or empty. `<`, `>` and `&` are escaped as `\uXXXX` inside the page, which JSON.parse and JS literals both read normally.

## Top level

| Key | Type | Notes |
|---|---|---|
| `version` | int | `1` |
| `project` | `{name: str, present_t: number or null}` | name is `title` from project.yaml |
| `counts` | `{nodes, edges, routes, resources, trade_routes, species_index, <entity type>: int}` | per-type counts such as `event`, `location`, `character` |
| `calendar` | object | see below |
| `nodes` | list | every entity |
| `edges` | list | every relationship |
| `timeline` | `{events: [...], traditions: [...]}` | |
| `map` | `{locations: [...], routes: [...], backdrop: str or null}` | `backdrop` is an optional custom/painted map image (`output/images/world-map.*` or `project.yaml: map_image`) |
| `climate` | `{zones: [...], legend: {zone: colour}}` | |
| `life` | `{species_index: [...]}` | |
| `economy` | `{resources, trade_routes, currencies, shocks}` | |
| `content` | list | discovered stories, D&D 5e campaigns, and chapters (`stories/`, `story/chapters/`, `output/stories/`, `output/campaigns/`) |
| `warnings` | list of str | missing or sparse data, for a banner |

## calendar

```json
{"eras": [{"prefix": "CE", "name": "Contact Era", "t0": 3000, "t1": 3500, "sort_order": 2}],
 "t_min": 0, "t_max": 4305.0, "present_t": null}
```

`t` is the world timeline value: years from the start of the first era (era offset plus year plus month/day fraction). Eras are contiguous: `t0` is the end of the previous era. An open last era has `t1 = t_max`. With no calendar eras, `eras` is `[]` and `t` is the plain year. `t_min`/`t_max` bound every dated item, the eras and `present_t`. `present_t` is `null` when neither project.yaml nor calendar.yaml has `present_date`.

## nodes

`{id, type, name, t, end_t, date_label, era, summary, status, tags, image}`

```json
{"id": "ai-wars", "type": "event", "name": "The AI Wars", "t": 3250.0, "end_t": 3280.0,
 "date_label": "250 CE", "era": "Contact Era", "summary": "...(max 160 chars)", "status": null, "tags": ["war"],
 "image": "images/events/ai-wars.png"}
```

`type` is one of `character, location, faction, item, magic-system, arc, event, species, race, language, lineage, tradition`. `t`/`end_t` are null when undated; `end_t` is null for point-in-time items. `id` is the kebab-case slug. `image` is a path relative to `output/world-viewer.html` (discovered from `output/images/<type-dir>/<slug>.{png,jpg,jpeg,webp}` or an optional frontmatter `image:` field), a `data:image/...;base64,...` URI when built with `--embed-images`, or `null` when absent.

## edges

`{source, target, kind, label, field, causal, memory}`. Both ends are node ids. `causal` is true for kind `causes` (cause to effect, `t(source) <= t(target)`); `memory` is true for kind `leaves-trace` (event to tradition: the memory chain). Other kinds are structural (`parent`, `member_of`, `route`, `location`, ...). `label` may be "". `field` is the source field (for example `faction`).

## timeline

Event: `{id, name, t, end_t, significance, type, era, caused_by, leads_to, traces, participants, locations, impact, open_ended}`

- `caused_by`, `leads_to`: event ids only. `traces`: ids (usually traditions) the event left as present-day marks.
- `participants`: ids of characters, factions, species. `locations`: location ids.
- `impact`: `{economic, social, political, magical}` each a prose string or null (always all four keys).
- `open_ended`: reason string for a finished event whose effects continue, else null. `significance` and `type` are the file's strings (for example `world-changing`, `war`) or null.

Tradition: `{id, name, kind, status, fidelity, first_attested_t, origin_events, contradicts}`; `origin_events` are event ids, `contradicts` tradition ids.

## map

Location: `{id, name, type, parent, children, depth, x, y, terrain, elevation_m, area_km2, population, population_label, climate, hydrology, flora, fauna, resources, has_own_climate}`

- `parent`: location id or null (top level). `depth`: 0 for top level. `children`: ids.
- `x`, `y`: layout position, numbers in [0, 1000] (see Layout).
- `terrain`: str or null. `elevation_m`, `area_km2`: number or null.
- `population`: number parsed from the leading figure (`"~45 million permanent"` gives 45000000) or null; `population_label` is the original text.
- `climate`: null, or `{zone, temperature_c, precipitation_mm, growing_season_days, seasons, hazards, notes, inherited}`. It is the effective profile: a child inherits its parent's `climate_profile` and overrides only the keys it states; `inherited` is true when taken wholly from an ancestor. `zone` may be null. `temperature_c` is whatever the file has: usually `{spring: [lo, hi], summer: [lo, hi], ...}`, possibly a number or `[lo, hi]`. `seasons` is a list of `{name, length, character}`; `hazards` a list of `{name, season, frequency, effect}` (both `[]` when absent). `notes` is the file's `notes` or its `drivers` joined with "; ".
- `hydrology`: null or `{flows_to, freshwater, source_of}` as written.
- `flora`, `fauna`: `[{name, species, role}]`; `species` is a species id (or the raw slug if it does not resolve) or null.
- `resources`: `[{name, category, rarity}]` (category/rarity null for plain-string entries).
- `has_own_climate`: true when the file itself declares `climate_profile`.

Route: `{id, from, to, modes, goods, reciprocal}`

```json
{"id": "meridian-station--terra-prime", "from": "meridian-station", "to": "terra-prime",
 "modes": [{"mode": "shuttle", "distance": "Lagrange point", "time": "4 hours"}],
 "goods": ["Manufactured Goods"], "reciprocal": true}
```

Routes are undirected: the two declarations (A lists B, B lists A) merge into one entry with `from < to` alphabetically and `id = "<from>--<to>"`. `reciprocal` is false when only one side declares it (a validator warning too). `modes` are merged by mode name; `distance`/`time` are strings or null. `goods` are resource names carried, from economy trade routes whose `from`, `via`, `to` chain includes this leg.

### Layout

Deterministic, no randomness; the same files always give the same `x`, `y`.
1. Locations sorted by id. Top-level places (no known parent) go on a ring of radius 340 about (500, 500), starting at the top and stepping evenly in id order; a single top-level place is centred.
2. Children are placed on a circle around their parent in id order, radius `120 * 0.55^(depth-1)` (minimum 24), starting at the parent's own angle.
3. 80 fixed force iterations (25 above 300 locations): pairwise repulsion `900/d^2` within 150 units, route springs (rest 130, k 0.04), parent springs (rest 60, k 0.08), step size cooling linearly, each move clamped to 20 units. Coincident points are nudged by index.
4. Positions are clamped to [20, 980] and rounded to 0.1.

## climate

`zones`: `[{zone, count, locations, mean_temperature_c, mean_precipitation_mm}]`, one per zone present (zone null becomes `"unspecified"`); the means are over the locations with data, or null. It uses effective climate, so inherited locations count. `legend` maps zone name to a hex colour from the Paul Tol muted palette (colour-blind safe, 10 colours): `tropical #CC6677, arid #332288, semi-arid #DDCC77, mediterranean #117733, temperate #88CCEE, continental #882255, subarctic #44AA99, polar #999933, alpine #AA4499, custom #DDDDDD`. Zones outside that list are added in sorted order and cycle through the palette. Colour a location with no climate yourself (for example neutral grey). `zones` is `[]` when no location has climate data.

## life

`species_index`: `[{name, kind, species_id, roles, locations}]`; `kind` is `flora` or `fauna`, `species_id` a species entity id/slug or null for a plain name, `roles` the distinct roles, `locations` the location ids where it occurs. Empty when no location lists flora or fauna.

## economy

- `resources`: `[{name, category, rarity, producers, consumers, routes}]`. Merged by slugified name from `world/economy.yaml` resources and production, plus each location's `resources`. `producers`/`consumers` are location ids. `routes` are map route ids that carry it, plus `trade:<trade route id>` entries for the economy trade routes that carry it.
- `trade_routes`: `[{id, name, from, to, from_label, to_label, via, mode, goods, annual_value, controlled_by, status, map_route_ids}]`. `from`/`to` are location ids or null when the endpoint is not a known location (`from_label`/`to_label` keep the written text, for example `"various"`). `via` are location ids. `goods` is `[{resource, direction, volume}]` where `resource` is a slug. `map_route_ids` are the legs `from -> via -> to` as map route ids (some may not exist as declared map routes).
- `currencies`: `[{name, issuer, accepted_in}]`; `issuer` is an entity id or the raw text, `accepted_in` entity ids.
- `shocks`: `[{event, effects}]` from `shocks:` in world/economy.yaml; `event` is an event id (or raw text), `effects` the remaining keys as written (`production_effects`, `trade_effects`, `wealth_transfers`, `price_effects`). `[]` when none.

## warnings

Plain strings, for example `"0 locations have climate data"`, `"3 of 22 locations have flora data"`, `"economy data missing: no world/economy.yaml"`, `"no present_date set in project.yaml or calendar.yaml"`. Show them in a dismissible banner; an empty view should say which warning explains it.
