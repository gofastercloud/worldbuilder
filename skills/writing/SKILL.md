---
name: writing
description: Turn a worldbuilding project into prose and play material - chapters, scenes, short stories, novels, outlines, series, and D&D-style campaigns, sessions, encounters, quests, adventure hooks, NPC dialogue and narration. Use when the user asks to write a chapter or scene, write a short story or novel, outline a book, build a campaign or session, design an encounter or quest, narrate a moment, voice an NPC, or write in the style of an author or preset. Assembles dated world context first, keeps prose faithful to the record, and writes new facts back to the entity files.
---

# Writing from the world

The world files are the truth. Prose and play material are a view onto them. Never write a scene until you know what is true at that moment, who knows what, and what the weather is doing. Whatever the prose adds that matters must be written back afterwards.

Load `worldbuilding` first (conventions, magic gate, working procedure). Load `world-validate` for the checker and graph tools, and `world-review` for the editor personas.

## Modes

- **Chapter or scene** (`wb-write`): one chapter or scene of an existing or new book. See `references/chapter-workflow.md`.
- **Short story, novel, series** (`wb-story`): premise from the world, then structure. See `references/story-and-series.md`.
- **Campaign** (`wb-campaign`): sessions, hubs, NPCs, rumours, clocks. See `references/campaign.md`.

Dialogue and voice for any mode: `references/dialogue-and-voice.md`. The context checklist for any mode: `references/context-assembly.md`.

## Deterministic brief generator (`scripts/story_campaign.py`)

Before drafting a short story or a D&D 5e campaign, run `scripts/story_campaign.py` to assemble a spoiler-free, dated world brief directly from the files (zero runtime dependencies):

```bash
# Short story anchored to an event, myth/tradition, era, or present day
python3 scripts/story_campaign.py story <project> --event <slug>
python3 scripts/story_campaign.py story <project> --tradition <slug>
python3 scripts/story_campaign.py story <project> --era <prefix> --start-year <Y> [--end-year <Y2>]

# D&D 5e-compatible campaign anchored to an era, event, tradition, or present day
python3 scripts/story_campaign.py campaign <project> --era <prefix> --year <Y> --level 1-4 --length short --location <slug>
```

The script enforces the **spoiler firewall** (excluding events after the anchor date), filters living characters, extracts `world_flags.magic` rules (including 5e low/no-magic guidance when magic is off), traces causal ancestry (`why`), and builds faction clocks, economy hooks, and a d6/d8 rumour table from real traditions. Use `--json` for structured output or `--out <path>` to save the brief.

## Step 0: locate and anchor

1. Find the project (folder with `project.yaml`). Read `project.yaml`: world flags, style block, tone, themes, calendar summary, present date.
2. Fix the anchor. Every piece of writing has an in-world date (scene date, story span, or campaign start). Ask the user if they have not said. Options: an event slug (the moment of that event), an era and year, or the present day.
3. Fix the scope: which book, chapter, POV character, location, length and rating. Use the chapter template fields (`pov`, `location`, `timeline_start`, `characters_present`, `status`) when a chapter file exists.

## Step 1: assemble context (before any prose)

Do this by reading files, not from memory. Write the result as a short working brief for yourself (and show it to the user for anything longer than a scene). Full checklist in `references/context-assembly.md`. The essentials:

- **Date and time**: scene date in WorldDate, season and time of day, what era it is, what has already happened (events before the anchor) and what has not (events after: never leak them).
- **Who is alive and where**: characters alive and of age at the anchor date, their location on that date, their faction, their relationships.
- **Places**: each present location, its parent chain, terrain, climate profile, and the season-appropriate weather, plus flora, fauna, architecture, resources. Use the data from `geography-and-climate`, not default fantasy weather.
- **Factions in play**: goals, leader, strength, who is allied or hostile, what they want right now.
- **Knowledge**: what each POV character can know. See Knowledge below.
- **Languages and names**: who speaks what, naming conventions of the people involved, honorifics, scripts.
- **Flags**: technology and magic. Apply the magic gate. If magic is absent, supernatural events in prose are beliefs, misread natural events or lies.
- **Recent events and consequences**: the last events before the anchor, their `immediate_consequences`, and the traces they left (prices, scarcity, grief, laws, grudges).
- **Voice fields**: `voice.description`, tags, accent, dialect, `instruct`. These are context for how a character speaks in prose, never audio instructions.

## Knowledge: truth versus story

Characters believe the version of events they inherited, not necessarily the truth.

