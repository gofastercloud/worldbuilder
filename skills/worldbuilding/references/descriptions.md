# Description System Reference

Description architecture: `machine` (source facts), `human` (styled prose), and optional `image_prompt` (visual art).

## The Description Variants

Every entity MUST have a `descriptions` block with `machine` and `human`, and MAY include an optional `image_prompt`:

1. **machine** (required) = SOURCE OF TRUTH
   - Structured, factual, deterministic
   - The assistant reads this during generation for consistency
   - Never styled, no flowery language
   - Written once, reused everywhere

2. **human** (required) = READER-FACING PROSE
   - Derived from `machine` + `style.prose` settings
   - Evocative, styled according to genre/tone
   - What appears in published work
   - Variable per style context

3. **image_prompt** (optional) = VISUAL ART PROMPT
   - Derived from `machine` + `style.visual` settings (and `heraldry` where present)
   - Used by the `world-art` skill to generate portraits, landscapes, emblems, items and scenes via the `fal` OAuth MCP server
   - Must stay visual-only (composition, materials, lighting, distinguishing marks) and obey `world_flags` (no magic if `world_flags.magic.present` is `false`, no disallowed technology)

**Example:** A character's `machine` description stays identical. From it, a literary novel produces flowing prose, a cozy fantasy produces warm narration, and `world-art` produces a consistent portrait prompt — all from the same source facts.

## YAML Frontmatter Structure

```yaml
descriptions:
  machine:
    # Structured fields specific to entity type
    physical: "..."
    clothing: "..."
    demeanor: "..."
    # (see entity-specific schemas below)
  human: |
    Prose paragraph describing the entity.
    Can span multiple sentences. Styled by
    style.prose settings from project.yaml.
  image_prompt: ""  # optional; visual-only subject prompt for world-art
```

## Character Machine Description

| Field | Content | Example |
|-------|---------|---------|
| physical | Height, build, coloring, age appearance, species traits | "6'1", lean athletic build, dark brown hair in short military cut, golden-brown eyes (Dawnblade bloodline), fair skin weathered by sun" |
| face | Facial features, distinguishing marks | "Strong jaw (Dawnblade trait), scar from left temple to jawline (thin, white, recent), habitually set expression, furrowed brow" |
| clothing | Default outfit, armor, colors, materials, condition, emblems | "Battered Silver Order surcoat (deep blue linen, winged sword emblem in faded silver thread, torn at hem), brown leather armor underneath, worn sword belt, Silver Order insignia at collar" |
| equipment | Weapons, tools, carried items | "Inherited longsword (plain steel, leather-wrapped grip, Dawnblade family mark on pommel), belt knife, water skin" |
| demeanor | Default body language, stance, energy | "Alert, tense, shoulders slightly forward, hand resting on sword hilt, always scans exits. Moves with trained economy." |
| voice | How they sound (dialogue and narration consistency) | "Mid-range baritone, clipped sentences, military cadence, Valdrian accent (sounds roughly like Northern English)" |
| distinguishing | The 2-3 instantly recognizable traits | "Scar from temple to jaw, golden-brown Dawnblade eyes, battered Silver Order surcoat" |

## Location Machine Description

| Field | Content | Example |
|-------|---------|---------|
| overview | What you see from distance/on approach | "Walled city on a river plateau, three concentric rings of white stone walls, visible for 20 miles" |
| architecture | Building style, materials, condition | "White limestone walls, slate roofs, heavy buttresses. Military architecture — functional over decorative. Crown Ring buildings are older, more ornate." |
| atmosphere | Sounds, smells, ambient feel | "Clang of smiths, market shouting, horses on cobblestone. Smells of woodsmoke, horse dung, bread. Crowded but orderly." |
| landmarks | 2-3 instantly recognizable features | "The Shattered Throne (visible crack in the palace dome), the Silver Bastion (fortress within a fortress), the Weave Gate spire" |
| time_of_day | How location changes throughout day | "Dawn: quiet except drilling soldiers. Midday: market noise peaks. Dusk: taverns fill. Night: Silver Order patrols, lamplighters." |
| weather | Typical weather patterns | "Temperate. Frequent rain in autumn. Cold dry winters. Warm summers with river fog." |

## Item Machine Description

| Field | Content | Example |
|-------|---------|---------|
| appearance | Shape, size, color, material | "Gold circlet set with seven gemstones (each a different color), cracked through the center. Weighs about 2 pounds. Roughly 8 inches diameter." |
| condition | State of repair, age markers | "Ancient. The crack runs through two gemstones. Tarnished but not corroded. Eldari glyphs still faintly luminous." |
| distinguishing | What makes it recognizable | "The crack, the seven colored stones, the faint glow of Eldari glyphs" |

## Faction Machine Description

| Field | Content | Example |
|-------|---------|---------|
| visual_identity | Colors, symbols, uniforms, banners | "Deep blue and silver. Winged sword emblem. Members wear blue surcoats with silver thread emblem. Banner: winged sword on blue field." |
| architecture | What their buildings/spaces look like | "Military austere. Clean lines, functional, stone and iron. The Silver Bastion is a fortress within Valdris." |
| atmosphere | What it feels like to be around them | "Disciplined, martial, honor-bound. Formal address. Rank visible on collar insignia." |

