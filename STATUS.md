# Status (ready for implementation)

## Goal
Spec #30: Expansive Cartography & Multi-World Support — full-canvas map layout with optional YAML `coordinates`, tectonic ridges/rivers/rain-shadow biomes/ornaments, and single-project multi-world scoping (`world`/`planet`/`realm`/`plane`/`system`) with Galaxy/Planar Overview and per-world `world_flags` overrides.

## In flight
- None yet.

## Waiting on you
- Nothing — all 4 tickets are approved and labelled `ready-for-agent`.

## Decisions
- Single-project multi-world via top-level location hierarchy (`world`, `planet`, `realm`, `plane`, `system`), backwards-compatible with `example-the-lattice`.
- Per-world `map_image` backdrop and optional per-world `world_flags` overrides (magic/tech per planet/realm).
- All 4 cartography upgrades in scope: full-canvas spread + YAML `coordinates`, tectonic ridges + rivers, rain-shadow biomes, and Parchment/Topographic ornaments.

## Next
- Run `/next` to dispatch ready tickets from Spec #30:
  - #31 — Full-canvas map layout spread & explicit YAML `coordinates` (M, unblocked)
  - #32 — Multi-world/realm scoping, per-world backdrops & `world_flags` overrides (M, unblocked)
  - #33 — Tectonic ridges, rivers, rain-shadow biomes & cartographic ornaments (M, blocked by #31)
  - #34 — Multi-world switcher & Galaxy/Planar Overview canvas in Map view (M, blocked by #31, #32)