- For each event the scene touches, decide what the POV character knows: the true record, an official version, a folk version, or nothing. Use traditions (`world/traditions/`), their `held_by`, `fidelity`, `regions`, and each event's `secrecy` (public, rumored, secret, forgotten, mythologized) and `known_by`.
- A character may only state, act on or recall what they could plausibly know by their birth date, location, literacy, class and faction. A peasant does not know the secret council minutes. A scholar may know the truth and be silenced.
- The author's truth is the engine: the gap between the true chain and the remembered chain is where dramatic irony, mystery and reveals come from. Never resolve a gap in prose without deciding what changes in the record (see write-back).

## Step 2: plan, write, check, write back

Chapter workflow, summarised:

1. Plan beats from the arc (`world/arcs/`): setup, inciting incident, rising action, midpoint, crisis, climax, resolution. Each beat must be caused by a fact in the world or by a character's motive.
2. Write scene by scene. Each scene has: date, place, POV, goal, conflict, change. Keep prose consistent with `descriptions.machine` (physical facts, ages, heights, colours, distances). Style may colour how a fact is told, never change it.
3. Continuity pass: re-read against the brief, then run `world-validate` and the `world-review` personas (continuity, worldrules, geography, character, dialogue).
4. Write back (mandatory): every new fact the prose introduced goes into entity files. See Write-back.

## Write-back (consequence sweep)

Prose is a source of new facts: a minor character's name, a tavern, a fine, a death, a scar, a rumour, a spoken oath. For each:

- **Decide**: canon (record it), invention for this scene only (cut it), or contradiction (fix the prose).
- **Record**: create or edit the entity file (character, location, event, tradition, item). New things get a cause (`caused_by`, origin, founding reason). Events that happen in the story become events with `caused_by`, `leads_to` or `open_ended`, consequences filled, and `traces`.
- **Both sides**: every link in both directions. Participants, locations, factions, parents and children, routes.
- **Update chapter metadata**: `characters_present`, `location`, `timeline_start`, `status`, `word_count`, `summary`; arc `chapters`, `foreshadowing`, `payoffs`, `unresolved`.
- **Rerun** `validate.py`; report errors honestly.

Run `graph.py impact <slug>` on any event the story creates or changes, then apply the consequence sweep from `worldbuilding/references/causality.md`.

## Style cascade

Resolve the prose style in this order, highest first: chapter `style:` block, book `style:` block (`story/books/<book>.yaml`), project `style:` in `project.yaml`, system defaults in `worldbuilding/references/style-system.md`. Merge field by field, not wholesale. Controls: preset (14), POV, tense, formality, vocabulary complexity, anachronism tolerance, profanity, tempo, scene length, content rating, sensory emphasis, metaphor density, internal monologue.

Applying a style without breaking facts:
- Treat the machine description as the fixed skeleton and the style as the way of telling it. Change diction, rhythm, imagery and what the narrator notices; do not change numbers, names, colours, dates, causes or who knows what.
- A style that implies unreliable narration (`noir`, `horror`, `unreliable` POV) may distort perception, but the distortion must be the narrator's, and the author's truth stays in the files.
- Anachronism tolerance `strict`: no idioms, units or metaphors that the world lacks (no clocks, trains or gunpowder metaphors where the flags forbid them). Use in-world units and in-world oaths.
- "In the style of" a named author: borrow technique (sentence length, point of view distance, imagery habits), never reproduce their text or invent facts from their books. Record the choice as a chapter or book `style:` override if it should persist.
- Content rating bounds what is on the page; keep it as set at project level.

## Stories and series

Premise from the world, not from nowhere. Sources, in order of strength: an `open_ended` event whose consequences are unfolding; a contradiction between traditions or between the official and folk version; a mystery from `graph.py unrooted` (events with no cause, traditions with no origin); a faction goal blocked by a real scarcity; a consequence nobody has dealt with. Details and series planning in `references/story-and-series.md`.

## Campaigns

Sessions with hubs, routes and travel times from the data, NPCs built from characters and factions with motives, rumour tables from traditions (true, distorted, false), clocks from real faction goals, economy hooks, and consequence tracking that writes player-caused change back as events. Details in `references/campaign.md`.

## Anti-patterns

- A fact invented in prose and never recorded.
- A character who knows something they cannot (before the event, far away, with no means to learn it).
- Anachronism: technology, units, idiom or magic the flags and era forbid.
- Weather, light or flora that ignores the climate profile and season.
- Plot armour: a character survives, escapes or wins in a way the world's causes do not allow; a faction acts without means or motive.
- A cause that comes after its effect, or an event with no consequences.
- Everyone speaking the narrator's dialect; every culture eating, swearing and worshipping alike.
- Resolving a mystery by narrator fiat without updating traditions and events.
- Style used as an excuse to change facts.
- Leaking the secret truth through a character who could not know it.

## Report

When finished, tell the user: what was written and where, the context brief used, new facts recorded and files changed, validator result, and anything left open (gaps deliberately kept, `open_ended` events, unresolved arcs).
