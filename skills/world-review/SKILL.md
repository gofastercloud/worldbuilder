---
name: world-review
description: Review a chapter, scene or set of entities against the established world using editor personas (continuity, worldrules, geography, character, sensitivity, dialogue, pacing, plot, prose). Use when the user asks to review my chapter, wants editor feedback, a continuity check, a pacing or dialogue critique, a prose critique, a sensitivity read, a world rules check, a manuscript review, or says edit this. Assembles the text and the world state at its in-world date, runs the chosen personas separately, runs the world checker and graph tools, and returns evidence-based findings with severities and a prioritised fix list. Advisory only, never rewrites prose without approval.
---

# World review

A review compares text against the world record and against craft standards. Findings are evidence, not verdicts: the author decides. Never rewrite prose, entities or the world during a review unless the user says so.

## Inputs

Ask only for what you cannot infer: the project (a folder with `project.yaml`), the target (chapter number or path, scene, or an entity set) and the personas wanted. If none are named, choose by the table in `references/persona-guide.md`. A full pass runs all nine.

## Step 1: assemble context (before any persona runs)

Read, do not guess. Record what you loaded so the user can see the basis of the review.

1. `project.yaml`: world flags, magic gate (`world_flags.magic.present`), content rating, cultural inspirations, prose and visual style.
2. The target text in full, with line numbers noted for quoting.
3. Every entity the text names or implies: characters present, POV character, locations, factions, items, magic systems, species and races, languages. Match names, titles and nicknames to slugs by searching `world/`.
4. The temporal context at the text's in-world date. Establish the date from chapter frontmatter or the text; if it is unknown, ask or state an assumption. Then work out:
   - who is alive, their ages, and where each named character should be (use `world/events/` and `world/history/calendar.yaml`)
   - who holds which office or faction role at that date
   - what exists then: settlements, routes, institutions, items, technology
   - events that have already happened and so may be known, remembered or distorted (traditions, see `folklore-and-traditions`)
   - season and weather expected from the calendar and climate
5. Preceding chapters or scenes: a summary of facts they established (physical details, injuries, possessions, promises, knowledge each character has).
6. The persona file for each persona you will run (Step 2). Its `context_requirements` list names extra files to load.

If the target is an entity set rather than prose (for example "review the Harbour Guild"), the text is the entities' frontmatter and body, and the temporal context is the date range they cover.

For long manuscripts, review a chapter at a time and carry a running fact sheet forward. Hand bulk reading to a subagent with a tight brief, but read its fact sheet back against the source before relying on it.

## Step 2: run the personas

Default order for a multi-persona pass (order matters, earlier results change what later ones should flag):

1. worldrules
2. geography
3. continuity
4. character
5. sensitivity

Then, on demand or for a full pass: plot, dialogue, pacing, prose.

