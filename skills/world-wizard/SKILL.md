---
name: world-wizard
description: Create a new worldbuilding project from scratch, guided or in YOLO mode. Use when the user wants to start a new world, setting, novel universe, campaign world or game world, or asks for a world wizard. Creates the project folder and project.yaml, asks the key world flags (magic yes or no first, then technology and others), then generates geography, peoples, economy, magic if allowed, history, folklore, factions and characters one causal stage at a time, validating after each stage and ending with a world bible summary.
---

# World wizard

Build a new world in dependency order so that every fact has a cause already on disk. This skill orchestrates; the domain skills own the detail. Follow the `worldbuilding` skill's procedure and consistency rules throughout.

Arguments the user passed (a path, a seed phrase, "yolo", a size, a genre) are the starting answers: do not ask again for anything they already gave.

## Modes

- **Guided** (default): ask the flag questions below, then stop after each stage with a two or three line summary and let the user steer before the next stage.
- **YOLO**: the user said "yolo", "just do it" or similar. Ask only for what is missing from this list: project location, genre, size, and the magic yes/no. Make all other choices yourself, record them in `project.yaml` (under `notes` or the flag's `notes`), then run every stage without stopping. Still validate after each stage.

Never silently default magic. Always ask the magic question even in YOLO unless the user already answered it.

## Step 1: set up the project

1. Choose the folder. Use the path given, otherwise ask where it should live. If the folder already holds a `project.yaml`, stop and ask: this is an existing project, use the `worldbuilding` skill instead.
2. Create `project.yaml` from `${CLAUDE_SKILL_DIR}/../worldbuilding/assets/templates/project_template.yaml`. Fill `title`, `genre`, `type`, `tone`, `style.prose.preset` and the `world_flags` as you learn them. Remove the unused template comments if they are noise.
3. Create the directories: `world/characters`, `world/locations`, `world/factions`, `world/items`, `world/magic-systems` (only if magic is allowed), `world/arcs`, `world/events`, `world/species`, `world/races`, `world/languages`, `world/lineages`, `world/traditions`, `world/history`. Put an empty `.gitkeep` in directories that stay empty if the folder is under git.
4. Create `world/history/calendar.yaml` (the validator reads this file, not `project.yaml`). Defer the eras until stage 6, but write the skeleton now: name, epoch, and the era or eras you already know. Each era needs a short unique `prefix` and a strictly increasing `sort_order`. Copy the format from the `history-and-events` skill's `references/calendar-and-eras.md`. Mirror `name`, `epoch` and `format` in the `calendar:` block of `project.yaml`.
5. Entity files come from the templates in `${CLAUDE_SKILL_DIR}/../worldbuilding/assets/templates/<type>/_template.md` (or `.yaml`) with the schema in the same folder.

## Step 2: ask the flags

Ask in this order, a few questions per message, offering options with a recommended one. Full question wording, options and the YAML to record are in `references/questions.md`.

1. **Magic: yes or no.** FIRST. Record `world_flags.magic.present`.
   - If **no**: set `present: false` and `prevalence: none`. Never create magic systems, spells, magical creatures or working curses at any stage. Apparent magic must have a mundane explanation on file.
   - If **yes**: ask prevalence, hardness, source, cost, heritability and whether it is public knowledge.
2. **Technology**: level, gunpowder, printing, electricity, steam, spaceflight, FTL, AI, medicine, transport. Take defaults from `preset_defaults` for the genre in `worldbuilding/assets/templates/world_flags.yaml`, show them, and ask what to change.
3. **Genre, project type, size** (S, M, L, XL; see `references/sizes.md`), and the user's seed idea or premise in a sentence or two.
4. **Tone and prose style**: pick from the prose presets in `worldbuilding/assets/templates/styles.yaml` (see `worldbuilding/references/style-system.md`). Genre defaults are in `world_flags.yaml` `preset_defaults`.
5. Optional in guided mode, chosen by you in YOLO: world shape and size, species diversity, governance, conflict level, number of central characters.

Write the answers to `project.yaml` before generating anything. Mark flags the user stated explicitly with `locked: true` in the flag's notes if the file uses that form, otherwise record in `notes`.

## Step 3: generate in causal order

One stage at a time. Each stage: load the named skill, generate only that layer, write both sides of every link, then run the checker (see Validate) and fix errors before the next stage. Detail for each stage is in `references/stages.md`.

| Stage | What | Load skill |
|---|---|---|
| 1 | Flags and premise: finish `project.yaml`, write `world/overview.md` and `world/rules.md` (the premise, the one or two big "what if" ideas, what the flags forbid) | `worldbuilding` |
| 2 | Geography and climate: world shape, continents, regions, climate, terrain, flora and fauna, resources in the ground, routes | `geography-and-climate` |
| 3 | Peoples: species and origins, races, languages, cultures, naming, lifespans | `peoples` |
| 4 | Economy: resources, production, trade routes, currency, institutions | `economy-and-trade` |
| 5 | Magic systems, only if `magic.present` is true | `magic-systems` |
| 6 | History by eras: calendar, eras, events era by era | `history-and-events` |
| 7 | Folklore: for each significant event at least consider whether it leaves a tradition. M world: 5 to 10 traditions, S: 2 to 4, L: 10 to 20, XL: 20 to 40, each derived from a real event | `folklore-and-traditions` |
| 8 | Factions, lineages, characters, items, arcs and story hooks | `peoples` |
| 9 | Final validation and the world bible | `world-validate` |

Rules for every stage:
- **Magic gate.** Before writing any supernatural element in any stage (a species trait, a religion's miracle, a curse, a monster, an item), read `world_flags.magic.present`. If it is false, there is none. If it is true, it must fit the flags and be an instance of a magic system on file.
- **Cause first.** Each new entity states what earlier fact on disk explains it. If nothing does, add the cause first or drop the entity.
- **Scale to size.** Use `references/sizes.md` for entity counts. Event and era counts come from the `history-and-events` skill's pacing table: use its numbers and do not restate them.
- **Retrofit upstream.** Later stages often reveal a gap in an earlier one (a trade good no region produces, a people with no origin). Fix it in the earlier layer, then continue.
- Sibling-skill detail wins over this file if they disagree.

## Validate

After each stage:

```
python3 "${CLAUDE_SKILL_DIR}/../world-validate/scripts/validate.py" <project-dir>
```

Load the `world-validate` skill for options and for what each finding means. Fix every error before moving on. Early stages will show warnings about layers not yet written (no events, no factions); note them and do not chase them yet. If `python3` is unavailable, use the by-hand checks in `worldbuilding` and say the validation was manual.

## Stage 9: final run and world bible

1. Run the checker and fix all errors; work through the warnings, fixing or explaining each.
2. Run `graph.py unrooted` and `stats` (see `world-validate`) and fix events or entities with no explanation.
3. Write `world/bible.md` and show the user a short version in chat. Structure in `references/stages.md`: a one-paragraph premise, the flags in plain words, the world in ten lines, the **causal spine** (the 5 to 10 key chains from physical fact to present-day tension, each written as "A, so B, so C"), the main factions and characters, open hooks for stories, and the validation result with anything unresolved.
4. Tell the user what is in the folder and how to extend it (any later change goes through the `worldbuilding` skill and its routing table).

## Failure handling

- If the user changes a flag after generation has started, stop, run an impact sweep of what exists, list what breaks, and get a decision before editing. Turning magic off after systems exist, or on after a mundane history is written, is a major retrofit.
- After 3 failed attempts to clear the same validator error, stop and explain it to the user.
- Do not regenerate over files the user has edited by hand; extend them.
