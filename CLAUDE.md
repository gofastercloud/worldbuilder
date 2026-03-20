# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WorldBuilder is a structured worldbuilding and book-writing system. CLI tool + MCP server + Flask web UI. Everything is file-based (YAML frontmatter + Markdown), no database. Supports novels, series, D&D campaigns, and game worlds.

## Running

```bash
# CLI (main entry point)
python scripts/worldbuilder.py --help
python scripts/worldbuilder.py wizard yolo --size M --genre fantasy
python scripts/worldbuilder.py validate --project <path>
python scripts/worldbuilder.py compile --project <path> --format md

# Web UI (Flask dev server)
python webapp/app.py [port]  # default 5000

# MCP server (stdio transport for Claude Code)
python mcp_server/worldbuilder_mcp.py
```

Dependencies managed via `uv` (see `pyproject.toml`). Core: `pyyaml`, `flask`. Voice generation (optional): `uv sync --extra voicegen` — `mlx-audio`, `soundfile`, `numpy`. Image generation (optional): `uv sync --extra imagegen` — `mflux`. Both media backends are Apple Silicon only (MLX). Install both with `uv sync --extra all-media`.

## No Tests, No Linting

There is no test suite, no linter config, no CI/CD. This is a gap to be aware of.

## Architecture

### Three entry points, one source of truth

- **`scripts/worldbuilder.py`** (~4800 lines) — the CLI. All logic lives here: 22 commands covering init, add, validate, compile, edit, write, wizard, etc.
- **`mcp_server/worldbuilder_mcp.py`** (~1000 lines) — thin MCP wrapper that shells out to the CLI via subprocess. Not independent logic.
- **`webapp/app.py`** — Flask UI for browsing projects, image generation, voice generation.
- **`webapp/imagegen.py`** — Z-Image-Turbo image generation via mflux (MLX). LoRA-based style presets (photorealistic, anime, cartoon). Pre-quantized 4-bit model from `filipstrand/Z-Image-Turbo-mflux-4bit`.
- **`webapp/voicegen.py`** — Qwen3-TTS VoiceDesign voice generation via mlx-audio.
### Entity model

11 entity types: `character, location, faction, item, magic-system, arc, event, species, race, language, lineage`. Each is a `.md` file with YAML frontmatter (structured data) and Markdown body (prose). Entities cross-reference each other by kebab-case slug matching the filename.

### Key subsystems

- **Validation** — cross-ref resolution, timeline consistency, world flag enforcement, species/race hierarchy, bidirectional relationship checks
- **Triple descriptions** — each entity can have `machine` (structured truth), `human` (styled prose), `image_prompt` (illustration prompt)
- **World flags** — boolean constraints (gunpowder, magic, FTL, etc.) checked by validator against all content
- **Style cascade** — 13 visual styles × 14 prose styles, configured at project level, overridable per book/chapter
- **9 editor personas** — specialized review prompts (character, continuity, dialogue, geography, pacing, plot, prose, sensitivity, worldrules)
- **Wizard** — interactive or YOLO mode world generation with T-shirt sizing (S/M/L/XL)
- **Image generation** — Z-Image-Turbo (Apache 2.0, unrestricted) via mflux (MLX-native). 4-bit quantized, ~5.5GB model. LoRA-based style presets: default, photorealistic, anime, cartoon. Entity `image_prompt` fields describe subject only (no style instructions) — style is applied at render time by the selected LoRA. Negative prompt (quality guards) injected automatically. ~8s/step, 9 steps at 768x768. Apple Silicon only (MLX).
- **Voice generation** — Qwen3-TTS VoiceDesign (1.7B) via mlx-audio. Generates unique character voices from natural language descriptions. Output: MP3, 24kHz. Voice is auto-built from character `voice.description`, `voice.tags`, `voice.accent`, `voice.dialect`, with fallback to location `regional_defaults`. Characters can set `voice.instruct` for manual override. Apple Silicon only (MLX).
- **Regional defaults** — locations can define `regional_defaults` (ethnicity, appearance, voice accent/dialect) that characters inherit unless they override. Inheritance walks up the location parent chain.

### Asset layout

Templates, schemas, editor configs, and genre presets live in `assets/`. The CLI auto-discovers them.

### Project discovery

Any directory containing `project.yaml` is a project. The CLI and MCP server find projects by walking the filesystem.

## Conventions

- Cross-references use kebab-case slugs matching filenames (e.g., `faction: "the-silver-order"`)
- Relationships must be bidirectional — if A refs B, B must ref A
- Dates use the WorldDate system (era prefix + year, optionally month/day)
- `generate` and `write` commands output prompts for Claude, not prose directly
- Reference documentation for subsystems lives in `references/` (entity schemas, styles, descriptions, economy, editors, wizard)

## Example Project

`assets/example/the-shattered-crown/` is a working fantasy project. Use it as a reference for entity structure and cross-referencing patterns.
