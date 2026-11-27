# AGENTS.md

Guidance for coding agents (Antigravity, Claude Code, Codex) working on this repository.

## What this is

WorldBuilder is a multi-agent plugin (works natively in Antigravity, Claude Code / Cowork, and Codex) for building internally consistent fictional worlds. A world is a folder of Markdown files with YAML frontmatter. There is no database, no server, and no external runtime dependencies: the agent does the creative work guided by skills, and small stdlib-only Python scripts do the deterministic checking, compilation, readability analysis, and interactive visualisation.

The goal that outranks everything else is internal consistency: every significant fact has causes and consequences recorded in the files, relationships are reciprocal, and nothing contradicts the world flags.

## Layout

- `plugin.json` and `.claude-plugin/plugin.json`: plugin manifests (Antigravity native and Claude Code / Cowork). The repo root is the plugin root.
- `mcp_config.json` and `.mcp.json`: remote Streamable HTTP MCP configs for fal.ai OAuth (`https://mcp.fal.ai/mcp-relay`, no API key required).
- `skills/`: one folder per skill, each with `SKILL.md` (frontmatter `name` and `description` only) and optional `references/`, `scripts/`, and `assets/`.
  - `worldbuilding` (core contract, routing table, magic gate), `world-wizard`, `history-and-events`, `geography-and-climate`, `economy-and-trade`, `peoples`, `magic-systems`, `folklore-and-traditions`, `writing`, `world-review`, `world-validate`, `prose-check`, `world-compile`, `world-visualiser`, `world-art`.
  - `skills/worldbuilding/assets/`: entity templates and schemas, editor personas, and `example-the-lattice/`, a complete worked example (magic off) that must always validate with 0 errors and 0 warnings.
- `skills/world-validate/scripts/validate.py` and `graph.py`: the checker and graph layer (`why`, `impact`, `path`, `unrooted`, `export`). `vendor/yaml/` is a vendored pure-Python PyYAML.
- `skills/world-compile/scripts/compile.py`, `skills/prose-check/scripts/readability.py`, `skills/writing/scripts/story_campaign.py`: manuscript export, prose statistics, and dated short story / D&D 5e campaign brief generation.
- `skills/world-visualiser/scripts/viz_data.py` and `build_viewer.py`: builds (or serves on localhost via `--serve`) a self-contained single-file HTML viewer (`output/world-viewer.html`, with optional `--embed-media` / `--embed-images`) featuring 7 views: 3D causal graph, timeline, cartographic map (procedural Topographic/Parchment terrain + optional `world-map.png` backdrop), trade, life, gallery (with artwork, looping soundtrack & character voice audio), and content reader (stories, 5e campaigns, chapters with clickable entity links).
- `commands/`: slash commands for Claude Code / Cowork (`/wb-new`, `/wb-wizard`, `/wb-validate`, `/wb-review`, `/wb-write`, `/wb-story`, `/wb-campaign`, `/wb-compile`, `/wb-readability`, `/wb-visualise`, `/wb-art`). Antigravity and Codex trigger the same workflows directly via the skills.
- `tests/`: pytest suite for all scripts.

## Rules for changes

- Scripts are Python 3.9+, standard library plus the vendored YAML. Do not add runtime dependencies.
- `SKILL.md` frontmatter has only `name` and `description` (with `name` matching the folder name), valid YAML (no colon-space inside the description), and sandbox-safe: no `!` shell injection, no absolute paths, and no client-specific env vars like `${CLAUDE_SKILL_DIR}` — use relative paths from the skill directory. Keep `SKILL.md` under 300 lines and push detail into `references/`.
- Keep `plugin.json` and `.claude-plugin/plugin.json` in sync.
- A skill that needs the checker says "load `world-validate` and use its scripts".
- The magic yes/no flag (`world_flags.magic.present`) gates every supernatural element in every skill and in the validator. Traditions may describe magic as a belief; they never cause real effects.
- One canonical home for each rule or number; other skills point to it rather than restating it.
- Never weaken or delete a test to make it pass. Adding an entity to the example world legitimately changes counts: update them with a comment.

## Verify

```bash
make verify
# Runs:
#   uv run ruff check .
#   uv run pytest -q
#   python3 skills/world-validate/scripts/validate.py skills/worldbuilding/assets/example-the-lattice
```

## Entity model

Twelve types: `character`, `location`, `faction`, `item`, `magic-system`, `arc`, `event`, `species`, `race`, `language`, `lineage`, `tradition`. Cross-references are kebab-case slugs matching filenames. Dates use WorldDate (era prefix and year, optionally month and day) with eras defined in `world/history/calendar.yaml`. Events carry `caused_by`, `leads_to`, `root_causes`, `consequences`, and `traces`; traditions carry `origin_events`.

<!-- groundhog-agency:start -->
## Groundhog Agency Workflow (Vendor-Agnostic)

This repository uses **groundhog-agency** with Groundhog's `agent-git` / `agent-gh` broker. Works identically in **Claude Code**, **Antigravity**, and **Codex**:

- **Skills:** `/spec <idea>` (grill → spec + tickets), `/next [N]` (dispatch up to 3 tickets → `implementer` → fresh-context `reviewer` → ship PR), `/handoff` (update `STATUS.md` ≤40 lines → start fresh).
- **Roles:** canonical contracts live in `.agents/roles/{implementer,reviewer,scout}.md` (and `.claude/agents/` for Claude Code).
  - **Claude Code:** uses `.claude/agents/*.md`, `.claude/hooks/gtq.py`, and `.claude/settings.json`.
  - **Antigravity:** delegates via `invoke_subagent` (`implementer` in `Workspace: "share"`, `reviewer` read-only, `scout` on `flash`/`flash_lite`).
  - **Codex:** runs in `workspace-write` sandbox with isolated git worktrees per ticket.
- **Git & GitHub:** always use `agent-git` and `agent-gh` on `agent/<persona>/t-<N>-<slug>` branches, label PRs `agent-authored`, and respect `groundhog agent-git status` (`autonomous` vs `human-review`). Never push directly to `main`/`master`.
- **Compact instructions:** when compacting, keep ticket numbers and branches in flight, PR numbers, decisions and reasons, open questions for the maintainer, and the next action. Drop tool output, file contents, diffs, and anything already in an issue or `STATUS.md`.
<!-- groundhog-agency:end -->
