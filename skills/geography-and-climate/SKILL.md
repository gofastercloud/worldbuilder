---
name: geography-and-climate
description: Design and edit the physical world of a worldbuilding project so geography, climate, weather, biomes, flora and fauna are causally consistent. Use for geography, maps, continents, regions, mountains, rivers, coasts, seas, terrain, climate, seasons, weather, rainfall, deserts, biomes, flora, fauna, habitats, planets, moons, star systems, habitable zones, routes, roads, travel time, distances, chokepoints, borders, resources and growing seasons, or when adding or changing any location entity.
---

# Geography and climate

Physical geography is the root cause layer of the whole world (see the `worldbuilding` skill and its `references/causality.md`). Climate, terrain and resources decide where people live, what they eat, what they trade and where they fight. Every place must be explainable by a chain from astronomy upward, and every change must be swept downstream.

Load this skill with `worldbuilding`. Detail lives in `references/`:

- `references/generation-order.md`: step by step physical causal order with rules of thumb and numbers.
- `references/schema-extension.md`: the climate, flora, fauna and resource fields on locations.
- `references/transport-and-travel.md`: hierarchy, route semantics, travel-time arithmetic, chokepoints.

## Step 0: magic gate (never skip)

Read `world_flags.magic.present` in `project.yaml`. If it is false (or `prevalence: none`), write no supernatural content: no magic cause for terraforming, climate, rivers or terrain, no ley-line, portal or teleportation routes, no mana fuel or magical resources, no magical flora or fauna. Offer technology, psychology or natural explanations instead (engineering, volcanism, currents, orbital mechanics). If it is unset, ask the user; the `magic-systems` skill owns the gate.

## Non-negotiable rules

1. **Read before you write.** Read `project.yaml` (world flags: `geography`, `physics`, `technology`, `magic`), the parent chain, siblings and neighbours of any location you touch.
2. **Cause before effect.** Fill the layers in order (below). Never choose a biome first and invent reasons later; if the user dictates a biome, derive or add the cause (a mountain range, a current) and record it in `climate_profile.drivers`.
3. **Inherit, then override.** A child location starts from its parent's climate and changes only what its own altitude, coast, latitude or terrain justify, with the reason recorded.
4. **Write both sides** of every parent/child link and every route.
5. **Sweep consequences** after every change (section below).
6. **Validate** with the `world-validate` skill before reporting done.

## Causal generation order

Work top-down. Skip layers the world does not need (a flat-world or pocket realm still needs its own stated rules), but never skip a layer silently: state the assumption.

1. **Astronomy.** Star type and luminosity, orbit distance, year length, axial tilt, rotation period, moons, planet size and gravity. For fantasy worlds with no stated astronomy assume Earth-like and record it in the `physics.astronomy` and `physics.seasons` flags.
2. **Latitude bands and seasons.** Tilt sets seasonality and where the tropics end (tropics = tilt degrees either side of the equator). No tilt means no seasons; high tilt means extreme polar seasons. Day length, not just temperature, changes with latitude.
3. **Land, sea and elevation.** Place continents, seas, mountain ranges (plate boundaries, linear, with foothills and a gradual rise on one side), plateaus and basins. Mountains are not isolated spikes; rivers need somewhere to fall from.
4. **Air and ocean circulation.** Rough Earth-like pattern: trade winds blow from the east in the tropics, westerlies in the mid latitudes, polar easterlies. The sea-level pressure belts give wet equator, dry subtropics (~15 to 35 degrees), wet mid latitudes, dry poles. Warm currents flow poleward on the west sides of oceans, cold currents equatorward on the east sides, so cold-current coasts are dry and foggy, warm-current coasts mild and wet.
5. **Climate zones and seasons.** Combine latitude, altitude, distance from sea and wind. Detailed rules in `references/generation-order.md`: lapse rate, rain shadow, continentality, monsoon.
6. **Hydrology.** Rivers start in the wet highlands, flow downhill and to the sea, merge but do not split (except in deltas and braided plains), and lakes either have an outflow or are salty and in dry basins.
7. **Biomes.** Read from temperature and precipitation (Whittaker table in the reference). Transitions are gradual, with ecotones, never a hard line without a barrier.
8. **Flora and fauna.** Species follow biomes. Keep trophic pyramids sane: predators are far fewer than prey (roughly 1:10 by biomass per level). Create species entities (see the `peoples` skill) for anything that matters to the story or economy; list the rest by name with a role.
9. **Resources.** Minerals follow geology (ores near old mountain roots and volcanic arcs, coal and oil in sedimentary basins, salt in dry basins); agricultural potential follows climate, soil and growing season. Record resources as `{name, category, rarity, notes}` (the economy enums) and hand over to `economy-and-trade`.
10. **Habitability and carrying capacity.** How many people can live there at the world's tech level; see the table. Hand over to `peoples`.

