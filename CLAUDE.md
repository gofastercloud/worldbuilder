# CLAUDE.md

Guidance for Claude Code when working on this repository.

## What this is

WorldBuilder is a Claude plugin (works in Claude Code and Cowork) for building internally consistent fictional worlds. A world is a folder of Markdown files with YAML frontmatter. There is no database, no server and no CLI: Claude does the creative work guided by skills, and small stdlib-only Python scripts do the deterministic checking.

The goal that outranks everything else is internal consistency: every significant fact has causes and consequences recorded in the files, relationships are reciprocal, and nothing contradicts the world flags.

## Layout

- `.claude-plugin/plugin.json`: plugin manifest. The repo root is the plugin root.
- `skills/`: one folder per skill, each with `SKILL.md` (frontmatter `name` and `description` only) and optional `references/`.
  - `worldbuilding` (core contract, routing table, magic gate), `world-wizard`, `history-and-events`, `geography-and-climate`, `economy-and-trade`, `peoples`, `magic-systems`, `folklore-and-traditions`, `writing`, `world-review`, `world-validate`, `prose-check`, `world-compile`.
  - `skills/worldbuilding/assets/`: entity templates and schemas, editor personas, and `example-the-lattice/`, a complete worked example (magic off) that must always validate with 0 errors and 0 warnings.
- `skills/world-validate/scripts/validate.py` and `graph.py`: the checker and the graph layer (`why`, `impact`, `path`, `unrooted`, `export`). `vendor/yaml/` is a vendored pure-Python PyYAML.
- `skills/world-compile/scripts/compile.py`, `skills/prose-check/scripts/readability.py`: manuscript export and prose statistics.
- `commands/`: slash commands (`/wb-new`, `/wb-wizard`, `/wb-validate`, `/wb-review`, `/wb-write`, `/wb-story`, `/wb-campaign`, `/wb-compile`, `/wb-readability`).
- `tests/`: pytest suite for all scripts.

## Rules for changes

- Scripts are Python 3.9+, standard library plus the vendored YAML. Do not add runtime dependencies.
- SKILL.md frontmatter has only `name` and `description`, valid YAML (no colon-space inside the description), and Cowork-safe: no `!` shell injection, no absolute paths. Keep SKILL.md under 300 lines and push detail into `references/`.
- A skill that needs the checker says "load `world-validate` and use its scripts": `${CLAUDE_SKILL_DIR}` resolves to the loaded skill's own folder.
- The magic yes/no flag (`world_flags.magic.present`) gates every supernatural element in every skill and in the validator. Traditions may describe magic as a belief; they never cause real effects.
- One canonical home for each rule or number; other skills point to it rather than restating it.
- Never weaken or delete a test to make it pass. Adding an entity to the example world legitimately changes counts: update them with a comment.

## Verify

```bash
python -m pytest -q
ruff check .
python skills/world-validate/scripts/validate.py skills/worldbuilding/assets/example-the-lattice
claude plugin validate .
```

## Entity model

Twelve types: character, location, faction, item, magic-system, arc, event, species, race, language, lineage, tradition. Cross-references are kebab-case slugs matching filenames. Dates use WorldDate (era prefix and year, optionally month and day) with eras defined in `world/history/calendar.yaml`. Events carry `caused_by`, `leads_to`, `root_causes`, consequences and `traces`; traditions carry `origin_events`.
