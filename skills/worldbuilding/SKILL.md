---
name: worldbuilding
description: Create and extend an internally consistent fictional world stored as Markdown files with YAML frontmatter. Use whenever the user is building, expanding, checking or querying a world's history, geography, climate, economy, peoples, languages, factions, magic or events, or mentions a worldbuilding project (a folder containing project.yaml).
---

# Worldbuilding core

The goal is a world that feels real because everything in it is explained by something else. A reader should be able to ask "why is it like that?" of any fact and find a cause in the files. Internal consistency outranks novelty: never add a fact that contradicts the record, and never leave a significant fact without causes and consequences.

## Project layout

A project is any folder containing `project.yaml`. Entities are one file each, `world/<type-dir>/<slug>.md`, YAML frontmatter (structured truth) plus a Markdown body (prose).

Types and directories: `character` (characters), `location` (locations), `faction` (factions), `item` (items), `magic-system` (magic-systems), `arc` (arcs), `event` (events), `species` (species), `race` (races), `language` (languages), `lineage` (lineages), `tradition` (traditions: myths, legends, customs, superstitions and other surviving memory of events).

Templates are in `assets/templates/<type>/`. Field-by-field schemas are in `references/entity-schemas.md`. A complete worked example is in `assets/example-the-lattice/`: copy its patterns.

## Conventions

- Cross-references are kebab-case slugs identical to the target filename without `.md`. A reference to a slug with no file is an error.
- Relationships are bidirectional. If A lists B, B must list A (child/parent, member/faction, route endpoints, allies, and so on).
- Dates use the WorldDate system: era prefix plus year, optionally month and day. The calendar and eras (each with a unique `prefix` and a strictly increasing `sort_order`) live in `world/history/calendar.yaml`, which the validator reads; `project.yaml` only carries a short `calendar:` summary. Never invent a new era without adding it to `calendar.yaml`.
- `project.yaml` holds world flags under `world_flags` (gunpowder, magic, FTL and similar). Content must never contradict a flag.
- Each entity has `descriptions.machine` (structured, factual) and `descriptions.human` (styled prose). The machine description is the source of truth; prose must not add facts that contradict it.

## Routing: which skill owns which change

Load the owning skill before writing in its layer.

| Kind of change | Load |
|---|---|
| New project, or a world from scratch | `world-wizard` |
| Geography, climate, flora, fauna, terrain, resources in the ground, routes, travel | `geography-and-climate` |
| Resources, trade, prices, currency, markets, institutions, production | `economy-and-trade` |
| Species, races, languages, characters, factions, lineages, cultures | `peoples` |
| Events, eras, calendar, timeline | `history-and-events` |
| Myths, legends, folklore, customs, superstitions, taboos, proverbs, how events are remembered or lost | `folklore-and-traditions` |
| Supernatural, magic, psionics, curses, magical creatures | `magic-systems` |
| Checking, impact of a change, "why is it like that" | `world-validate` |
| Chapters, scenes, short stories, campaign and session material | `writing` |
| Editorial review of prose against the world | `world-review` |
| Readability and prose statistics | `prose-check` |
| Exporting a manuscript as Markdown or HTML | `world-compile` |

A change usually touches several layers. The consequence sweep (step 3 below) must load the owning skill for every layer touched, not just the one you started in.

## Magic gate

Before writing any supernatural element in any domain (a species trait, a miracle, a curse, a monster, an item, an event), read `world_flags.magic.present` in `project.yaml`. If it is false, there is no magic: write a mundane explanation or none. If it is unset, ask the user yes or no and record it. If true, the element must fit the magic flags and belong to a system on file (`magic-systems`).

## Working procedure (follow every time)

1. **Read before you write.** Locate the project, read `project.yaml`, then read every existing entity the new material touches: its location chain, its faction, its era, neighbouring events, the relevant world flags. If the world is large, list the directory and read only the related files, but always read the ones you will link to.
2. **Trace causes.** Before adding an entity or event, state in one line why it exists: what earlier fact (geography, climate, resource, event, belief) made it happen. If nothing does, either add the missing cause first or change the idea. See `references/causality.md`.
3. **Trace consequences.** After adding it, state what it changes downstream (economy, settlement, population, politics, culture, language, other events) and record those changes in the affected files, not just in the new one. Load the owning skill from the routing table for each layer touched.
4. **Write both sides.** Create the file, then edit every referenced entity to add the reverse link.
5. **Check dates and flags.** Causes precede effects. Characters must be alive and old enough. Technology and magic must be allowed by the world flags.
6. **Run the checks** (see Validation) before telling the user the work is done, and report any issue honestly.

## Consistency rules that are easy to break

- Physical chain: latitude, elevation and ocean currents determine climate; climate and terrain determine flora, fauna and agriculture; those and mineral resources determine settlement, population and trade; trade and surplus determine wealth, factions and conflict.
- Distances and travel times follow terrain and the transport technology the flags allow.
- Population, army size, food supply and tax base must be mutually plausible.
- A species or culture's language, naming, diet, religion and architecture should reflect its origin location and history.
- Ages, lifespans, generations and dates must add up. Count them.
- When the user asks to change an established fact, list everything that depends on it first, then update all of it or tell the user what breaks.

## Validation

Load the `world-validate` skill and run its checker. If `python3` is unavailable, validate by hand: every reference resolves, every link is reciprocated, every event's causes are earlier than its effects, no content violates a world flag, no character acts outside their lifespan. Report each failure with the file and field.

## Further reading (load only when needed)

- `references/causality.md`: how to model and check causal chains, including the memory layer (traditions are traces of events).
- `references/entity-schemas.md`: fields for every entity type.
- `references/economy.md`: resources, production, trade routes, currency.
- The `world-wizard` skill: creating a new project.
- `references/editors.md` and `assets/editors/`: editorial review personas.
- `references/descriptions.md`: the machine/human description system.
- `references/style-system.md`: prose styles.
