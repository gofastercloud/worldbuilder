# Style System Reference

Controls all generated prose, visual output, and descriptions. Cascades from project → book → chapter.

## Visual Style Presets (13)

Controls image generation and visual descriptor formatting.

| Preset | Aesthetic | Best For |
|--------|-----------|----------|
| realistic | Photorealistic, cinematic lighting | Modern/historical, grounded fantasy |
| painterly | Oil painting, concept art (Frazetta, Vallejo) | Epic fantasy, dramatic scenes |
| anime | Japanese animation (Ghibli, Makoto Shinkai) | Soft-focus, emotional moments |
| manga | Black and white manga panels | Action sequences, stark contrasts |
| comic-book | Western comic style (Marvel/DC) | Superhero, action-forward |
| pixel-art | Retro pixel art | Sci-fi, indie games, vintage feel |
| art-nouveau | Mucha-inspired decorative style | Fantasy, historical, ornamental |
| dark-fantasy | Berserk, Dark Souls aesthetic | Horror fantasy, gothic |
| sci-fi-concept | Hard SF concept art (Syd Mead, Chris Foss) | Hard sci-fi, technical |
| cyberpunk | Neon-noir (Blade Runner, Akira) | Dystopian, futuristic cities |
| watercolor | Soft, flowing watercolor illustration | Gentle fantasy, introspective |
| woodcut | Medieval woodcut/linoprint style | Historical, mythic, medieval |
| stained-glass | Stylized religious/mythic art | Sacred moments, formal/ceremonial |
| custom | User-defined style | Custom requirements |

## Visual Style Global Modifiers

Applied to ALL image prompts. Can be overridden per chapter/book.

| Modifier | Type | Options | Default |
|----------|------|---------|---------|
| lighting | enum | natural, dramatic, cinematic, soft, harsh, neon, candlelit, moonlit, golden-hour, overcast, custom | cinematic |
| color_palette | enum | vibrant, muted, monochrome, warm, cool, earth-tones, jewel-tones, pastel, desaturated, high-contrast, custom | muted |
| camera | enum | eye-level, low-angle, high-angle, birds-eye, dutch-angle, close-up, medium-shot, wide-shot, portrait, cinematic-wide, custom | cinematic-wide |
| mood | enum | epic, intimate, ominous, hopeful, melancholy, tense, serene, chaotic, mysterious, triumphant, custom | epic |
| detail_level | enum | minimal, moderate, detailed, hyper-detailed | detailed |
| negative_prompt | string | Things to AVOID in images | "watermark, text, logo, signature, blurry, low quality, deformed" |

**Example:** visual_style.preset = "dark-fantasy" + lighting = "candlelit" + color_palette = "desaturated" → grim, moody fantasy scenes

## Prose Style Presets (14)

Controls how Claude generates prose: voice, vocabulary, pacing, content.

| Preset | Voice | Pace | Best For |
|--------|-------|------|----------|
| literary | Elegant, metaphor-rich | Measured | Rothfuss, Le Guin |
| pulp | Fast-paced, punchy | Breakneck | Howard, Salvatore |
| young-adult | Accessible, emotional | Fast | Sanderson, Riordan |
| dark | Grim, unflinching, morally gray | Varied | Abercrombie, Martin |
| gritty | Street-level, visceral, noir | Moderate | Morgan, Low Town |
| epic | Grand scope, formal | Deliberate | Tolkien, Jordan |
| litrpg | Game-stat aware, progression | Fast | System-visible narratives |
| cozy | Warm, low-stakes, comfort | Slow | Pratchett, Becky Chambers |
| horror | Dread-building, unreliable narrator | Variable | King, Barker |
| hard-sf | Technical precision, idea-driven | Deliberate | Clarke, Egan |
| space-opera | Grand space adventure | Fast | Banks, Reynolds |
| noir | First-person cynical, hardboiled | Fast | Chandler |
| fairy-tale | Once-upon-a-time, archetypal | Variable | Oral tradition feel |
| custom | User-defined | User-defined | Custom blends |

## Prose Voice Controls

Fine-grained prose configuration.

### POV & Tense

| Setting | Options | Default | Notes |
|---------|---------|---------|-------|
| POV | first-person, second-person, third-limited, third-omniscient, third-deep, rotating-pov, unreliable | third-limited | Which perspective? |
| tense | past, present, future | past | Narrative time |
| formality | colloquial, casual, neutral, formal, archaic, mixed | neutral | Narrative voice formality |

### Vocabulary

| Setting | Options | Default | Notes |
|---------|---------|---------|-------|
| complexity | simple, moderate, rich, ornate | moderate | "simple" for YA, "ornate" for literary |
| anachronism_tolerance | strict, moderate, loose | moderate | "strict" bans modern phrasing |
| profanity | none, mild, moderate, heavy, invented-only | invented-only | "invented-only" = in-world oaths only |

### Pacing