## Sci-fi and planets

- **Habitable zone.** Liquid water needs stellar flux of about 0.75 to 1.8 times Earth's. Flux = L / d^2 (L in solar luminosities, d in AU), so the zone is d from about 0.75 x sqrt(L) to 1.15 x sqrt(L) (conservative: 0.95 to 1.4 for the best-understood case). Red dwarfs: zone is close in, so tidal locking is likely (permanent day and night side, habitable ring at the terminator, strong winds); flares threaten atmospheres. Giant stars: short lived, so no deep biosphere history.
- Year length from Kepler: years = sqrt(AU cubed / stellar mass in solar masses). Check that stated year lengths and seasons agree with the stated orbit.
- Surface gravity scales with density and radius; above about 1.5 g long-term human habitation is hard without adaptation, below about 0.4 g it is poorly understood.
- Terraformed, engineered or artificial worlds (stations, rings, hollow worlds) need an explicit machine cause (or a magic cause, only if the gate allows) for every departure from the physics above, recorded in a world flag or location note.
- Single-biome planets (ice world, desert world) need a stated cause (tidal lock, runaway glaciation, no ocean) and still show altitude and local variation.

## Location hierarchy and transport

Hierarchy: `universe > galaxy > star-system > planet/moon > continent/ocean/sea > country/kingdom/empire/region/province > city/town/village/district > building/room`, with natural features (`mountain-range`, `river`, `lake`, `desert`, `forest`, `island`, `valley`) hanging under the region that contains them. Every non-root location has exactly one `parent`; the parent's file lists the child in its prose or by reference, and the type must sit at a plausible level below its parent (no `room` directly under `planet`).

Routes: each side of a route lists the other (`bidirectional: true` still needs both entries unless the route is genuinely one-way, in which case say why in `notes`). Route shape (the one used everywhere, including by `economy-and-trade`): `to` plus `methods[]`, each with `mode`, `distance` and `travel_time` consistent with each other and with terrain, season and the transport technology the world flags allow. Distances and speeds, chokepoints, seasonal closures: `references/transport-and-travel.md`.

Coordinates (optional): a location may pin its map position on the 1000x1000 atlas canvas using `coordinates: [x, y]` or `coordinates: {x: N, y: M}` (two finite numbers in `[0, 1000]`). Leave `coordinates` unset (or `{}`) for automatic placement; pinned locations stay fixed while unpinned locations relax around them.

## Adding or editing a location (procedure)

1. Read `project.yaml` flags and the whole parent chain (up to the planet or world root), noting each level's `climate_profile`, terrain, elevation and hydrology.
2. List siblings and anything that touches the new place; read the neighbours it will border or route to.
3. State in one line why this place exists here (the cause), and what it changes (the consequence).
4. Start from the parent's climate; adjust for altitude (about minus 6.5 degrees C per 1000 m), coast or interior, windward or leeward, latitude offset. Record each adjustment in `drivers`.
5. Compare with every neighbour: contrasting climates need a barrier (mountain, current, sea) in between or a gradual transition; check river directions and shared water.
6. Fill flora, fauna and resources that follow from the biome. Reuse existing species entities by slug; create missing ones only if significant.
7. Write routes on both ends, with times computed from distance and mode; mark seasonal closures that follow from the climate (passes closed in winter, rivers frozen, monsoon floods).
8. Run the consequence sweep and the checklist.

When *editing* an existing place, list what depends on the current value (inhabitants, crops, routes, events that mention its weather) before changing it.

## Consequence sweep

After any geographic or climatic change, ask each layer and edit the files now.

