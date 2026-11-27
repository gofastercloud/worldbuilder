# WorldBuilder

A multi-agent plugin (**Antigravity**, **Claude Code / Cowork**, and **Codex**) for building fictional worlds that stay internally consistent. History, geography, climate, economy, peoples, magic, and folklore are generated as linked Markdown files, a built-in checker catches contradictions, and an interactive single-file viewer lets you explore your world in 3D and 2D.

Everything is plain files (YAML frontmatter plus Markdown) and zero-dependency Python 3.9+ scripts (PyYAML is vendored), so a world is easy to read, edit, and version with Git — and runs natively inside desktop agent clients.

## What it does differently

- **Causal chains.** Every significant event records its causes and consequences. You can ask why something is the way it is (`why`) and what a change would affect (`impact`).
- **Two chains: truth and memory.** Myths, legends, customs, and superstitions are modelled as traditions that descend from real events and distort them for named reasons, so a chain can end in the past and leave only a story.
- **A magic yes/no gate.** If your world has no magic, nothing supernatural gets written, and the checker enforces it.
- **A causal order for generation.** Geography and climate first, then resources, peoples, economy, history, and folklore, so each layer follows from the last.
- **Interactive world visualiser.** Builds a self-contained `output/world-viewer.html` (with optional `--embed-media` / `--embed-images`, or `--serve [--port 8765]` for a zero-dependency local webserver with auto-rebuild and audio streaming) featuring **7 views**: 3D causal graph, timeline, cartographic map (procedural Topographic & Parchment terrain plus optional painted/custom `world-map.png` backdrop), trade network, climate/life, artwork gallery (with looping world soundtrack & character voice playback), and a **Content** reader for generated stories and D&D 5e campaigns with clickable entity links.
- **Zero-key fal.ai artwork, maps & audio.** Connects to fal.ai's official remote MCP server (`https://mcp.fal.ai/mcp-relay`) using browser OAuth (no API key needed) to generate portraits, landscapes, emblems, coordinate-locked painted maps, ambient soundtracks, and character TTS voices that flow straight into the visualiser.
- **Dated short stories & D&D 5e campaigns.** `skills/writing/scripts/story_campaign.py` assembles spoiler-free, dated story briefs (anchored to an event, myth/tradition, or era) and D&D 5e-compatible campaign briefs (calibrated party tiers, DCs/CRs, magic-gate rules, faction clocks, and d6/d8 rumour tables built from real traditions).

## Install

### Antigravity (Gemini)

Link or copy this repository into your global or workspace plugins folder:

- Global: `~/.gemini/config/plugins/worldbuilder/`
- Workspace: `.agents/plugins/worldbuilder/`

Antigravity automatically discovers `plugin.json`, `mcp_config.json` (fal.ai OAuth MCP), and all 15 skills under `skills/`.

### Claude Code & Cowork

- **Cowork:** Customize → Plugins → upload this folder as a zip or add the repository as a marketplace.
- **Claude Code:**

```bash
claude --plugin-dir /path/to/worldbuilder
```

`.mcp.json` wires up the fal.ai OAuth MCP server automatically — sign in via browser when first prompted.

### Codex

Copy or symlink **all** skill folders inside `skills/` together into `~/.codex/skills/` (or `.codex/skills/` in a workspace), as the compile and visualiser scripts share the vendored YAML library in `world-validate/scripts/`. For artwork generation, connect the remote fal.ai OAuth MCP server (`https://mcp.fal.ai/mcp-relay`).

## Use

Just talk to your agent — the skills load automatically when you ask to start a world, add geography, design an economy or species, check consistency, or visualise your world.

In Claude Code / Cowork, you can also invoke the slash commands directly:

| Command | Skill | What it does |
|---|---|---|
| `/wb-new` | `world-wizard` | Start a project with a few guided questions |
| `/wb-wizard` | `world-wizard` | Full guided or YOLO world creation, validated at each stage |
| `/wb-validate` | `world-validate` | Check the world for contradictions and fix them |
| `/wb-visualise` | `world-visualiser` | Build or `--serve` the interactive HTML viewer (3D graph, timeline, terrain map, trade, life, gallery, content) |
| `/wb-art` | `world-art` | Generate portraits, landscapes, emblems, painted maps, and audio via fal.ai OAuth MCP |
| `/wb-review` | `world-review` | Editorial review of prose against the world |
| `/wb-write`, `/wb-story`, `/wb-campaign` | `writing` | Chapters, dated short stories (event/myth/era), and D&D 5e-compatible campaigns |
| `/wb-compile` | `world-compile` | Export a manuscript as Markdown or HTML |
| `/wb-readability` | `prose-check` | Prose readability statistics |

## Skills

`worldbuilding` (core rules and routing), `world-wizard`, `history-and-events`, `geography-and-climate`, `economy-and-trade`, `peoples`, `magic-systems`, `folklore-and-traditions`, `writing`, `world-review`, `world-validate`, `prose-check`, `world-compile`, `world-visualiser`, `world-art`.

A complete example world, **The Lattice** (a science-fiction setting with magic off), is in `skills/worldbuilding/assets/example-the-lattice/`.

## Scripts

All scripts require only Python 3.9+ (PyYAML is bundled):

```bash
python3 skills/world-validate/scripts/validate.py <project-dir>
python3 skills/world-validate/scripts/graph.py <project-dir> why <event-slug>
python3 skills/world-validate/scripts/graph.py <project-dir> impact <slug>
python3 skills/world-visualiser/scripts/build_viewer.py <project-dir> [--serve --port 8765]
python3 skills/writing/scripts/story_campaign.py story <project-dir> --event <slug>
python3 skills/writing/scripts/story_campaign.py campaign <project-dir> --era <prefix> --year <Y> --level 1-4
python3 skills/world-compile/scripts/compile.py <project-dir> --format md
python3 skills/prose-check/scripts/readability.py <path>
```

## Development

```bash
make verify
```

Contributor rules are in [AGENTS.md](./AGENTS.md).

## Licence

Apache 2.0. The vendored PyYAML is MIT licensed (see `skills/world-validate/scripts/vendor/`).
