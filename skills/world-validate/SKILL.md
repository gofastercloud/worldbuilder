---
name: world-validate
description: Check a worldbuilding project for contradictions and broken links, then fix them. Use after adding or changing any world content, before declaring worldbuilding work finished, or when the user asks whether their world is consistent. Covers dangling references, one-way relationships, timeline and lifespan errors, world-flag violations, causal-chain problems such as effects that precede their causes, and traditions (myths, customs, taboos) that do not trace back to a real event.
---

# World validation

Run the checker, read its findings, fix the real problems, rerun.

## Run

Run [scripts/validate.py](./scripts/validate.py) (resolved relative to this skill's directory):

```
python3 <this-skill-dir>/scripts/validate.py <project-dir>
```

Options: `--json` for machine-readable output, `--severity error` to hide warnings. Exit code 1 means at least one error. The script needs only Python 3.9+; PyYAML is bundled.

If `python3` is missing or the script cannot run, tell the user, then do the checks by hand by reading the files, using the list below, and say the check was manual.

## Tracing causes and consequences

`graph.py` ([scripts/graph.py](./scripts/graph.py)) builds the world as a graph (entities as nodes, typed links as edges):

```
python3 <this-skill-dir>/scripts/graph.py <project-dir> <command> [args]
```

- `why <slug>`: the full upstream causal ancestry of an event, down to its root causes. Use it to check an event really is explained. For a tradition it lists the origin events first (marked `[memory link: origin of tradition]`, since a tradition is remembered from an event, not caused by it) and then each event's causal ancestry.
- `impact <slug> [--depth N]`: everything downstream of an entity or event, causal effects first, then places, members and routes that depend on it. For an event it also lists `Traces in the present`: the traditions and other entities it left behind, with their status. Run it before changing an established fact, and update every entity it lists.
- `path <a> <b>`, `neighbors <slug>`: how two things connect.
- `unrooted`: events with no causal ancestry and no `root_causes`, traditions with no origin event, and entities with no links.
- `stats`: counts, connected components and causal depth.
- `export --out graph.json`: the whole graph as JSON for visualisation. Edges of kind `leaves-trace` run from an event to each tradition or entity in its `traces` (and to each tradition naming it in `origin_events`), one edge per pair.

Add `--json` to any command for machine-readable output.

## What it checks

Errors:
- unparseable or unclosed frontmatter; a file that cannot be read
- missing targets for character relationships, chapter POV and event participants, and causal links (`caused_by`, `leads_to`) that point at a non-event
- a race whose species is missing or not a species; intelligibility scores outside 0 to 1
- circular location hierarchies; river `hydrology.flows_to` cycles
- characters acting before birth or after death, birth after death
- a parent under 16 years older than the child; a faction leader who is not a character, or is dead
- broken family, species/race and lineage links (one side lists the other, the other does not list back)
- a character's race belonging to a different species; birth events with parents of different species when cross-species breeding is off or undefined
- content that contradicts a world flag: technology transport (train, car, spaceship...), magical transport (teleportation, ley-line, portal, magic carpet...) when `world_flags.magic.present` is false, magic systems or references to them when magic is absent
- causes dated later than their effects, or in a cycle; an end date before a start date
- a tradition whose `origin_events` names a missing event or a non-event; a tradition whose `first_attested` is earlier than its earliest origin event (`tradition-before-origin`)

Warnings:
- a missing faction, location, parent location, route destination, organisation, location or item on an event, or any other reference not listed above
- relationships, faction membership, notable characters, routes and allies that are not reciprocated
- events with no cause, effect or consequences recorded; significant events (`important`, `crucial`, `world-changing`; legacy `major` and `critical` are tolerated) with no cause or no effect (a non-empty `traces` or a valid `open_ended` counts as an effect)
- a tradition with neither `origin_events` nor `origin_unknown` (`orphan-tradition`); a purely oral tradition marked `fidelity: accurate` 300 or more years after its earliest origin event, when the present date (`present_date` or `current_date` in `project.yaml` or `calendar.yaml`) is known (`implausible-fidelity`)
- an event `traces` entry or a tradition `origin_events` entry that the other side does not reciprocate; `contradicts` that is not mutual; missing `held_by`, `regions`, `places`, `language`, `related` or `traces` targets
- entities used before they existed or after they ended; a death event for a character not marked dead
- an event era prefix that `world/history/calendar.yaml` does not define (only when the calendar lists eras)
- `flows_to` pointing uphill when both places have `elevation_m`; unresolved `flows_to`, `climate_profile` and flora/fauna `species` references (plain `name:` entries are fine)
- magic words in any frontmatter text field (not the Markdown body, and not traditions, which record beliefs rather than facts about the world) when magic is absent, unless listed in `world_flags.magic.exceptions` or its notes; incomplete magic systems when magic is present; technology words in chapter prose when the flag is false; a faction with no leader or whose leader is not a member

## How other skills call this

Other skills say "load `world-validate` and use its scripts". Resolve `<this-skill-dir>` to the directory containing this `SKILL.md` file (so the commands work from any working directory in Antigravity, Claude, or Codex):

```
python3 <this-skill-dir>/scripts/validate.py <project-dir>
python3 <this-skill-dir>/scripts/graph.py <project-dir> why <event-slug>
python3 <this-skill-dir>/scripts/graph.py <project-dir> impact <slug>
```

## Fixing findings

1. Group findings by entity and read each file named.
2. Decide the cause. A missing reverse link is usually a one-line edit. A date conflict needs a judgement: change the date, change the link, or remove it. Tell the user which you chose and why when a fix changes established facts.
3. For warnings about missing causes or consequences, use the `worldbuilding` skill: work out what really caused or followed the event and record it in the affected files. Do not write filler to silence a warning.
4. Rerun until no errors remain. Report remaining warnings honestly, with the reason for any left unresolved.

Never edit the checker or its tests to make a world pass.