| Setting | Options | Default | Notes |
|---------|---------|---------|-------|
| default_tempo | breakneck, fast, moderate, deliberate, slow, variable | moderate | Story speed |
| scene_length | short, medium, long, variable | medium | ~500w / ~1500w / ~3000w |
| chapter_length | string | "3000-5000 words" | Target word count |

### Content Rating

| Rating | Description | Default |
|--------|-------------|---------|
| all-ages | No violence, no romance, no horror | — |
| middle-grade | Mild peril, no gore, no romance | — |
| young-adult | Violence without gore, fade-to-black romance | — |
| adult | On-page violence, romance, dark themes | ✓ default |
| mature | Graphic violence, explicit content, extreme themes | — |

## Description Modifiers

Control how machine_description → human_description conversion works.

| Modifier | Type | Options | Default | Effect |
|----------|------|---------|---------|--------|
| sensory_emphasis | list | sight, sound, smell, taste, touch | [sight, sound, smell] | Which senses emphasized |
| metaphor_density | enum | sparse, moderate, rich | moderate | How poetic the language |
| internal_monologue | enum | minimal, moderate, deep | moderate | POV character's thoughts on page |

## Narration Style

For AI audiobook narration output.

| Setting | Options | Default | Notes |
|---------|---------|---------|-------|
| preset | dramatic, conversational, formal, storyteller, neutral, documentary | dramatic | Narrator delivery style |
| voice_direction | string | — | General narrator voice (e.g., "warm baritone, measured pace, British RP") |
| character_voices | boolean | true | Should narrator do distinct character voices? |
| pacing | slow, moderate, fast, dynamic | dynamic | Narration speed |

## Image Prompt Templates

Per-entity-type templates that assemble final image prompts from entity fields + style settings.

### Character Template
```
{visual_style.preset} portrait of {name}, {species} {race},
{physical_description}. {clothing_and_equipment}.
Setting: {location}. Mood: {visual_style.mood}.
{visual_style.lighting} lighting, {visual_style.color_palette} palette,
{visual_style.camera} shot, {visual_style.detail_level} detail.
--no {visual_style.negative_prompt}
```

### Location Template
```
{visual_style.preset} {location_type} landscape,
{description}. Climate: {climate}. Time: {time_of_day}.
{visual_style.lighting} lighting, {visual_style.color_palette} palette,
{visual_style.camera} shot, {visual_style.detail_level} detail.
--no {visual_style.negative_prompt}
```

### Item Template
```
{visual_style.preset} {item_type}, {description}.
Materials: {materials}. Context: {context}.
{visual_style.lighting} lighting, {visual_style.detail_level} detail.
--no {visual_style.negative_prompt}
```

### Scene Template
```
{visual_style.preset} scene, {description}.
Characters: {characters}. Location: {location}.
Action: {action}. Mood: {mood}.
{visual_style.lighting} lighting, {visual_style.color_palette} palette,
{visual_style.camera} shot, {visual_style.detail_level} detail.
--no {visual_style.negative_prompt}
```

### Map Template
```
{visual_style.preset} fantasy map of {region},
showing {features}. Style: {map_style}.
{visual_style.color_palette} palette, birds-eye view.
--no {visual_style.negative_prompt}
```

## Style Cascading

Style settings cascade from highest to lowest precedence:

```
1. Chapter-level style overrides (if set in chapter YAML)
   ↓
2. Book-level style overrides (if set in book YAML)
   ↓
3. Project-level default style (in project.yaml)
   ↓
4. System defaults (this reference)
```

Example: Project uses visual_style=realistic, but Chapter 5 overrides to anime → Chapter 5 uses anime style for all entities, rest of project uses realistic.

## Where Styles Are Defined

- **Project default:** `project.yaml` → `style:` block
- **Book override:** `story/books/{book}.yaml` → `style:` block
- **Chapter override:** `story/chapters/{chapter}.yaml` → `style:` block

## Common Style Combinations

| Genre | Visual | Prose | Lighting | Palette | Example |
|-------|--------|-------|----------|---------|---------|
| Epic Fantasy | painterly | epic | golden-hour | vibrant | Rothfuss + concept art |
| Dark Fantasy | dark-fantasy | dark | harsh | desaturated | Abercrombie + gothic |
| Cozy Fantasy | watercolor | cozy | soft | warm | Discworld + illustration |
| Hard Sci-Fi | sci-fi-concept | hard-sf | cinematic | cool | Clarke + technical art |
| Space Opera | anime | space-opera | dramatic | vibrant | Banks + anime aesthetic |
| Cyberpunk | cyberpunk | noir | neon | high-contrast | Neuromancer + neon |
| Horror | dark-fantasy | horror | candlelit | monochrome | King + atmospheric |

## Quick Tips

- **Visual style** affects only image generation and image_prompt descriptions
- **Prose style** affects human-readable prose generation
- **Voice/POV/tense** locked at project level for consistency (can override per-book carefully)
- **Content rating** filters what kinds of scenes Claude will write (locked to project level)
- **machine_description** is NEVER styled — it's raw facts for Claude's reference
- **human_description** is derived from machine_description + prose_style settings
- **image_prompt** is derived from machine_description + visual_style settings
