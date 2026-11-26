# WorldBuilder

A Claude plugin for building fictional worlds that stay internally consistent. History, geography, climate, economy, peoples, magic and folklore are generated as linked Markdown files, and a built-in checker catches contradictions: broken links, one-way relationships, causes dated after their effects, characters acting after death, content that breaks your world rules.

It works in Claude Code and Cowork. Everything is plain files (YAML frontmatter plus Markdown), so a world is easy to read, edit and keep in git.

## What it does differently

- **Causal chains.** Every significant event records its causes and consequences. You can ask why something is the way it is (`why`) and what a change would affect (`impact`).
- **Two chains: truth and memory.** Myths, legends, customs and superstitions are modelled as traditions that descend from real events and distort them for named reasons, so a chain can end in the past and leave only a story.
- **A magic yes/no gate.** If your world has no magic, nothing supernatural gets written, and the checker enforces it.
- **A causal order for generation.** Geography and climate first, then resources, peoples, economy, history and folklore, so each layer follows from the last.

## Install

In Cowork: Customize, then Plugins, then upload this folder as a zip or add the repository as a marketplace.

In Claude Code:

```bash
claude --plugin-dir /path/to/worldbuilder
```

## Use

| Command | What it does |
|---|---|
| `/wb-new` | Start a project with a few guided questions |
| `/wb-wizard` | Full guided or YOLO world creation, validated at each stage |
| `/wb-validate` | Check the world for contradictions and fix them |
| `/wb-review` | Editorial review of prose against the world |
| `/wb-write`, `/wb-story`, `/wb-campaign` | Chapters, stories and campaign material |
| `/wb-compile` | Export a manuscript as Markdown or HTML |
| `/wb-readability` | Prose statistics |

You can also just talk to Claude: the skills load when you ask about geography, an economy, a species, a myth and so on.

## Skills

`worldbuilding` (core rules and routing), `world-wizard`, `history-and-events`, `geography-and-climate`, `economy-and-trade`, `peoples`, `magic-systems`, `folklore-and-traditions`, `writing`, `world-review`, `world-validate`, `prose-check`, `world-compile`.

A complete example world, The Lattice (a science-fiction setting with magic off), is in `skills/worldbuilding/assets/example-the-lattice/`.

## The checker

The scripts need only Python 3.9 or newer; PyYAML is bundled.

```bash
python3 skills/world-validate/scripts/validate.py <project-dir>
python3 skills/world-validate/scripts/graph.py <project-dir> why <event-slug>
python3 skills/world-validate/scripts/graph.py <project-dir> impact <slug>
python3 skills/world-validate/scripts/graph.py <project-dir> export --out graph.json
```

## Development

```bash
uv sync
uv run pytest -q
uv run ruff check .
```

Contributor rules are in `CLAUDE.md`.

## Licence

Apache 2.0. The vendored PyYAML is MIT licensed (see `skills/world-validate/scripts/vendor/`).
