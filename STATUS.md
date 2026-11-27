# Status (Spec #30 complete)

## Goal
Spec #30: Expansive Cartography & Multi-World Support — **completed and closed**.

## Completed
- **#31** (PR #36): Full-canvas map layout spread (`[90, 910]`) & explicit YAML `coordinates: [x, y]` support with validator bounds checks.
- **#32** (PR #37): Multi-world/realm scoping (`map.scopes`, `map.cross_world_routes`), per-world `map_image` backdrops, and per-world `world_flags` overrides.
- **#33** (PR #38): Domain-warped tectonic ridges, procedural rivers (`hydrology.flows_to` + downhill drainage), rain-shadow biomes, and Parchment/Topographic cartographic ornaments.
- **#34** (PR #39): Multi-world `World / Realm` switcher & Galaxy/Planar Overview canvas in `map.js` with cross-world portal/warp routes and drill-down.

## In flight
- None.

## Waiting on you
- Nothing — backlog is drained (`0` open `ready-for-agent` tickets).

## Next
- Run `/spec <idea>` for the next feature, or pin `coordinates` & `hydrology.flows_to` on `worlds/elderglen` and rebuild its viewer to preview the upgraded atlas.
