# WorldBuilder Quick Start

Get from zero to a generated world in under 10 minutes.

## Prerequisites

| Requirement | Details |
|---|---|
| **Platform** | macOS with Apple Silicon (M1/M2/M3/M4/M5+) |
| **RAM** | 16GB minimum, **32GB+ recommended** for image generation |
| **Python** | 3.10+ (3.12+ recommended) |
| **uv** | [Install uv](https://docs.astral.sh/uv/getting-started/installation/) |
| **Claude Code** | [Install Claude Code](https://docs.anthropic.com/en/docs/claude-code) or use the Claude Cowork app |

WorldBuilder is designed to be used inside Claude Code. The wizard, generate, write, and edit commands produce prompts that Claude processes — they don't generate prose on their own.

## 1. Clone and Install

```bash
git clone https://github.com/gofastercloud/worldbuilder.git
cd worldbuilder
uv sync
```

This installs the core dependencies (`flask`, `pyyaml`). The CLI and web viewer are ready to use immediately.

## 2. Install Optional Media Backends

Image and voice generation are optional visualization features. They help you see and hear your world, but aren't needed for worldbuilding itself.

```bash
# Voice generation only (~3.5GB model download on first use)
uv sync --extra voicegen

# Image generation only (~5.5GB model download on first use)
uv sync --extra imagegen

# Both voice and image generation
uv sync --extra all-media
```

### Model Downloads

All models download automatically from HuggingFace Hub on first use and are cached in `~/.cache/huggingface/hub/`. No manual setup needed.

| Model | Size | Purpose | RAM Needed |
|---|---|---|---|
| Qwen3-TTS VoiceDesign 1.7B (bf16) | ~3.5GB | Character voice generation | 16GB+ |
| Z-Image-Turbo (4-bit quantized) | ~5.5GB | Entity illustration | 32GB+ |
| Style LoRAs (per style) | ~200MB each | Photorealistic, anime, cartoon presets | included above |

The models are pre-quantized — there's no separate quantization step. First generation will be slower while the model loads; subsequent generations use the cached model.

### Using Lighter Models

If you're memory-constrained:

- **Voice**: Edit `MODEL_ID` in `webapp/voicegen.py` to point to a smaller mlx-audio compatible model
- **Image**: Edit `DEFAULT_WIDTH`, `DEFAULT_HEIGHT`, and `DEFAULT_STEPS` in `webapp/imagegen.py` to reduce resolution and steps (e.g., 512x512 with 6 steps)

## 3. Set Up Claude Code Integration

WorldBuilder integrates with Claude Code via an MCP server and a skill.

### MCP Server

Add the WorldBuilder MCP server to your Claude Code config. Create or edit `~/.claude/mcp_servers.json`:

```json
{
  "worldbuilder": {
    "command": "uv",
    "args": ["run", "--directory", "/path/to/worldbuilder", "python", "mcp_server/worldbuilder_mcp.py"],
    "env": {}
  }
}
```

Replace `/path/to/worldbuilder` with the actual path to your clone. Restart Claude Code for the MCP server to load.

This gives Claude access to 17+ tools for querying and manipulating your world — listing projects, browsing entities, searching, validating, generating images, and more.

### Skill

The WorldBuilder skill is automatically available if you're working in the WorldBuilder directory within Claude Code. It provides high-level worldbuilding workflows triggered by conversation context.

## 4. Generate Your First World

Open Claude Code in the worldbuilder directory and run:

```bash
uv run python scripts/worldbuilder.py wizard yolo --size M --genre fantasy --seed "a dying empire and forbidden magic"
```

This produces a structured prompt. In Claude Code, the wizard output is processed by Claude to generate:

- A `project.yaml` with world configuration and flags
- 30-90 entities across all 11 types (characters, locations, factions, species, etc.)
- A timeline spanning 2-3 historical eras
- An economy with currencies, resources, and trade routes
- Story arcs and an outline
- Cross-referenced relationships between all entities

### T-Shirt Sizes

| Size | Entities | Eras | Best For |
|------|----------|------|----------|
| **S** | 13-45 | 1-2 | Short story, one-shot session |
| **M** | 30-90 | 2-3 | Novel, short campaign |
| **L** | 87-253 | 3-5 | Book series, full campaign |
| **XL** | 173-555 | 4-8 | Epic universe, sandbox world |

### Genre Options

`fantasy`, `scifi`, `modern`, `horror`, `post-apocalyptic`, `steampunk`, `custom`

### Tone and Seed

- `--tone` sets the atmosphere: `epic`, `dark`, `gritty`, `whimsical`, `hopeful`, etc.
- `--seed` is a creative prompt that steers the generation: themes, premises, imagery, constraints

## 5. Explore Your World

### CLI

```bash
# Validate everything (cross-refs, timeline, world flags, relationships)
uv run python scripts/worldbuilder.py validate --project worlds/my-world

# Browse entities
uv run python scripts/worldbuilder.py list characters --project worlds/my-world
uv run python scripts/worldbuilder.py list locations --project worlds/my-world

# View the timeline
uv run python scripts/worldbuilder.py timeline --project worlds/my-world

# See the geography hierarchy
uv run python scripts/worldbuilder.py geography --project worlds/my-world

# Check world flags
uv run python scripts/worldbuilder.py flags --project worlds/my-world

# Full project stats
uv run python scripts/worldbuilder.py stats --project worlds/my-world
```

### Web UI

```bash
uv run python webapp/app.py 5050
# Open http://localhost:5050
```

The web UI provides:
- Entity browser with search
- Timeline visualization
- Geography view with location hierarchy
- Relationship graphs
- Image generation (if `imagegen` extra installed)
- Voice generation (if `voicegen` extra installed)

## 6. Add Content

```bash
# Add entities manually
uv run python scripts/worldbuilder.py add character "Kael Ashford" --project worlds/my-world
uv run python scripts/worldbuilder.py add faction "The Silver Order" --project worlds/my-world
uv run python scripts/worldbuilder.py add location "The Sunken Library" --project worlds/my-world

# Generate procedural history
uv run python scripts/worldbuilder.py generate conflict --years 50 --project worlds/my-world

# Write a chapter (generates a context-aware writing prompt for Claude)
uv run python scripts/worldbuilder.py write --chapter 1 --project worlds/my-world

# Generate a short story anchored to an event
uv run python scripts/worldbuilder.py story --event the-great-war --project worlds/my-world

# Generate a D&D campaign one-shot
uv run python scripts/worldbuilder.py campaign --present --location tavern-district \
  --length one-shot --level 3-5 --project worlds/my-world
```

## 7. Review and Edit

Run editor personas against your chapters to get specialized review prompts:

```bash
# List available editors
uv run python scripts/worldbuilder.py edit list

# Run a specific editor
uv run python scripts/worldbuilder.py edit continuity --chapter all --project worlds/my-world
uv run python scripts/worldbuilder.py edit worldrules --chapter 1-3 --project worlds/my-world

# Analyse prose readability
uv run python scripts/worldbuilder.py readability --project worlds/my-world --verbose
```

Available editors: `character`, `continuity`, `dialogue`, `geography`, `pacing`, `plot`, `prose`, `sensitivity`, `worldrules`

## What's Next

- See `assets/example/the-lattice/` for a complete sci-fi world (143 files, wizard-generated XL) with a story prompt, campaign module, and written chapter
- Read [REFERENCE.md](REFERENCE.md) for exhaustive documentation of all commands, schemas, flags, styles, and API endpoints
- Run `uv run python scripts/worldbuilder.py --help` for CLI usage
