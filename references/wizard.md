# World Creation Wizard Reference

Wizard system for generating worlds at 4 t-shirt sizes. Includes YOLO mode and post-generation validation.

## T-Shirt Sizes & Entity Ranges

Sizes control project scope: entity count, history depth, geography complexity.

### Size S — Short Story / One-Shot Campaign

**Use case:** One-shot D&D session, short story, limited scope

| Entity Type | Min | Max |
|-------------|-----|-----|
| species | 1 | 3 |
| races | 1 | 4 |
| languages | 1 | 3 |
| characters | 3 | 8 |
| locations | 2 | 6 |
| factions | 1 | 3 |
| items | 0 | 3 |
| events | 3 | 10 |
| lineages | 0 | 2 |
| arcs | 1 | 2 |
| magic_systems | 0 | 1 |

**Scope:**
- History depth: 50-500 years
- Eras: 1-2
- Geography depth: 3 levels (universe → continent → city)
- Transport modes: 1-3
- Currencies: 1
- Resources: 2-5
- Trade routes: 0-2
- Generation passes: 1 (single pass)

### Size M — Novel / Short Campaign Arc

**Use case:** Single novel, campaign arc, moderate world-building

| Entity Type | Min | Max |
|-------------|-----|-----|
| species | 2 | 5 |
| races | 3 | 10 |
| languages | 2 | 6 |
| characters | 8 | 20 |
| locations | 5 | 15 |
| factions | 2 | 6 |
| items | 2 | 8 |
| events | 10 | 30 |
| lineages | 1 | 4 |
| arcs | 2 | 4 |
| magic_systems | 1 | 2 |

**Scope:**
- History depth: 200-2,000 years
- Eras: 2-3
- Geography depth: 4 levels (universe → continent → region → city)
- Transport modes: 2-5
- Currencies: 1-3
- Resources: 4-10
- Trade routes: 1-5
- Generation passes: 2

### Size L — Book Series / Full Campaign

**Use case:** Multi-book series, full campaign, complex world

| Entity Type | Min | Max |
|-------------|-----|-----|
| species | 4 | 10 |
| races | 6 | 20 |
| languages | 4 | 12 |
| characters | 20 | 50 |
| locations | 12 | 35 |
| factions | 4 | 12 |
| items | 5 | 15 |
| events | 25 | 80 |
| lineages | 3 | 8 |
| arcs | 3 | 8 |
| magic_systems | 1 | 3 |

**Scope:**
- History depth: 1,000-10,000 years
- Eras: 3-5
- Geography depth: 5 levels (universe → continent → region → city → district)
- Transport modes: 3-8
- Currencies: 2-5
- Resources: 8-20
- Trade routes: 3-10
- Generation passes: 3

### Size XL — Epic Universe / Multi-Campaign Sandbox

**Use case:** Epic universe, multiple campaigns, infinite expansion

| Entity Type | Min | Max |
|-------------|-----|-----|
| species | 8 | 20 |
| races | 12 | 40 |
| languages | 8 | 25 |
| characters | 40 | 100 |
| locations | 25 | 80 |
| factions | 8 | 25 |
| items | 10 | 30 |
| events | 50 | 200 |
| lineages | 5 | 15 |
| arcs | 5 | 15 |
| magic_systems | 2 | 5 |

**Scope:**
- History depth: 5,000-50,000 years
- Eras: 4-8
- Geography depth: 7 levels (full hierarchy)
- Transport modes: 4-12
- Currencies: 3-10
- Resources: 12-40
- Trade routes: 5-25
- Generation passes: 5

## Wizard Steps (Interactive Mode)

User is guided through 8 steps in order. Each step collects input that biases generation.

### Step 1: Project Basics

**Required inputs:**