For each persona, read its file from `../worldbuilding/assets/editors/<name>.yaml` (relative to this skill's directory) and adopt its `role`, `personality`, `checks` and `output_format`. Use the check ids and severities defined there. Run them one at a time. Keep each persona's findings separate; do not merge them mid-pass, and do not let one persona's conclusions leak into another's. If a later persona notices a problem outside its brief, hand it to the right persona's list rather than reporting it twice.

Persona overview and cross-links to world skills: `references/persona-guide.md`.

## Step 3: mandatory world checks

The continuity and worldrules personas must never rely on reading alone.

1. Load `world-validate` and use its scripts: run `validate.py` on the project and read every finding that touches an entity in scope. Report validator errors on in-scope entities as findings, quoting the validator line.
2. Use the graph tools for the claims the text makes: `graph.py why <event>` to confirm an event the text relies on is really explained, `graph.py impact <slug>` for anything the text changes or assumes, `graph.py path <a> <b>` and `neighbors <slug>` for travel, kinship and allegiance claims.
3. If `python3` or the scripts are unavailable, say so and do the checks by hand, labelling findings "manual check".

A contradiction between the text and the established world is always a finding. Do not resolve it silently. It has exactly two resolutions, and the finding must name both:

- **Fix the text.** The world stands; the passage changes. Usually the cheaper option.
- **Change the world deliberately.** The text is right and the record should move. This is a world change, not an edit: run an impact sweep first (`graph.py impact <slug>`), list what breaks, and hand off per "Feeding results back" below.

State which you recommend and why, but the author chooses.

## Evidence rules

Every finding needs:

- the persona and check id (for example `continuity / dead-character-active`)
- a quote from the text, with file and line (`story/chapters/05.md:42`), or a quote of the contradicting entity field with file and field (`world/characters/morwen.md`, `status`)
- the rule or record it breaks, or the craft reason
- a suggested direction, in one sentence, not a rewrite

No quote, no finding. Do not report guesses as errors: if you cannot confirm, mark severity `info` and say what would settle it. A persona with nothing to report says "no findings" and lists what it checked.

## Severity

| Level | Meaning | Examples |
|---|---|---|
| error | Breaks the world record or the story's logic; must be resolved | dead character acts, impossible travel, flag violation, validator error in scope |
| warning | Significant; should fix, author may overrule with reason | voice drift, magic cost skipped, stereotype, unresolved setup |
| info | Optional polish or a note | adverb density, tension plateau, missing breather |

Use the persona's own severity as the default. Raise it only with a stated reason (a repeated slip may be an error). Never lower a validator error.

## Output format

Open with a short header: project, target, in-world date, personas run, world flags relied on, validator result (error and warning counts).

Then one section per persona, in run order, each with a findings table:

| # | Sev | Check | Location | Evidence | Rule or record broken | Direction |
|---|---|---|---|---|---|---|
| 1 | error | dead-character-active | ch5:42 | "Morwen raised her bow" | `morwen.md` died at "The Siege", Y14 | Fix text, or revise death with impact sweep |

Add the persona's own extras where its `output_format` defines them (travel log, fact tracker, voice matrix, tension curve, thread tracker). Keep them brief.

Close with a prioritised fix list, across personas:

1. Errors first, ordered by how much else they affect (world-level contradictions before single-line slips).
2. Warnings, grouped by passage so the author can fix a scene once.
3. Info items as a single short list.

For each item say whether the fix is to the text, to the world, or either. Do not claim the manuscript passes. Say what was checked and what was not (for example "geography not run").

## Feeding results back

Review ends with findings. Changes start only on the user's word.

- **Accepted text fixes:** ask whether to apply them. If yes, make minimal edits, preserve voice, and rerun the persona that raised the issue plus `validate.py`.
- **Accepted world changes** (the world should bend to the text): this is a world edit. Load `worldbuilding` and follow its procedure: read before writing, trace causes, run `graph.py impact <slug>`, then the consequence sweep (step 3 of its procedure) loading the owning skill for every layer touched (see the table below). Update both sides of every relationship, then rerun `validate.py`. Report what changed in the world and which findings it closes.
- **New facts the text established** (a detail the text invented that is not a contradiction): offer to record them in the relevant entity, with causes and consequences, rather than leaving them only in prose.
- **Rejected findings:** note them as deliberate. If the author wants a contradiction kept as an intentional mystery or unreliable narration, record it in the entity (`origin_unknown`, a `contradicts` link on a tradition, or a note) so the next review does not raise it again.

## Which skill owns the fix

| Finding concerns | Load |
|---|---|
| Distances, terrain, climate, routes, travel time, seasons | `geography-and-climate` |
| Prices, trade, currency, wealth, food supply, institutions | `economy-and-trade` |
| Characters, species, languages, naming, factions, lineages, speech and accent | `peoples` |
| Dates, eras, who was alive when, event causes and order | `history-and-events` |
| Legends, customs, how an event is remembered or lost | `folklore-and-traditions` |
| Spells, costs, limits, supernatural creatures, magic flags | `magic-systems` |
| Any contradiction, any impact sweep | `world-validate` |
| The write-both-sides procedure for any change | `worldbuilding` |

Prose and pacing findings need no world skill; they are craft fixes in the text.

## Guardrails

- Advisory only. No edits to prose, entities or `project.yaml` during the review.
- Quote briefly, only the passage at issue.
- Do not invent world facts to make the text fit. If the record is silent, say so and offer options.
- Keep persona voices out of the report; use the findings format above, not roleplay.
- Australian spelling in the prose you write for the report, unless the manuscript uses another variety, in which case leave the manuscript's own spelling alone.
