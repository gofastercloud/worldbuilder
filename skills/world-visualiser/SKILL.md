---
name: world-visualiser
description: Build an interactive single-file HTML viewer of a worldbuilding project with a 3D causal graph, timeline, map, trade and life views. Use when the user asks to visualise, view, explore or map their world, see the timeline or cause and effect chains, or look at climate zones, species ranges, resources and trade routes.
---

# World visualiser

Turns the project's files into one self-contained page, `output/world-viewer.html`, that opens in a browser. It reads the same graph as the validator, so what you see is what the files say. Nothing is invented: data that is not in the files shows as empty.

## Build it

Run [scripts/build_viewer.py](./scripts/build_viewer.py) (resolved relative to this skill's directory):

```bash
python3 <this-skill-dir>/scripts/build_viewer.py <project-dir>
```

Options: `--out FILE` to write elsewhere, `--json-only` to write `viz.json` instead of the page, `--template PATH` to use another shell (its `css/` and `js/` folders sit beside it). The sources are in `assets/viewer/`; the build inlines them into one file. The script exits with an error if the folder has no `project.yaml`. It prints any data warnings (for example `0 locations have climate data`).

Then tell the user the path of `world-viewer.html` and ask them to open it in a browser. The page loads three.js from a CDN, so it needs an internet connection the first time it is opened.

## Views

Tabs run in this order. Every view shares one selection: click anything and the right-hand panel shows its summary, date and linked items (caused by, leads to, traces, participants, locations, related), each clickable.

- Causal graph (3D): events as nodes, causal edges as arrows, memory edges (event to tradition) dashed. Selecting a node colours its upstream causes blue and downstream effects orange and dims the rest. Drag rotates, shift-drag or right-drag pans, wheel zooms. Toggles: causal chain or all entities, causal edges only or all kinds, traditions on or off, pin time axis (x follows date), reset layout. The layout is seeded, so it is the same on every build.
- Timeline: era bands, events on lanes by type or by location, marker size by significance, causal arcs from cause to effect, traditions (diamonds) at first attestation with dashed links to their origin events, and the present date line when set. Ctrl+wheel zooms. Keys: left and right move by date, up goes to a cause, down to an effect. A screen reader table lists the events in order.
- Map, Trade and Life: locations and routes, trade routes and resources, climate zones with flora and fauna.

## Controls

Search box (press /) filters by name; type chips and the era menu filter every view. The Entity list button opens a keyboard-friendly list of everything that passes the filters. The footer shows the warning count; click it for the list. Light and dark themes follow the system, and motion is not used when the system asks for reduced motion.

If three.js cannot load (no internet) a banner says so; the entity list, detail panel and timeline still work.

## Missing data

Climate, flora, fauna, terrain, resources and economy data are optional in the schema, so a young world shows those views mostly empty. The warnings list says what is thin. To fill them in:

- Climate, terrain, elevation, flora, fauna: use the `geography-and-climate` skill.
- Resources, production, trade routes, currencies, shocks: use the `economy-and-trade` skill.
- Dates and causes for the timeline: use `history-and-events`; traditions: `folklore-and-traditions`.

Rebuild after any change; the page is a snapshot of the files at build time.

## Data format

The payload shape is documented in `references/data-format.md`. The scripts are standard library only (PyYAML is vendored with the validator).