| Field | Type | Options | Default | Impact |
|-------|------|---------|---------|--------|
| title | string | — | — | Project name |
| genre | enum | fantasy, scifi, modern, horror, post-apocalyptic, steampunk, custom | fantasy | Determines aesthetic & rules |
| project_type | enum | novel, series, campaign, game, worldbook | novel | Affects scope emphasis |
| size | enum | S, M, L, XL | M | Entity count & depth |
| tone | enum | literary, pulp, young-adult, dark, gritty, epic, litrpg, cozy, horror, hard-sf, space-opera, noir, fairy-tale | epic | Prose style preset |

### Step 2: Cosmology & Physics

**Optional inputs (can skip):**

| Field | Type | Options | Default | Impact |
|-------|------|---------|---------|--------|
| creation_myth | string | — | (skip) | Flavor text for world origin |
| magic_exists | enum | yes, no, ambiguous | yes | Core world rule |
| calendar_name | string | — | "Common Reckoning" | Timeline/date names |

### Step 3: Geography & Climate

**Required input:**

| Field | Type | Options | Default | Impact |
|-------|------|---------|---------|--------|
| world_name | string | — | — | Primary planet/world name |
| notable_regions | string | comma-separated or "generate" | generate | Creates location hierarchy |
| climate_variety | enum | uniform, moderate-variety, extreme-variety | moderate-variety | Affects terrain/resources |

### Step 4: Species & Peoples

**Inputs:**

| Field | Type | Options | Default | Impact |
|-------|------|---------|---------|--------|
| species_approach | enum | humans-only, few-species, many-species, cosmic-zoo | few-species | Species count & diversity |
| species_hints | string | comma-separated species names or "generate" | generate | Biases species generation |
| interbreeding | enum | yes, no, rare-exceptions | rare-exceptions | Affects race/bloodline complexity |

### Step 5: Power & Factions

**Inputs:**

| Field | Type | Options | Default | Impact |
|-------|------|---------|---------|--------|
| political_structure | enum | monarchy, republic, tribal, theocracy, empire, fragmented, corporate, mixed | mixed | Affects faction types |
| conflict_level | enum | peaceful, simmering, active-conflict, total-war, post-war | simmering | Event severity & frequency |
| faction_hints | string | comma-separated faction names or "generate" | generate | Biases faction generation |

### Step 6: History & Timeline

**Inputs:**

| Field | Type | Options | Default | Impact |
|-------|------|---------|---------|--------|
| history_depth | enum | shallow, moderate, deep, ancient | moderate | Years of history |
| pivotal_events | string | comma-separated events or "generate" | generate | Biases major events |

### Step 7: Central Characters

**Inputs:**

| Field | Type | Options | Default | Impact |
|-------|------|---------|---------|--------|
| protagonist_name | string | character name or "generate" | generate | Main character name |
| protagonist_archetype | enum | reluctant-hero, chosen-one, anti-hero, everyman, scholar, outcast, soldier, trickster, generate | generate | Protagonist personality |
| antagonist_type | enum | dark-lord, political-rival, nature, cosmic-force, self, organization, mystery, generate | generate | Primary conflict source |

### Step 8: Review & Generate

Summary of all choices. User can edit or proceed. Generation begins.

## YOLO Mode

Skips all prompts. Generates world from just:
- **Required:** genre, size
- **Optional:** seed phrase, tone, project_type

**Usage:** `wizard --yolo --genre fantasy --size L --seed "Viking seafarers exploring new continents"`

YOLO defaults:
- genre: fantasy
- size: M
- tone: epic
- project_type: novel
- seed: (empty)

Seed phrase biases generation toward relevant themes/cultures.

## Post-Generation Validation Pipeline

After wizard generates ALL entities, validation editors run automatically.

### Validation Order (Sequential)

| Order | Editor | Purpose | Checks |
|-------|--------|---------|--------|
| 1 | worldrules | Foundation rules | Tech flags, magic limits, physics |
| 2 | geography | Spatial integrity | Terrain, routes, travel times |
| 3 | continuity | Timeline integrity | Dead character active, date contradictions |
| 4 | lore | Internal consistency | Lore contradictions, fact drifts |
| 5 | characterization | Character consistency | Voice drift, motivation gaps |
| 6 | sensitivity | Content review | Stereotypes, harmful tropes, rating compliance |