| Change | Check and update |
|---|---|
| Colder, drier, shorter growing season, drought, flood | Food yield and population (carrying capacity), crops grown, famine or migration events, prices; load `economy-and-trade`, `peoples`, `history-and-events` |
| Mountain, pass, river or coast altered or blocked | Routes and travel times on both ends, chokepoints, borders and fortifications, trade routes and tolls; `economy-and-trade`, `history-and-events` |
| New or exhausted resource (ore, timber, fertile soil, water) | Production, trade flows, settlement, faction wealth and conflicts; `economy-and-trade` |
| New species or habitat shift (fauna, crop, pest, predator) | Diet, domesticates, hunting, disease, species entities, cultural symbols; `peoples` |
| Sea level, rivers changing course, volcanic or seismic events | Port towns, cities, farmland, who migrates, which events caused it and what they cause; `history-and-events` |
| Planet-scale change (tilt, orbit, star) | Every climate_profile beneath it, calendar and seasons in `project.yaml`, all `climate` strings; this is a retcon: list everything and confirm with the user |

Sibling skills to load by name: `economy-and-trade` (resources, food, trade routes), `peoples` (species, races, settlement, diet, culture), `history-and-events` (famines, migrations, disasters, wars over land). Record the cause on the event (`caused_by` or the event text naming the location) as `references/causality.md` requires.

## Worked example (the-lattice, Keth Prime)

`assets/example-the-lattice/world/locations/keth-prime.md` has `type: planet`, `climate: "warm, humid, volcanic"`, `population: ~80 billion`, `routes: []`, and resources like `industrial-labor`. Applying this skill finds gaps in a good world:

- **Cause:** a large volcanic planet, warm and humid, needs a driver: close orbit or dense greenhouse atmosphere, plus volcanic CO2 and water vapour. Add `climate_profile.drivers: ["heavy volcanism: CO2 and water vapour greenhouse", "close, warm star"]`, `zone: tropical`, `rain_pattern: even`, narrow `temperature_c` ranges (little tilt, so no real seasons: `seasons: []`).
- **Carrying capacity:** 80 billion people on one planet is roughly 160 people per km² over a planet the size of Earth including oceans, which only works with industrial food (the example's economy already has `Nutrient Cultures` as food). Add a `resources` entry or note stating the food source and that Keth Prime imports or synthesises food, instead of leaving the figure unexplained.
- **Hazards:** `dangers: [volcanic-activity]` becomes `climate_profile.hazards` (ashfall, acid rain) tied to the caldera cities, and ash lowers solar output, which is another reason for geothermal energy.
- **Routes:** the system has routes to `sol-system` and `crossroads-system`, but the planet's `routes: []`; add an `orbital-shuttle` route to `keth-prime-system` on both sides, as `vaelor.md` does, with hours not days (orbital distances).
- **Sweep:** if the planet were cooled, geothermal industry, population and the factory culture would all change; load `economy-and-trade` and `peoples`.

## Anti-patterns

- Single-biome planets or continents with no cause and no altitude variation.
- Rivers that flow uphill, split into two unrelated seas, or end in a desert with no lake or sink.
- Deserts next to oceans or rainforests without a rain shadow, cold current or mountain wall; rainforest at 60 degrees latitude without a warm current.
- Climate ignoring altitude: snow on the equator at sea level, or palm trees at 4000 m.
- Impossible travel times: 500 km in a day on foot, ships crossing a continent, trains without railways or steam in a no-steam world.
- Seasons that contradict axial tilt, year length or the calendar in `project.yaml`.
- Cities with no water, food or trade reason to exist there; populations above the carrying capacity without imports.
- Species with no habitat, apex predators with no prey, crops outside their growing season.
- One-sided routes and children that do not know their parent.

## Checklist

- [ ] Read flags, parent chain, siblings and neighbours first.
- [ ] Cause chain stated: astronomy and latitude, altitude, wind and sea, then climate, water, biome, life, resources, habitability.
- [ ] `climate_profile` consistent with parent, altitude, and neighbours; drivers recorded.
- [ ] Rivers flow downhill, merge, end at a sea or a justified sink.
- [ ] Flora, fauna and resources follow from the biome; slugs resolve to existing species; resources use the shared `{name, category, rarity, notes}` shape.
- [ ] Population is within carrying capacity or the import or tech reason is recorded.
- [ ] Routes written on both ends; times match distance, terrain, mode and flags.
- [ ] Consequence sweep done across `economy-and-trade`, `peoples`, `history-and-events`.
- [ ] Run the `world-validate` skill and report every failure honestly.
