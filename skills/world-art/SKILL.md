---
name: world-art
description: Generate consistent worldbuilding artwork (character portraits, location landscapes, faction emblems, item illustrations, species studies and event scenes) via the fal.ai OAuth MCP server, using entity image prompts, project visual style presets and world flags. Use when the user asks to illustrate, draw, paint, render or generate images or art for entities in a worldbuilding project.
---

# World art

Generates visual artwork for world entities through the connected `fal` MCP server (`https://mcp.fal.ai/mcp-relay`, Streamable HTTP with browser OAuth sign-in — no API key required) and saves the resulting images where `world-visualiser` picks them up automatically.

Every image must obey the world's canonical facts (`descriptions.machine`) and its rules (`world_flags`). Never let an image prompt invent magic, technology or features that contradict the project files.

## Before generating

1. **Locate the project** (the folder containing `project.yaml`) and read `project.yaml`:
   - Read `world_flags`, especially `world_flags.magic.present` and `world_flags.technology.*` (plus `reality.time_period` and `narrative.anachronisms`).
   - Read `style.visual` (preset, palette, lighting, negative prompt, seed notes). If `style.visual` is absent, pick an appropriate preset with the user from `references/style-presets.md` and record it in `project.yaml`.
2. **Read the target entity file(s)** under `world/<type-dir>/<slug>.md`, plus any directly referenced files needed for visual accuracy (for example, a character's `species`, `faction` heraldry, `location` climate/attire, or owned `item`).
3. **Verify against `world_flags`:**
   - **Magic gate:** If `world_flags.magic.present` is `false` (or `prevalence: none`), forbid glowing runes, arcane auras, floating objects, spell effects or supernatural creatures. Add `magic, glowing runes, arcane aura, fantasy spells` to the negative prompt.
   - **Technology gate:** Exclude any technology set to `false` (firearms if `gunpowder: false`, electric lamps if `electricity: false`, printed books if `printing: false`, modern fabrics/glass if medieval, etc.).
   - **Consistency:** Follow `descriptions.machine` verbatim for physical traits, scars, clothing, heraldry colours, materials and landmarks.

## Building the prompt

If the entity already has a non-empty `descriptions.image_prompt` in its YAML frontmatter, start from it and verify it still matches `descriptions.machine` and `world_flags`.

If `descriptions.image_prompt` is empty or missing:

1. Distil `descriptions.machine` (and `heraldry` for factions/lineages/locations) into a concrete visual subject description — composition, framing, subject details, materials, condition, setting and mood. Avoid abstract prose or non-visual facts (like voice or backstory).
2. Append the project's `style.visual` preset prompt suffix (see `references/style-presets.md`) and any project-level `palette` or `lighting` modifiers.
3. Combine the preset's `negative_prompt` with any `world_flags` exclusions.
4. Save the composed subject prompt back into the entity's `descriptions.image_prompt` field (keep it clean of provider-specific parameters so it stays portable).

## Generating via the `fal` MCP server

1. Inspect the tools exposed by the connected `fal` MCP server to find the available image-generation model/tool (prefer high-quality text-to-image models such as Flux for portraits, landscapes and scenes, or vector/graphic-friendly models for clean heraldry and emblems).
2. Choose an aspect ratio suited to the entity type (see `references/style-presets.md`):
   - `characters`, `species`: portrait (`3:4` or `2:3`)
   - `locations`, `events`: landscape (`16:9` or `3:2`)
   - `factions` (emblems/heraldry), `items`: square (`1:1`)
3. Call the `fal` MCP generation tool with the prompt, aspect ratio/dimensions, negative prompt (if supported by the model) and seed (if reusing one).
4. Download the generated image URL returned by `fal` and save it to:

   ```text
   <project>/output/images/<type-dir>/<slug>.png
   ```

   Use `.webp` or `.jpg` if the returned image is in that format (keep the actual format extension matching the file bytes). `<type-dir>` matches the entity folder name under `world/`: `characters`, `locations`, `factions`, `items`, `species`, `races`, `events`, `magic-systems`, `lineages`, `traditions`, `languages`, `arcs`.
5. Ensure parent directories exist before writing.
6. **Log usage, tokens and cost** to `<project>/output/art-usage.yaml` using [scripts/log_usage.py](./scripts/log_usage.py) (resolved relative to this skill's directory):

   ```bash
   python3 <this-skill-dir>/scripts/log_usage.py record <project-dir> \
     --entity <type-dir>/<slug> \
     --endpoint <endpoint-id> \
     --request-id <request-id> \
     --seed <seed> \
     --width <w> --height <h> \
     --unit-price <price> --unit <unit> \
     --tokens <tokens-if-reported> \
     --output-file output/images/<type-dir>/<slug>.<ext>
   ```

   Use `summary` to report accumulated spend and token usage for a world:

   ```bash
   python3 <this-skill-dir>/scripts/log_usage.py summary <project-dir> [--json]
   ```

## Batch generation

When the user asks to illustrate multiple entities (for example, all main characters, every city, or the whole project):

1. List the candidate entities and confirm the batch scope with the user before generating (to avoid unwanted usage/credits).
2. Check `style.visual` and `world_flags` once for the project.
3. Prepare or verify `descriptions.image_prompt` for every target entity first so all prompts share the same art direction.
4. Generate images one group at a time (e.g. portraits, then locations, then emblems), saving each to `<project>/output/images/<type-dir>/<slug>.<ext>`.
5. Report a concise summary table of generated files, skipped entities and any failures.

## Visual consistency tips

- **Lock one preset per project:** Set `style.visual.preset` in `project.yaml` and apply its suffix to every generation so portraits, landscapes and scenes feel part of one world.
- **Reuse palette and lighting:** Define `style.visual.palette` and `style.visual.lighting` in `project.yaml` (e.g. "muted slate blue, ochre, weathered bronze; overcast northern light").
- **Seed discipline:** Record useful seeds in notes or `style.visual` when generating variations of the same character, location or faction banner.
- **Heraldry fidelity:** For factions and lineages, pull exact colours, sigil shapes and blazons from the entity's `heraldry:` block so banners in scenes match the standalone emblem.
- **Reference images:** When a fal.ai model supports image-to-image or subject reference, pass an existing saved character portrait when rendering that character in an event scene.

## Updating the viewer

After saving new or updated images or audio, load the `world-visualiser` skill and rebuild the interactive viewer so the new artwork, looping soundtrack and character voice buttons appear automatically:

```bash
python3 <world-visualiser-dir>/scripts/build_viewer.py <project-dir> --embed-media
```

Tell the user the saved asset paths and the rebuilt `output/world-viewer.html` path.

## Soundtracks & Character Voices (Audio via `fal` MCP)

The same `fal` OAuth MCP server also supports low-cost **music** and **text-to-speech**:

- **World soundtrack (looping in the visualiser header with a mute toggle):** Save to `<project>/output/audio/theme.mp3` (or `.wav`/`.ogg`). Prefer cost-effective instrumental models such as `google/lyria-3.5` (~$0.10/generation; **never pass `negative_prompt`** — even though its schema lists the field, Lyria 3.5 rejects it at runtime with HTTP 422; put `"strictly instrumental, no vocals"` inside `prompt` instead).
- **Coordinate-locked painted world maps (optional):** Save to `<project>/output/images/world-map.png` (or `.jpg`). When using `fal-ai/flux/dev/image-to-image` over a deterministic elevation guide PNG, use `strength: 0.88–0.92` and avoid large flat bright-white regions in the guide (which FLUX may interpret as cloud cover).
- **Character voice samples ("Hear them speak" buttons in the Entity list and Detail panel):** Save to `<project>/output/audio/characters/<slug>.mp3` (or `.wav`). Prefer low-cost expressive TTS such as `google/gemini-3.8-flash-tts` (~$0.045 per 1,000 characters — keep lines to 1–2 crisp sentences, ~$0.005 each).
- Always log audio and music runs to `<project>/output/art-usage.yaml` via `scripts/log_usage.py record` (using `--unit generations` or `--unit characters` and `--cost-usd`) so every world tracks its total media spend.

## Graceful fallback when not signed in to `fal`

The `fal` MCP server uses OAuth browser sign-in (`https://mcp.fal.ai/mcp-relay`) and requires no API key. If the `fal` MCP tools are unavailable or return an authentication error:

1. Explain clearly that the `fal` MCP server needs a quick browser OAuth sign-in (no API key needed) and point the user to reconnect or sign in to the `fal` MCP server in their client's plugin/MCP settings.
2. Do not fabricate images or silently skip the user's request.
3. Offer to draft and save polished, `world_flags`-checked `descriptions.image_prompt` entries into the requested entity files right away so they are ready to render as soon as the user signs in (or to paste into any external image generator).

## References

- `references/style-presets.md`: visual style presets, prompt suffixes, negative prompts, aspect ratios and model selection guidance.