### Validation Editors (Full Roster)

6 mandatory post-gen editors:
1. **worldrules** — Enforces world flags (no guns in medieval, etc.)
2. **continuity** — Catches timeline errors, contradictions
3. **geography** — Spatial consistency, terrain, routes
4. **characterization** — Character voice, motivation, arcs (called "lore" in some contexts)
5. **lore** — Internal world consistency
6. **sensitivity** — Representation, stereotypes, content rating

### Failure Handling

**Default strategy:** fix-and-retry

| Setting | Value | Meaning |
|---------|-------|---------|
| max_retries | 3 | Try to fix up to 3 times |
| on_failure | "Flag issues for human review" | If 3 retries fail, human must review |

When an editor finds issues:
1. Claude attempts to fix (regenerate affected section)
2. Editor re-validates
3. If still broken, retry again (up to 3 times)
4. If all retries fail, flag for user to manually review

**Example:** Continuity editor finds character appearing after death. Wizard tells Claude to fix it. Claude regenerates that character's last appearance. Continuity re-validates. If successful, continue. If still broken, user must manually decide what's canon.

## Typical Wizard Workflow

```
User runs: claude-code --wizard
    ↓
Wizard: "Welcome! Let's build your world."
    ↓
Step 1-7: Collect inputs (or skip with sensible defaults)
    ↓
Step 8: Show summary
    ↓
User: "Looks good, generate!"
    ↓
Generation Phase:
  - Create entities within size ranges
  - Bias by all user inputs (genre, tone, hints, etc.)
  - Generate species, locations, factions, characters, events...
    ↓
Validation Phase:
  - worldrules editor checks tech/magic compliance
  - geography editor checks spatial consistency
  - continuity editor checks timeline consistency
  - characterization editor checks character voices
  - lore editor checks internal consistency
  - sensitivity editor checks representation
    ↓
If all pass: "World generated successfully!"
If failures: "Fixing [X] issues... Retry 1/3..."
    ↓
Output: Complete world YAML in world/ folder
```

## Quick Size Selection

| Project | Recommended Size | Why |
|---------|------------------|-----|
| D&D one-shot | S | Small, focused cast |
| Novel | M | Rich but manageable |
| Trilogy | L | Complex with room for expansion |
| Game world/sandbox | L-XL | Needs depth for exploration |
| Wiki/universe bible | XL | Infinite expansion potential |
| Short story | S | Minimal entities |
| Campaign arc (3-6 months) | M | Campaign-arc scope |
| Long campaign (1+ year) | L-XL | Needs hidden depth |

## Seed Phrase Examples

Effective seed phrases guide generation toward specific themes:

```
--seed "Viking seafarers exploring new continents"
--seed "Post-apocalyptic where nature reclaimed cities"
--seed "Magical schools competing for students"
--seed "Ancient aliens left technology behind"
--seed "Time-loop society that resets every century"
--seed "Four kingdoms in fragile peace"
--seed "Underwater civilization discovering the surface"
--seed "Planar travelers caught between dimensions"
```

Seed phrases:
- Bias entity generation toward thematic relevance
- Don't lock the world into one concept
- Can be genre-neutral or genre-specific
- Affect character archetypes, faction types, location themes

## Common Wizard Gotchas

❌ **Don't:**
- Pick XL size for a short story (over-scoped)
- Skip genre selection (affects everything)
- Ignore pivotal_events input (major events feel random without input)
- Use YOLO without clear seed phrase (can be too random)

✓ **Do:**
- Start with M if unsure (most flexible)
- Give specific faction/species hints (guides quality)
- Pick a clear conflict_level matching your story tension
- Review the summary before generating
- Let validation editors run fully (fixes consistency)

## Post-Generation Customization

After wizard completes, you can:
- Add/remove entities manually
- Adjust character arcs
- Refine faction relationships
- Add/modify events
- Customize styles (prose, visual, narration)
- Adjust world flags

But don't regenerate (you'll lose hand-made changes). The wizard creates the foundation; you build from there.