## Heraldry / Sigil System

Any entity with visual identity (faction, lineage, location, race, species) should have heraldry block.

### Heraldry Block Structure

```yaml
heraldry:
  sigil:
    description: "Plain language description of the symbol"
    blazon: "Formal heraldic blazon (optional, for realism nerds)"
    shape: "shield, circle, diamond, banner, seal, custom"
  colors:
    primary: "deep blue"
    secondary: "silver"
    accent: "gold"
  motto: "First to face the dawn"
  words: "We endure"
  banner_description: "A deep blue banner bearing a winged silver sword, gold fringe"
```

### Heraldry Sigil Shapes

| Shape | Usage | Characteristics |
|-------|-------|-----------------|
| shield | Medieval/fantasy, faction/lineage | Pointed or flat-bottomed, classic heraldry shape |
| circle | Modern organizations, organizations spanning epochs | Symmetrical, formal |
| diamond | Artistic emphasis, specific cultures | Creates focus point |
| banner | Flags, standards, faction colors | Horizontal/vertical, meant to fly |
| pennant | Military, quick identification | Triangular, sharp |
| seal | Official documents, institutional | Circular, compact |
| roundel | Regional identity, cities | Circular with border |
| lozenge | Historically feminine heraldry | Diamond-rotated shape |

## Entities and Their Description Types

### Must Have Dual Descriptions:
- **Character** (machine: physical, face, clothing, equipment, demeanor, voice, distinguishing)
- **Location** (machine: overview, architecture, atmosphere, landmarks, time_of_day, weather)
- **Item** (machine: appearance, condition, distinguishing)
- **Faction** (machine: visual_identity, architecture, atmosphere + heraldry)
- **Event** (machine, human)
- **Magic System** (machine, human)
- **Arc** (optional, but recommended)

### Should Have Heraldry:
- **Faction** (organization emblem, uniform colors)
- **Lineage** (house/dynasty crest)
- **Location** (city/kingdom flag or seal)
- **Race** (cultural symbols, tribal markings)
- **Species** (racial identifiers if visually distinct)

### Optional for:
- **Species** (cultural symbols if sapient)
- **Lineage** (formal blazon for royal houses)

## Common Machine Description Mistakes

❌ **Don't do:**
- Write prose in machine descriptions ("The warrior stood tall and proud...")
- Include emotional interpretation ("His eyes burned with determination...")
- Use metaphors ("Lightning-quick reflexes...")
- Leave vagueness ("He looked mean" vs "Scar on left cheek, jaw set forward")

✓ **Do:**
- State facts objectively ("6'2", muscular build, scar on left cheek")
- Be specific about colors ("deep blue" not "blue", "dark leather worn at edges" not "worn")
- Include visible context ("Standing in the market square, crowds around him")
- Note condition ("freshly sharpened" vs "rusty", "neat stitching" vs "frayed hem")

## Human Description Examples

Same character, different prose styles:

**Literary:** "Kael stood on the battlements, the scar on his jaw a pale reminder of lessons learned in blood. His surcoat, once the Silver Order's pride, had faded to the color of old bruises."

**Dark:** "The scar twisted Kael's face into a permanent sneer. His surcoat hung in tatters, its winged sword emblem barely visible beneath road dust and bloodstains."

**Young Adult:** "Kael adjusted his Silver Order surcoat—or what was left of it. The scar along his jaw caught the light as he scanned the courtyard below, every muscle tense."

**Cozy:** "Kael looked rather dashing in his battered surcoat, scar and all. He had the air of someone who'd seen far too much, but hadn't let it sour him completely."

All derived from the same machine_description, styled differently.

## When to Use Each Description

| Situation | Use |
|-----------|-----|
| Generating prose or dialogue | `descriptions.machine` |
| Proofreader/editor reviewing text | `descriptions.human` |
| World-building document | `descriptions.machine` |
| Published novel text | `descriptions.human` |
| Character sheet for players | `descriptions.machine` |
| Generating artwork (`world-art`) | `descriptions.image_prompt` (derived from `descriptions.machine` + `style.visual`) |

## Style System Integration

**`descriptions.machine`** → never changes, pure facts

**`descriptions.human`** ← derived using `style.prose` settings:
- `vocabulary.complexity` affects word choice
- `style.prose.preset` affects voice
- `content_rating` affects what can be described
- `sensory_emphasis` determines which senses are featured

**`descriptions.image_prompt`** ← derived using `style.visual` settings (see `skills/world-art/references/style-presets.md`):
- `style.visual.preset` supplies the art direction suffix and default negative prompt
- `style.visual.palette` and `style.visual.lighting` keep colour and mood consistent across entities
- `world_flags` filter out disallowed magic or technology

## Maintenance Tips

- Update machine_description when facts change (character ages, item becomes damaged, faction moves headquarters)
- human_description auto-updates in generation (it's derived)
- For custom hand-written descriptions, ensure they match the source machine_description
- If prose differs from stated facts, machine_description is canonical (prose is wrong)
- Use machine_description as source-of-truth in continuity checks
