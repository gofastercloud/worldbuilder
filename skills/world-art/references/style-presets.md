# Visual Style Presets Reference

Canonical reference for `style.visual` presets used by the `world-art` skill. Project-level defaults live in `project.yaml` under `style.visual` (schema in `skills/worldbuilding/assets/templates/styles.yaml`).

## Visual Style Presets

| Preset | Art Direction | Prompt Suffix | Default Negative Prompt |
|---|---|---|---|
| `painterly-fantasy` | Oil-painted fantasy concept art, rich brushwork, atmospheric depth | `oil painting, rich textured brushwork, atmospheric fantasy concept art, dramatic chiaroscuro, museum quality illustration` | `3d render, plastic skin, neon, modern clothing, watermark, text, signature` |
| `dark-ink` | High-contrast ink wash and woodcut, brooding shadows | `ink and wash illustration, fine cross-hatching, woodcut linework, stark shadows, muted parchment and charcoal tones` | `bright neon, glossy 3d, airbrushed, anime, watermark, text` |
| `watercolour-storybook` | Soft hand-painted watercolour with delicate ink outlines | `traditional watercolour illustration, fine sepia ink outlines, textured cold-press paper, warm natural pigments, storybook art` | `photorealistic, 3d render, harsh neon, glossy, watermark, text` |
| `cinematic-realism` | Live-action film still, natural lenses, grounded textures | `cinematic film still, 35mm anamorphic lens, natural lighting, weathered practical costumes and sets, shallow depth of field, high detail` | `cartoon, anime, painterly brushstrokes, plastic, cgi look, watermark, text` |
| `concept-art` | Clean studio production design, readable silhouettes and materials | `professional entertainment concept art, matte painting, clear silhouette, detailed material rendering, atmospheric perspective` | `blurry, amateur sketch, watermark, text, logo, frame` |
| `scifi-technical` | Crisp industrial design, clean hard-surface rendering | `hard science fiction industrial design illustration, clean technical precision, realistic weathered metal and composites, cinematic rim lighting` | `medieval fantasy, magic sparkles, painterly blur, watermark, text` |
| `retro-pulp` | Classic mid-century painted paperback cover art | `vintage painted pulp cover illustration, gouache and oil, bold composition, warm saturated highlights, dramatic shadows, canvas grain` | `minimalist vector, flat corporate art, sterile 3d, watermark, text` |
| `woodblock-print` | Traditional carved block print, flat layered colours, bold contours | `traditional woodblock print, bold carved outlines, flat layered mineral pigments, visible paper grain, disciplined composition` | `photorealistic, 3d render, soft airbrush, lens flare, watermark, text` |
| `graphic-novel` | Crisp inked comic art with cel-shaded or flat colour palettes | `European graphic novel illustration, clean ligne claire ink linework, cohesive flat colour palette, expressive framing` | `photorealistic, blurry painting, 3d render, watermark, text` |
| `heraldic-illuminated` | Medieval manuscript illumination and formal heraldry | `illuminated manuscript style, crisp flat heraldic tinctures, fine ink borders, vellum texture, gold leaf accents` | `photorealistic, 3d bevels, lens flare, modern gradients, watermark, text` |
| `custom` | Project-defined style using `style.visual.prompt_suffix` | Use `style.visual.prompt_suffix` from `project.yaml` | Use `style.visual.negative_prompt` from `project.yaml` |

## Aspect Ratios by Entity Type

| Entity Type | `<type-dir>` | Recommended Aspect | Composition Guidance |
|---|---|---|---|
| `character` | `characters` | `3:4` or `2:3` (portrait) | Head-and-shoulders or three-quarter portrait; keep distinguishing marks, attire and heraldry readable |
| `species` | `species` | `3:4` or `2:3` (portrait) | Naturalistic field-guide study showing anatomy, scale and native environment |
| `race` | `races` | `3:4` (portrait) | Cultural dress, everyday tools and architectural backdrop |
| `location` | `locations` | `16:9` or `3:2` (landscape) | Establishing wide shot from the approach described in `descriptions.machine.overview` |
| `event` | `events` | `16:9` (landscape) | Dramatic narrative scene capturing the turning point and environment |
| `faction` | `factions` | `1:1` (square) | Centred heraldic emblem, seal or banner on a clean neutral or parchment ground |
| `lineage` | `lineages` | `1:1` (square) | Formal house crest or coat of arms following the `heraldry` block |
| `item` | `items` | `1:1` (square) | Studio-style object study on a simple surface showing material, wear and scale |
| `tradition` | `traditions` | `16:9` or `4:3` | Cultural ritual, festival or artefact scene reflecting how the tradition is practised |
| `magic-system` | `magic-systems` | `16:9` or `1:1` | Diagrammatic or atmospheric depiction (only when `world_flags.magic.present` is `true`) |

## World-Flag Exclusion Prompts

Append these to the negative prompt whenever the corresponding flag is `false` (or `none`):

- `world_flags.magic.present: false` → `magic, glowing runes, arcane aura, floating objects, spell effects, energy beams, fantasy glow`
- `world_flags.technology.gunpowder: false` → `guns, firearms, rifles, pistols, cannons, gunpowder smoke`
- `world_flags.technology.electricity: false` → `electric lights, neon, power lines, lightbulbs, glowing screens, cables`
- `world_flags.technology.steam_power: false` → `steam engines, locomotives, brass steampunk gears, smokestacks`
- `world_flags.technology.internal_combustion: false` → `cars, motorcycles, asphalt roads, modern vehicles`
- `world_flags.technology.computing: false` → `computers, monitors, holograms, digital displays, circuit boards`
- `world_flags.technology.spaceflight: false` → `spaceships, rockets, spacesuits, orbital stations`

## Model Selection Guidance on fal.ai

Inspect the tools exposed by the connected `fal` MCP server before choosing a model rather than hardcoding stale model slugs:

- **Portraits, landscapes and scenes:** Prefer high-fidelity Flux-family text-to-image models for strong prompt adherence, lighting and natural anatomy.
- **Heraldry, faction emblems and seals:** Prefer graphic/vector-capable or clean illustrative models (such as Recraft or Flux with `heraldic-illuminated` / `dark-ink` framing) and avoid unsolicited text unless a motto is explicitly wanted.
- **Fast iteration / batch drafts:** Use a fast distilled variant first to verify composition and consistency, then re-render hero pieces at full quality.
- **Consistent characters across scenes:** When a model supports subject reference or image-to-image, pass the saved portrait from `output/images/characters/<slug>.png` as a reference.
