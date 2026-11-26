# Hierarchy, routes and travel time

## Hierarchy semantics (from the schema and the old CLI)

- `parent` points one level up the spatial tree; the tree is acyclic and ends in a single root (universe, galaxy, world or realm). A location's ancestors are found by following `parent`.
- Containment is spatial: a city in a province in a kingdom on a continent on a planet in a star system. Natural features (river, mountain-range, forest) sit under the region they mainly lie in; if they cross several, parent them to the smallest region containing all of them and list the others in `routes` or prose.
- Descendants inherit climate, `regional_defaults` and, unless overridden, faction control; override explicitly.
- When you add a child, ensure the parent's prose mentions it and the types make sense (planet > continent > region > city).

## Distance and travel time

Distance first, then speed by terrain and mode, then the time; never the other way round.

Rough daily speeds (km per day, good conditions):

| Mode | Speed per day | Notes |
|---|---|---|
| Walking, road | 25 to 35 | A year's march with an army: 15 to 20. Rough ground: 10 to 15. |
| Walking, mountain trail | 8 to 15 | Passes may close in winter |
| Pack animal / caravan | 20 to 30 | Camels in desert 30 to 40 with water stops every 2 to 4 days |
| Riding, single horse | 40 to 60 | With remounts and relays 150 to 200 for messengers |
| Cart / wagon | 20 to 30 | Needs roads; bulk cargo is very costly per km |
| Coach with relays | 60 to 120 | Roads, inns, post system |
| River barge downstream | 40 to 80 | Upstream 10 to 25 (towed, poled) |
| Sailing ship | 100 to 200 (4 to 8 knots) | Wind-dependent; 300 with a strong fair wind; days to weeks of calm |
| Steamship | 400 to 700 | Requires `technology.steam_power` |
| Railway | 500 to 1500 | Requires rail and steam or electric power |
| Car / truck | 600 to 1000 | Requires `internal_combustion` and roads |
| Aircraft | 5000 to 15,000 | Requires flight tech or flying mounts |
| Flying mount | by definition per species | Limited by range, rest and load |

Multipliers: swamp x0.5, dense forest x0.5, hills x0.7, mountain x0.4, desert x0.6 without wells, snow x0.5, road x1.3, navigable river or sea as above. One degree of latitude is about 111 km.

Travel time = distance / (speed x terrain multiplier) plus rest, river crossings, seasonal waits. State both the distance and the time in the route, and check that `travel_time` is within about 25 percent of the calculation.

## World flags decide allowed modes

Read `technology` and `magic` flags before listing any mode: steamship needs steam power, railway needs steam or electric power and metallurgy, aircraft needs flight, `teleportation`, `portal`, `ley-line` need `magic.present` and a stated cost, `starship` and `jump-gate` need `spaceflight` or `ftl`. Mark mode-specific infrastructure with a transport system file (`assets/templates/transport/_template.yaml`, `requires_flags`).

Space travel: sub-light speeds make distances in AU take hours to days (about 8 minutes of light travel per AU); interstellar journeys need FTL or generation ships, and times must agree with the `ftl` and `communication` flags. The lattice example uses `lattice-drive` (4 to 5 days between systems) and `orbital-shuttle` (about 2 hours within a system); keep such figures consistent across all routes using the same mode.

## Route reciprocity and structure

- If A has a route `to: B`, B must have a route `to: A`, unless `bidirectional: false` with a stated reason (rapids, one-way gate).
- Both sides carry the same mode, distance and roughly equal time (upstream and downstream may differ; say so).
- A route's seasonal flag must match the climate (frozen river, flooded ford, closed pass, monsoon seas).
- Hubs (`transport_hub`) are ports, junctions, passes or gates; a `hub_type` must fit the terrain (port needs coast or navigable water).
- Connectivity: every settlement should be reachable from the rest of its region, or explicitly isolated with a reason.

## Chokepoints

A chokepoint is a location where many routes pass through one narrow place: mountain pass, strait, ford, bridge, canal, desert well, gate, jump point, isthmus. They carry strategic and economic weight:

- Mark them as locations with routes on both sides and a `transport_hub` or note.
- Their control gives tolls, taxes, wars and fortresses (hand over to `economy-and-trade` and `history-and-events`).
- Closing one (snow, siege, war, earthquake) should lengthen routes or cut them: update the affected routes and prices.
- If you add a second route that bypasses a chokepoint, say what it costs (longer, more dangerous, seasonal) or the chokepoint stops making sense.
