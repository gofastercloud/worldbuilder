# Style System Reference

Controls all generated prose and descriptions. Cascades from project → book → chapter.

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

Example: Project uses prose_style=literary, but Chapter 5 overrides to noir → Chapter 5 uses noir prose for all entities, rest of project uses literary.

## Where Styles Are Defined

- **Project default:** `project.yaml` → `style:` block
- **Book override:** `story/books/{book}.yaml` → `style:` block
- **Chapter override:** `story/chapters/{chapter}.yaml` → `style:` block

## Quick Tips

- **Prose style** affects human-readable prose generation
- **Voice/POV/tense** locked at project level for consistency (can override per-book carefully)
- **Content rating** filters what kinds of scenes Claude will write (locked to project level)
- **machine_description** is NEVER styled — it's raw facts for Claude's reference
- **human_description** is derived from machine_description + prose_style settings
