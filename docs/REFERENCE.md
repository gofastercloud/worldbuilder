# WorldBuilder Reference

Exhaustive documentation for all commands, entity schemas, world flags, style presets, editor personas, API endpoints, and configuration options.

## Table of Contents

- [CLI Commands](#cli-commands)
- [Entity Types and Schemas](#entity-types-and-schemas)
- [World Flags](#world-flags)
- [Style System](#style-system)
- [Editor Personas](#editor-personas)
- [Genre Presets](#genre-presets)
- [Wizard Mode](#wizard-mode)
- [Image Generation](#image-generation)
- [Voice Generation](#voice-generation)
- [Economy System](#economy-system)
- [MCP Server Tools](#mcp-server-tools)
- [Web UI API Endpoints](#web-ui-api-endpoints)
- [Project File Structure](#project-file-structure)

---

## CLI Commands

All commands are run via `uv run python scripts/worldbuilder.py <command>`. Every command that operates on a project accepts `--project <path>` (defaults to auto-discovery).

### Project Management

#### `init`

Initialize a new project.

```
init <name> [--genre {fantasy,scifi,modern,campaign,custom}] [--type {novel,series,campaign,game,worldbook}]
```

Creates a project directory under `worlds/<slug>/` with all required subdirectories, schema files, and template stubs. Series projects get an additional `series/` directory; campaign projects get `campaign/sessions/`, `campaign/encounters/`, and `campaign/quests/`.

#### `add`

Add a new entity or chapter.

```
add <entity_type> <name> --project <path>
```

Entity types: `character`, `location`, `faction`, `item`, `magic-system`, `arc`, `event`, `species`, `race`, `language`, `lineage`, `chapter`.

Copies the appropriate template from `assets/templates/` and fills in the name. For chapters, creates a numbered markdown file in `story/chapters/`.

#### `validate`

Check project consistency.

```
validate --project <path> [--no-fix]
```

Runs all validation checks:
- Cross-reference resolution (every slug points to an existing entity)
- Bidirectional relationships (if A references B, B must reference A)
- Timeline consistency (chronological soundness, birth/death dates)
- Parent age rules (parents old enough to have children)
- Faction completeness (leaders, members, goals)
- Image prompt coverage (flags missing `descriptions.image_prompt`)
- World flag compliance (content matches declared flags)
- Species/race hierarchy (races reference valid species)
- Graph analysis (isolated nodes, asymmetric edges, unreachable subgraphs)

#### `fix`

Auto-fix consistency issues.

```
fix --project <path>
```

Attempts to automatically resolve issues found by `validate`.

#### `compile`

Compile manuscript from chapters.

```
compile --project <path> [--format {md,html,all}]
```

Assembles all chapters in order into a single document. Output goes to `output/manuscript.{md,html}`.

#### `stats`

Show project statistics.

```
stats --project <path>
```

Displays entity counts, word counts, cross-reference density, and other project metrics.

### World Exploration

#### `list`

List entities of a type.

```
list <entity_type> --project <path>
```

#### `query`

Search project data.

```
query <question> --project <path>
```

Full-text search across all entity names, metadata, and prose bodies.

#### `timeline`

Display world timeline.

```
timeline --project <path> [--era <era>] [--filter <text>]
```

Chronological listing of all events with dates, types, and significance.

#### `graph`

Generate relationship graph.

```
graph --project <path>
```

Outputs a Mermaid diagram of character relationships.

#### `history`

Show event history for an entity.

```
history <entity_name> --project <path>
```

#### `crossref`

Show cross-references for an entity.

```
crossref <entity_name> --project <path>
```

#### `flags`

Display world flags.

```
flags --project <path>
```

#### `geography`

Display spatial hierarchy and transport routes.

```
geography --project <path>
```

Shows the location tree (universe → galaxy → system → planet → continent → region → city → district → building) and all defined transport routes.

#### `family`

Display family tree.

```
family <name> --project <path>
```

Shows lineage members, succession history, and family relationships for a lineage or character.

#### `languages`

Display language families and intelligibility.

```
languages --project <path>
```

Shows language family trees, speaker counts, script types, and mutual intelligibility scores.

#### `peoples`

Display species and races.

```
peoples --project <path>
```

Shows species with their associated races, traits, and relationships.

#### `economy`

Display economic overview.

```
economy --project <path>
```

Shows currencies, resources, production sites, trade routes, and faction economies.

### Content Generation

#### `generate`

Generate procedural history prompt.

```
generate <gen_type> --years <n> --project <path>
```

Generation types: `peaceful`, `conflict`, `catastrophe`, `mixed`.

Produces a prompt for Claude to generate historically consistent events covering the specified number of years.

#### `write`

Build context-aware writing prompt.

```
write [--chapter <n>] --project <path>
```

Assembles all relevant world context (characters present, active factions, timeline position, world rules, style directives) into a writing prompt for the specified chapter.

#### `story`

Generate an in-universe short story prompt.

```
story --project <path> [--event <slug>] [--era <era>] [--start-year <n>] [--end-year <n>]
      [--protagonist <slug|generate>] [--tone <tone>] [--subgenre <subgenre>]
      [--rating {young-adult,adult,mature}] [--chapters <n>] [--words <n>]
```

Creates a prompt for writing standalone short fiction anchored to a specific event or time period. Includes all world context filtered to the relevant timeframe — which characters are alive, which factions are active, what has happened before and after.

Default: 12 chapters, 30,000 words.

#### `campaign`

Generate a D&D 5e campaign prompt.

```
campaign --project <path> [--event <slug>] [--era <era>] [--year <n>] [--present]
         [--length {one-shot,short,custom}] [--sessions <n>] [--level <range>]
         [--tone <tone>] [--themes <themes>] [--location <slug>]
```

Generates a campaign module prompt with session structure, NPC stat blocks, encounter tables, faction dynamics, rewards, and player handouts — all consistent with the established world.

Default: one-shot, level 1-4, 1 session.

#### `wizard`

World Creation Wizard.

```
wizard <mode> [--size {S,M,L,XL}] [--genre <genre>] [--tone <tone>]
       [--seed <creative_prompt>] [--project-type {novel,series,campaign,game,worldbook}]
       [--project <path>]
```

Modes:
- `yolo` — fully automated, no prompts, generates everything in one pass
- `interactive` — walks through 7 steps: basics, cosmology, geography, peoples, politics, history, protagonist

Genres: `fantasy`, `scifi`, `modern`, `horror`, `post-apocalyptic`, `steampunk`, `custom`.

### Review and Analysis

#### `edit`

Run an editor persona against chapters.

```
edit <editor_name|list> [--chapter <range>] --project <path>
```

Chapter ranges: `1`, `1-3`, `all`. Use `edit list` to see available editors.

See [Editor Personas](#editor-personas) for details on each editor.

#### `readability`

Analyse prose readability.

```
readability --project <path> [--verbose] [--entities] [--chapter <n>]
```

Computes deterministic metrics at paragraph, page (~250 words), chapter, and story level:

| Metric | What It Measures |
|--------|-----------------|
| Flesch-Kincaid Grade Level | US school grade required to understand the text |
| Flesch Reading Ease | 0-100 scale (higher = easier) |
| Gunning Fog Index | Years of formal education needed |
| Coleman-Liau Index | Character-based readability estimate |
| Avg sentence length | Words per sentence |
| Avg word length | Characters per word |

`--verbose` adds paragraph-level detail with outlier flagging (>1.5 standard deviations from mean grade level). `--entities` includes entity body text in the analysis.

---

## Entity Types and Schemas

Every entity is a Markdown file with YAML frontmatter. Entities cross-reference each other by kebab-case slug matching the filename (e.g., `faction: "the-silver-order"` → `world/factions/the-silver-order.md`).

### Character

Required: `name`, `role`, `status`

```yaml
name: ""
aliases: []
role: protagonist | antagonist | supporting | minor | mentioned
status: alive | dead | unknown | transformed | undead | missing
species: ""           # ref:species
race: ""              # ref:races
ethnicity: ""
age: 0
gender: ""
location: ""          # ref:locations
faction: ""           # ref:factions
arc: ""               # ref:arcs

relationships:
  - target: ""        # ref:characters
    type: ally | enemy | family | romantic | mentor | rival | servant | master | friend | unknown
    notes: ""

family_links:
  father: ""          # ref:characters
  mother: ""
  spouse: ""
  children: []
  siblings: []
  lineage: ""         # ref:lineages
  birth_order: 0
  legitimacy: ""
  title_inherited: ""

traits: []
skills: []
inventory: []
secrets: []
tags: []

languages:
  native: ""          # ref:languages
  spoken: []
  literacy: ""

voice:
  description: ""     # free-text voice description (primary input for TTS)
  tags: []            # [male, deep, warm, raspy]
  accent: ""          # falls back to location regional_defaults
  dialect: ""         # falls back to location regional_defaults
  sample_text: ""     # characteristic line of dialogue
  instruct: ""        # manual TTS override (bypasses auto-generation)

descriptions:
  machine:
    physique: ""
    face: ""
    attire: ""
    voice: ""
    demeanor: ""
  human: ""
  image_prompt: ""
```

### Location

Required: `name`, `type`

```yaml
name: ""
aliases: []
type: universe | galaxy | star-system | planet | moon | continent | ocean | sea |
      country | kingdom | empire | region | province | city | town | village |
      district | neighborhood | building | fortress | temple | dungeon | ruins |
      room | wilderness | forest | mountain | mountain-range | river | lake |
      desert | island | cave | valley | station | ship | dimension |
      pocket-realm | portal-nexus | custom
parent: ""            # ref:locations
coordinates:
  x: 0
  y: 0
climate: ""
population: 0
faction: ""           # ref:factions
notable_characters: []

routes:
  - to: ""            # ref:locations
    methods:
      - mode: walking | horse | caravan | sailing-ship | train | starship |
              wormhole | jump-gate | teleportation | portal  # ... 34 modes total
        travel_time: ""
        distance: ""
        cost: ""
        danger_level: ""
        requires: ""
        seasonal: false
        notes: ""
    route_type: major | minor | hidden | seasonal | restricted
    bidirectional: true

transport_hub:
  hub_type: ""
  capacity: ""
  services: []

regional_defaults:
  ethnicity: ""
  appearance:
    skin_tone: ""
    hair: ""
    build: ""
    distinguishing: ""
  voice:
    accent: ""
    dialect: ""
    tags: []

resources: []
dangers: []
tags: []

descriptions:
  machine:
    architecture: ""
    atmosphere: ""
    notable_features: ""
  human: ""
  image_prompt: ""
```

### Faction

Required: `name`, `type`

```yaml
name: ""
aliases: []
type: military | religious | political | criminal | guild | secret-society |
      noble-house | academic | mercantile | custom
status: active | disbanded | underground | dormant
alignment: ""
leader: ""            # ref:characters
leaders: []
headquarters: ""      # ref:locations
territories: []
goals: []
ideology: ""

heraldry:
  sigil: ""
  blazon: ""
  colors: []
  motto: ""
  banner_description: ""
  image_prompt: ""

resources: []
military_strength: ""
influence_level: local | regional | continental | global | cosmic

relationships:
  - faction: ""       # ref:factions
    relationship_type: ally | enemy | rival | vassal | patron | neutral |
                       trade-partner | enemy-of-enemy | competing-for-power | unknown
    notes: ""

members: []
member_count: 0

ranks:
  - name: ""
    description: ""
    responsibilities: ""

founding_date: ""
founding_event: ""
dissolution_date: ""
tags: []

descriptions:
  machine: ""
  human: ""
  image_prompt: ""
```

### Item

Required: `name`, `type`

```yaml
name: ""
aliases: []
type: weapon | armor | artifact | consumable | tool | treasure | document | key-item | custom
rarity: common | uncommon | rare | very-rare | legendary | artifact | unique
owner: ""             # ref:characters
location: ""          # ref:locations
creator: ""
creator_ref: ""       # ref:characters
creation_date: ""
creation_location: "" # ref:locations
creation_method: crafted | forged | grown | summoned | discovered | inherited |
                 cursed | magical | technological | natural | custom

properties:
  magical: false
  magical_effects: []
  mundane_properties: []
  power_source: mana | artifact | charge | life-force | solar | mechanical | unknown
  limitations: []
  cursed: false
  curse_details: ""

significance: trivial | minor | notable | important | crucial | world-changing
significance_reason: ""
material: ""
materials: []
weight: ""
dimensions: ""
condition: pristine | excellent | good | worn | damaged | broken | ruined
history: ""
tags: []

descriptions:
  machine: ""
  human: ""
  image_prompt: ""
```

### Magic System

Required: `name`, `type`

```yaml
name: ""
aliases: []
type: arcane | divine | natural | psionic | technological | cosmic | blood |
      elemental | custom
source: ""
origin_event: ""
rules: ""
can_do: []
cannot_do: []
mechanics: ""

cost:
  type: mana | life-force | memory | sanity | time | materials | ritual |
        currency | favor | sacrifice | custom
  amount: ""
  side_effects: []

limitations: []
learning_difficulty: trivial | easy | moderate | difficult | very-difficult |
                     nearly-impossible
counter_magic: ""
weaknesses: []

practitioners:
  - type: ""
    requirement: ""

famous_practitioners: []

ranks:
  - name: ""
    description: ""
    requirements: ""

forbidden_uses: []
forbidden_consequences: []
ethical_stance: universally-accepted | widely-accepted | controversial |
               restricted | taboo | forbidden | universally-forbidden

interaction_with_tech:
  enhances | interferes | incompatible
  notes: ""

interaction_with_other_magic: ""
cultural_significance: ""
history: ""
tags: []

descriptions:
  machine: ""
  human: ""
  image_prompt: ""
```

### Arc

Required: `name`, `type`

```yaml
name: ""
aliases: []
type: main | subplot | character-arc | faction-arc | world-arc
status: planned | in-progress | completed | abandoned
books: []

chapters:
  start: ""
  end: ""
  start_number: 0
  end_number: 0

characters_involved: []   # ref:characters
factions_involved: []     # ref:factions
locations: []             # ref:locations
themes: []
hook: ""
inciting_incident: ""
climax_summary: ""
resolution_summary: ""
cliffhangers: []
revelation_count: 0

setup_threads:
  - from_arc: ""          # ref:arcs
    thread_description: ""
payoff_threads: []
setup_for_next: ""
pacing_notes: ""

act_structure:
  act_1: ""
  act_2: ""
  act_3: ""

key_scenes: []
emotional_arc: ""
stakes: ""
central_question: ""
tags: []
```

### Event

Required: `name`, `type`

```yaml
name: ""
aliases: []
type: war | battle | birth | death | founding | discovery | plague | cataclysm |
      trade_agreement | coronation | rebellion | treaty | milestone | marriage |
      festival | catastrophe | custom
date: ""              # WorldDate format: era prefix + year (e.g., "2A 450")
date_precision: exact | approximate | approximate-season | approximate-year | unknown
end_date: ""
duration: ""
significance: trivial | minor | notable | important | crucial | world-changing
scope: personal | local | regional | continental | global | cosmic
historical_importance: ""

participants:
  - entity: ""        # ref to any entity type
    role: protagonist | antagonist | ally | witness | victim | beneficiary |
          facilitator | observer | affected | custom
    impact: ""

primary_characters: []
primary_factions: []
locations: []
primary_location: ""
caused_by: ""
root_causes: []
immediate_trigger: ""
leads_to: ""
immediate_consequences: []
long_term_consequences: []
political_impact: ""
economic_impact: ""
social_impact: ""
death_toll: ""

casualties:
  death_count: 0
  injured_count: 0
  missing_count: 0

outcome: decisive | pyrrhic | stalemate | ongoing | ambiguous | reversed | subverted
winner: ""
loser: ""
narrative_significance: ""
turning_point: false
public_knowledge: true

reliability: firsthand | well-documented | rumored | conflicting-accounts |
             legend | false-history
tags: []

descriptions:
  machine: ""
  human: ""
  image_prompt: ""
```

### Species

Required: `name`, `sentience`

```yaml
name: ""
aliases: []
sentience: sapient | semi-sapient | non-sapient | hive-mind | artificial | unknown

biology:
  classification: humanoid | beast | avian | aquatic | amphibian | reptilian |
                  insectoid | arachnid | plant | fungal | elemental | spirit |
                  construct | undead | shapeshifter | amorphous | crystalline | custom
  size: tiny | small | medium | large | huge | gargantuan | colossal
  lifespan: ""
  maturity_age: 0
  reproduction: ""
  diet: ""
  physical_traits: []
  senses: []

habitat:
  native_terrain: ""
  climate_preference: ""
  range: ""
  population_estimate: ""
  population_trend: ""

# Sapient species only:
culture:
  languages: []
  native_language: ""     # ref:languages
  social_structure: ""
  governance: ""
  religion: ""
  technology_level: ""
  magic_affinity: ""

races: []                 # ref:races

relationships:
  - species: ""           # ref:species
    disposition: allied | friendly | neutral | wary | hostile | predatory |
                 prey | symbiotic | parasitic | unknown
    can_interbreed: false
    notes: ""

# Non-sapient species only:
creature:
  danger_level: ""
  domesticable: false
  uses: []
  pack_size: ""
  territorial: false

origin: ""
tags: []
```

### Race

Required: `name`, `species`

```yaml
name: ""
aliases: []
species: ""               # ref:species

variation:
  distinguishing_traits: []
  average_height: ""
  average_build: ""
  lifespan_modifier: ""
  unique_abilities: []

culture:
  homeland: ""            # ref:locations
  current_territories: []
  language: ""            # ref:languages
  additional_languages: []
  social_structure: ""
  values: []
  taboos: []
  traditions: []
  religion: ""
  naming_conventions:
    pattern: ""
    examples: []
    notes: ""

relationships:
  - race: ""              # ref:races
    disposition: ""
    history: ""

faction_affiliations: []  # ref:factions

population:
  estimate: ""
  distribution: ""
  trend: ""

origin: ""
magic_affinity: ""
tags: []
```

### Language

Required: `name`, `status`

```yaml
name: ""
aliases: []
status: living | endangered | dead | extinct | constructed | divine | ancient | proto

family:
  family_name: ""
  branch: ""
  parent_language: ""     # ref:languages
  child_languages: []
  proto_language: ""
  divergence_date: ""

intelligibility:
  - language: ""          # ref:languages
    score: 0.0            # 0.0 to 1.0
    direction: mutual | one-way-to | one-way-from
    notes: ""

script:
  name: ""
  type: alphabet | syllabary | logographic | abjad | abugida | runic |
        pictographic | telepathic | magical | none
  direction: ltr | rtl | ttb | boustrophedon | circular | custom
  shared_with: []
  literacy_rate: ""

speakers:
  native_species: []
  native_races: []
  as_second_language: []
  total_speakers: ""
  geographic_range: ""

characteristics:
  phonology: ""
  grammar_notes: ""
  registers: []
  loanwords_from: []
  loanwords_to: []

special:
  is_lingua_franca: false
  is_sacred: false
  magical_properties: ""
  can_be_spoken_by: []
  nonverbal_component: ""

origin: ""
tags: []
```

### Lineage

Required: `name`

```yaml
name: ""
aliases: []
type: royal | noble | common | divine | magical | clan | corporate | custom
species: ""               # ref:species
race: ""                  # ref:races
seat: ""                  # ref:locations
faction: ""               # ref:factions

heraldry:
  sigil: ""
  colors: []
  motto: ""
  words: ""

bloodline:
  inherited_traits: []
  inherited_powers: []
  genetic_weaknesses: []
  blood_purity: irrelevant | tracked | important | critical

founder: ""               # ref:characters
current_head: ""          # ref:characters
members: []

succession:
  rule: primogeniture | male-primogeniture | ultimogeniture | elective |
        meritocratic | combat | divine-selection | custom
  title: ""
  history:
    - ruler: ""           # ref:characters
      reign_start: ""
      reign_end: ""
      how_ended: death | abdication | deposition | conquest | disappearance | custom

status: active | declining | extinct | exiled | hidden | ascendant | scattered
founded: ""               # WorldDate
ended: ""

allied_lineages: []       # ref:lineages
rival_lineages: []
marriage_alliances:
  - member: ""            # ref:characters
    married_into: ""      # ref:lineages
    date: ""
    political: false

tags: []
```

---

## World Flags

World flags are boolean or categorical constraints declared in `project.yaml` under `world_flags`. The validator checks all entity content against these flags.

### Reality

| Flag | Values | Description |
|------|--------|-------------|
| `basis` | primary, secondary, alternate, far-future | Relationship to our world |
| `time_period` | (string) | General era |
| `internal_consistency` | hard, soft, mythic | How strictly rules are enforced |
| `tone` | (list) | e.g., [epic, dark, gritty] |

### Physics

| Flag | Values | Description |
|------|--------|-------------|
| `earth_like` | bool | Earth-like physics |
| `cosmology` | natural, mythic, artificial, unknown | How the universe works |
| `astronomy` | (string) | Celestial setup |
| `seasons` | earth-like, irregular, magical, none, custom | Seasonal patterns |

### Magic

| Flag | Values | Description |
|------|--------|-------------|
| `present` | bool | Magic exists |
| `prevalence` | none, rare, uncommon, common, ubiquitous, fading, growing | How widespread |
| `hardness` | soft, medium, hard, scientific | Rule rigidity |
| `source` | (string) | Where magic comes from |
| `cost` | (string) | What magic costs |
| `heritability` | (string) | Can it be inherited |
| `public_knowledge` | bool | Is magic known publicly |
| `divine_intervention` | active, passive, none, ambiguous, dead-gods | Gods' involvement |

### Technology

| Flag | Values | Description |
|------|--------|-------------|
| `level` | stone-age → post-singularity, mixed | Overall tech level |
| `gunpowder` | bool | Gunpowder exists |
| `printing` | bool | Printing press exists |
| `electricity` | bool | Electrical technology |
| `steam_power` | bool | Steam engines |
| `internal_combustion` | bool | Combustion engines |
| `computing` | bool | Computers exist |
| `spaceflight` | bool | Space travel |
| `ftl` | bool (+ subtype) | Faster-than-light travel |
| `ai` | bool | Artificial intelligence |
| `biotech` | bool | Biotechnology |
| `magitech` | bool | Magic-technology fusion |
| `metallurgy` | stone → exotic | Metalworking level |
| `medicine` | folk → magical | Medical capability |
| `communication` | oral → magical | Communication technology |
| `transportation` | foot → teleportation | Transport technology |

### Society

| Flag | Values | Description |
|------|--------|-------------|
| `governance` | (list) | Government types |
| `economic_system` | (string) | Economic model |
| `slavery` | (string) | Slavery status |
| `gender_roles` | (string) | Gender dynamics |
| `literacy` | (string) | Literacy level |
| `urbanization` | (string) | Urban vs rural |
| `religion` | (string) | Religious landscape |

### Peoples

| Flag | Values | Description |
|------|--------|-------------|
| `species_diversity` | (string) | How many species |
| `species_relations` | (string) | Inter-species dynamics |
| `cross_species_breeding` | bool (locked) | Cross-species reproduction |
| `cultural_inspiration` | (list) | Real-world cultural analogues |

### Geography

| Flag | Values | Description |
|------|--------|-------------|
| `world_shape` | globe, flat, disc, ring, cylinder, pocket-dimension, infinite, unknown | World geometry |
| `world_size` | (string) | Scale |
| `known_world` | (string) | How much is explored |
| `biomes` | (list) | Available biomes |

### Narrative

| Flag | Values | Description |
|------|--------|-------------|
| `death_permanence` | always, mostly, sometimes, revolving-door | Can the dead return |
| `power_ceiling` | (string) | Maximum power level |
| `realism` | gritty, heroic, mythic, comedic | Tone of reality |
| `content_rating` | (string) | Content rating |
| `violence_level` | (string) | Violence intensity |
| `language_style` | (string) | Profanity level |
| `anachronisms` | strict, loose, intentional, irrelevant | Historical accuracy |

---

## Style System

Styles are configured at project level in `project.yaml` and can be overridden per book or chapter.

### Visual Styles (13 presets)

`realistic`, `painterly`, `anime`, `manga`, `comic-book`, `pixel-art`, `art-nouveau`, `dark-fantasy`, `sci-fi-concept`, `cyberpunk`, `watercolor`, `woodcut`, `stained-glass`, `custom`

#### Visual Modifiers

| Modifier | Options |
|----------|---------|
| `lighting` | natural, dramatic, cinematic, soft, harsh, neon, candlelit, moonlit, golden-hour, overcast, custom |
| `color_palette` | vibrant, muted, monochrome, warm, cool, earth-tones, jewel-tones, pastel, desaturated, high-contrast, custom |
| `camera` | eye-level, low-angle, high-angle, birds-eye, dutch-angle, close-up, medium-shot, wide-shot, portrait, cinematic-wide, custom |
| `mood` | epic, intimate, ominous, hopeful, melancholy, tense, serene, chaotic, mysterious, triumphant, custom |
| `detail_level` | minimal, moderate, detailed, hyper-detailed |

### Prose Styles (14 presets)

`literary`, `pulp`, `young-adult`, `dark`, `gritty`, `epic`, `litrpg`, `cozy`, `horror`, `hard-sf`, `space-opera`, `noir`, `fairy-tale`, `custom`

#### Prose Voice

| Control | Options |
|---------|---------|
| `pov` | first-person, second-person, third-limited, third-omniscient, third-deep, rotating-pov, unreliable |
| `tense` | past, present, future |
| `formality` | colloquial, casual, neutral, formal, archaic, mixed |

#### Prose Vocabulary

| Control | Options |
|---------|---------|
| `complexity` | simple, moderate, rich, ornate |
| `anachronism_tolerance` | strict, moderate, loose |
| `profanity` | none, mild, moderate, heavy, invented-only |

#### Prose Pacing

| Control | Options |
|---------|---------|
| `default_tempo` | breakneck, fast, moderate, deliberate, slow, variable |
| `scene_length` | short (~500w), medium (~1500w), long (~3000w), variable |
| `chapter_length` | (string, default "3000-5000 words") |

#### Content Rating

`all-ages`, `middle-grade`, `young-adult`, `adult`, `mature`

#### Description Modifiers

| Control | Options |
|---------|---------|
| `sensory_emphasis` | list, default: [sight, sound, smell] |
| `metaphor_density` | sparse, moderate, rich |
| `internal_monologue` | minimal, moderate, deep |

---

## Editor Personas

Nine specialized review personas, each with specific checks and a distinct editorial voice. Run via `edit <name> --chapter <range>`.

### character — The Psychologist

Checks: out-of-character behaviour, voice drift, arc stall, forgotten traits, unearned change, relationship drift, motivation gaps, knowledge violations.

### continuity — The Archivist

Checks: dead characters acting, timeline contradictions, location contradictions, fact drift, age inconsistencies, relationship contradictions, missing events, season/weather mismatches.

### dialogue — The Linguist

Checks: voice sameness between characters, period-inappropriate language, talking heads (dialogue without action), voice breaks, info-dump dialogue, missing dialect markers.

### geography — The Cartographer

Checks: impossible travel times, transport anachronisms, undefined routes, direction contradictions, location description drift, terrain impossibilities, geology contradictions, missing journeys, climate inconsistencies, scale violations, hierarchy gaps, unreachable locations. Includes terrain adjacency rules.

### pacing — The Conductor

Checks: chapter length imbalance, tension plateaus, arc stalls, missing breather scenes, premature climax, saggy middle, unresolved setups.

### plot — The Detective

Checks: plot holes, unresolved threads, Chekhov's gun violations, deus ex machina, idiot ball, coincidence overuse, broken causality, power inconsistencies.

### prose — The Wordsmith

Checks: purple prose, weak verbs, adverb excess, repetition, telling instead of showing, passive voice, filter words, sentence monotony.

### sensitivity — The Guardian

Checks: stereotypes, harmful tropes, representation gaps, power dynamics, content rating violations.

### worldrules — The Lawkeeper

Checks: technology anachronisms, magic rule violations, magic cost skipping, physics violations, social anachronisms, flag contradictions. Includes keyword lists per technology flag for automated detection.

---

## Genre Presets

Presets configure world flags, entity options, and style defaults. Set via `--genre` on `init` or `wizard`.

### Fantasy

- Tech level: medieval
- Currency: gold/silver/copper
- Species: human, elf, dwarf, halfling, orc, gnome, dragonborn, tiefling
- Magic types: arcane, divine, elemental, nature, blood, rune, psionic
- Factions: kingdom, guild, religion, military-order, criminal-syndicate, mage-circle, tribal-confederation, merchant-league
- Themes: good-vs-evil, power-corrupts, chosen-one, quest, coming-of-age, war, prophecy, lost-magic, ancient-evil

### Sci-Fi

- Tech level: spacefaring
- Currency: credits
- Species: human, android, cyborg, alien, uplifted-animal, digital-consciousness, clone
- Tech types: ftl-drive, energy-weapons, shields, ai-systems, biotech, nanotech, cybernetics, terraforming, cryogenics, quantum-tech
- FTL options: hyperspace, wormholes, warp-drive, jump-gates, alcubierre, none
- Themes: humanity-vs-technology, first-contact, dystopia, utopia-gone-wrong, ai-consciousness, colonialism, survival, identity, corporate-greed, transhumanism

### Campaign

Extends the base preset with D&D-specific fields:
- Character extensions: level, class, subclass, hp, ac, D&D stats, proficiencies, spells, background, alignment
- Session template: session number, players, summary, key events, loot, XP, cliffhanger, DM notes
- Encounter template: type (combat/social/puzzle/exploration/trap), difficulty (easy-deadly), enemies, rewards
- Quest template: giver, type (main/side/personal/faction), status, objectives, rewards, consequences

---

## Wizard Mode

### Entity Counts by Size

| Entity | S | M | L | XL |
|--------|---|---|---|-----|
| Species | 1-3 | 2-5 | 4-10 | 8-20 |
| Races | 1-4 | 3-10 | 6-20 | 12-40 |
| Languages | 1-3 | 2-6 | 4-12 | 8-25 |
| Characters | 3-8 | 8-20 | 20-50 | 40-100 |
| Locations | 2-6 | 5-15 | 12-35 | 25-80 |
| Factions | 1-3 | 2-6 | 4-12 | 8-25 |
| Items | 0-3 | 2-8 | 5-15 | 10-30 |
| Events | 3-10 | 10-30 | 25-80 | 50-200 |
| Lineages | 0-2 | 1-4 | 3-8 | 5-15 |
| Arcs | 1-2 | 2-4 | 3-8 | 5-15 |
| Magic systems | 0-1 | 1-2 | 1-3 | 2-5 |

### History Depth

| Size | Eras | Timespan | Generation passes |
|------|------|----------|-------------------|
| S | 1-2 | 50-500 years | 1 |
| M | 2-3 | 200-2,000 years | 2 |
| L | 3-5 | 1,000-10,000 years | 3 |
| XL | 4-8 | 5,000-50,000 years | 5 |

### Economy Scale

| Size | Currencies | Resources | Trade routes |
|------|-----------|-----------|-------------|
| S | 1 | 2-5 | 0-2 |
| M | 1-3 | 4-10 | 1-5 |
| L | 2-5 | 8-20 | 3-10 |
| XL | 3-10 | 12-40 | 5-25 |

### Geography Depth

| Size | Max depth | Transport modes |
|------|-----------|----------------|
| S | 3 | 1-3 |
| M | 4 | 2-5 |
| L | 5 | 3-8 |
| XL | 7 | 4-12 |

### Interactive Mode Steps

1. **Basics** — title, genre, project type, size, tone
2. **Cosmology** — creation myth, magic exists, calendar name
3. **Geography** — world name, notable regions, climate variety
4. **Peoples** — species approach, species hints, interbreeding
5. **Politics** — political structure, conflict level, faction hints
6. **History** — history depth, pivotal events
7. **Protagonist** — name, archetype, antagonist type
8. **Review** — summary, then generation

### Post-Generation Validation

Wizard runs editors in sequence after generation: worldrules → geography → continuity → lore → characterization → sensitivity. Fix-and-retry with max 3 retries per pass.

---

## Image Generation

Apple Silicon only (MLX). Install: `uv sync --extra imagegen`.

### Configuration

| Setting | Default | Location |
|---------|---------|----------|
| Model | `filipstrand/Z-Image-Turbo-mflux-4bit` | `webapp/imagegen.py` |
| Steps | 9 | `DEFAULT_STEPS` |
| Width | 768 | `DEFAULT_WIDTH` |
| Height | 768 | `DEFAULT_HEIGHT` |
| Negative prompt | "watermark, text, signature, border, logo, blurry, low quality, distorted, deformed, ugly" | hardcoded |

### Style Presets

| Key | LoRA | Scale | Prompt prefix | Prompt suffix |
|-----|------|-------|---------------|---------------|
| `default` | (none) | — | (none) | "high quality, detailed" |
| `photorealistic` | `suayptalha/Z-Image-Turbo-Realism-LoRA` | 0.8 | (none) | "cinematic lighting, sharp focus, high detail" |
| `anime` | `Haruka041/z-image-anime-lora` | 0.85 | "anime style, " | "vibrant colors, clean linework, cel-shaded" |
| `cartoon` | `AiAF/D-ART_Z-Image-Turbo_LoRA` | 0.8 | "digital art illustration, " | "stylized, vivid colors, expressive" |

### Prompt Enrichment

The `enrich_prompt()` function assembles the final prompt from:

1. Style prefix (from LoRA preset)
2. Entity `image_prompt` (subject description — physical details, composition, pose, setting, mood)
3. Visual details extracted from `descriptions.machine` (up to 4 relevant sentences, max 300 chars)
4. Genre context hint from `project.yaml` (e.g., "fantasy setting", "sci-fi setting, futuristic")
5. Style suffix (from LoRA preset)

Entity `image_prompt` fields should describe the **subject only**. Do not include style instructions or negative prompts — those are applied automatically.

### Caching

Generated images are saved as `<entity_slug>_<sha256_16chars>.png` in `<project>/output/images/`. Regeneration requires `force: true`.

### Job System

Single background worker thread. Jobs: queued → running → complete/failed. Poll via `/api/imagegen/job/<job_id>`.

---

## Voice Generation

Apple Silicon only (MLX). Install: `uv sync --extra voicegen`.

### Configuration

| Setting | Default | Location |
|---------|---------|----------|
| Model | `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16` | `webapp/voicegen.py` |
| Output format | MP3 at 24kHz | hardcoded |

### Voice Instruct Assembly

The TTS `instruct` parameter is built automatically from character data:

1. If `voice.instruct` is set → use it verbatim (manual override)
2. Otherwise, auto-assemble from:
   - Gender from `character.gender` (mapped to male/female)
   - Age from `character.age` (mapped to: young/teenage, young adult, middle-aged, mature, elderly)
   - `voice.description` (richest input — be vivid and specific)
   - `voice.tags` (as "Voice qualities: tag1, tag2")
   - Accent: `voice.accent` → falls back to location `regional_defaults.voice.accent`
   - Dialect: `voice.dialect` → falls back to location `regional_defaults.voice.dialect`
3. Fallback: "A neutral, clear speaking voice."

Location resolution walks up the parent chain until `regional_defaults` is found.

### Caching

Voice samples saved as `<entity_slug>_<sha256_16chars>.mp3` in `<project>/output/voices/`.

---

## Economy System

Defined in `world/economy.yaml` within each project.

### Resources

```yaml
resources:
  - name: ""
    category: raw-material | food | luxury | strategic | magical | knowledge |
              labor | currency | fuel | custom
    rarity: ""
    base_value: ""
    unit: ""
    perishable: false
    requires_tech: ""
    tags: []
```

### Production

```yaml
production:
  - resource: ""          # ref:resources
    location: ""          # ref:locations
    output: ""
    quality: poor | fair | good | excellent | legendary
    labor_source: ""
    status: active | disrupted | destroyed | depleted | seasonal | new
    disrupted_by: []      # ref:events
```

### Trade Routes

```yaml
trade_routes:
  - name: ""
    from_location: ""     # ref:locations
    to_location: ""       # ref:locations
    transport_route: ""
    goods:
      - resource: ""
        direction: ""
        volume: ""
    annual_value: ""
    controlled_by: ""     # ref:factions
    tariff: ""
    status: active | disrupted | closed | seasonal | new
    risks: []
```

### Currencies

```yaml
currencies:
  - name: ""
    symbol: ""
    denominations:
      - name: ""
        value: 0
        material: ""
    issuing_authority: "" # ref:factions
    accepted_in: []       # ref:locations
    exchange_rates: {}
```

### Faction Economies

```yaml
faction_economies:
  - faction: ""           # ref:factions
    wealth_level: destitute | poor | modest | comfortable | wealthy | rich |
                  very-rich | extravagant | incalculable
    income_sources: []
    expenses: []
    treasury: ""
    debts: []
    economic_strategy: ""
```

---

## MCP Server Tools

The MCP server (`mcp_server/worldbuilder_mcp.py`) exposes WorldBuilder as tools for Claude Code via stdio transport.

| Tool | Parameters | Description |
|------|-----------|-------------|
| `wb_list_projects` | — | List all projects |
| `wb_project_overview` | `project` | Full project overview |
| `wb_init_project` | `name`, `genre`, `project_type` | Initialize new project |
| `wb_add_entity` | `entity_type`, `name`, `project`, `fields` | Add entity |
| `wb_get_entity` | `entity_type`, `slug`, `project` | Get entity detail |
| `wb_list_entities` | `entity_type`, `query`, `project` | List/search entities |
| `wb_search` | `query`, `project` | Full-text search |
| `wb_timeline` | `project` | Event timeline |
| `wb_geography` | `project` | Location hierarchy |
| `wb_families` | `project` | Lineages and dynasties |
| `wb_languages` | `project` | Language families |
| `wb_species` | `project` | Species and races |
| `wb_economy` | `project` | Economic overview |
| `wb_world_flags` | `project` | World flags |
| `wb_validate` | `project` | Run validation |
| `wb_wizard` | `mode`, `size`, `genre`, `seed`, `tone`, `project_type` | World creation wizard |
| `wb_generate_history` | `gen_type`, `years`, `project` | Procedural history |
| `wb_write_chapter` | `chapter`, `project` | Writing prompt |
| `wb_edit_review` | `editor`, `project` | Editor review |
| `wb_generate_image` | `entity_type`, `slug`, `project`, `force` | Generate entity image |

---

## Web UI API Endpoints

The Flask web UI (`webapp/app.py`) serves a single-page app at `/` and exposes a REST API.

### Project and Entity APIs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List all projects |
| GET | `/api/project/<slug>` | Project config and entity counts |
| GET | `/api/project/<slug>/entities/<etype>` | List entities (supports `?q=` search) |
| GET | `/api/project/<slug>/entity/<etype>/<entity_slug>` | Get entity detail |
| GET | `/api/project/<slug>/search` | Full-text search (`?q=`) |

### World Data APIs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/project/<slug>/timeline` | Chronological events |
| GET | `/api/project/<slug>/geography` | Location hierarchy and routes |
| GET | `/api/project/<slug>/families` | Lineages with members |
| GET | `/api/project/<slug>/relationships` | Character relationship graph |
| GET | `/api/project/<slug>/languages` | Language families and intelligibility |
| GET | `/api/project/<slug>/species` | Species and races |
| GET | `/api/project/<slug>/economy` | Economy data |
| GET | `/api/project/<slug>/flags` | World flags |

### Image Generation APIs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/imagegen/status` | Backend availability |
| GET | `/api/imagegen/styles` | Available style presets |
| POST | `/api/project/<slug>/entity/<etype>/<entity_slug>/image` | Submit image job |
| POST | `/api/imagegen/playground` | Free-form image generation |
| GET | `/api/imagegen/job/<job_id>` | Poll job status |
| GET | `/api/imagegen/preview/<job_id>` | Step preview image |
| GET | `/api/imagegen/jobs` | List all jobs (`?project=` filter) |
| GET | `/api/imagegen/completions` | Jobs completed since `?since=` |
| GET | `/api/project/<slug>/entity/<etype>/<entity_slug>/image/check` | Check cached image |
| GET | `/api/project/<slug>/images/<filename>` | Serve generated image |
| GET | `/api/imagegen/playground/images/<filename>` | Serve playground image |

### Voice Generation APIs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/voicegen/status` | Backend availability |
| POST | `/api/project/<slug>/entity/<etype>/<entity_slug>/voice` | Submit voice job |
| GET | `/api/voicegen/job/<job_id>` | Poll voice job status |
| GET | `/api/project/<slug>/entity/<etype>/<entity_slug>/voice/check` | Check cached voice |
| POST | `/api/project/<slug>/voices/generate-all` | Batch generate all voices |
| GET | `/api/project/<slug>/voices/<filename>` | Serve voice sample |

### Wizard API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/wizard/sizes` | T-shirt size descriptions |

---

## Project File Structure

Created by `init`, populated by `wizard` or manual `add` commands.

```
worlds/<slug>/
├── project.yaml                    # Project config, world flags, style settings
├── world/
│   ├── overview.md                 # World overview prose
│   ├── rules.md                    # World rules summary
│   ├── economy.yaml                # Currencies, resources, trade, faction economies
│   ├── characters/
│   │   ├── _schema.yaml            # Field definitions
│   │   └── <slug>.md               # One per character
│   ├── locations/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── factions/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── items/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── magic-systems/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── events/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── species/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── races/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── languages/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   ├── lineages/
│   │   ├── _schema.yaml
│   │   └── <slug>.md
│   └── history/
│       └── calendar.yaml           # Eras and calendar system
├── story/
│   ├── outline.yaml                # Three-act structure
│   ├── arcs/                       # Story arc definitions
│   ├── chapters/                   # Chapter markdown files
│   └── notes/                      # Freeform notes
├── stories/                        # In-universe short stories
│   └── <story-slug>/
│       └── chapter-NN.md
├── output/                         # Generated content (gitignored in user projects)
│   ├── manuscript.md               # Compiled manuscript
│   ├── manuscript.html
│   ├── images/                     # Generated entity illustrations
│   ├── voices/                     # Generated voice samples
│   ├── stories/                    # Story prompt output
│   ├── campaigns/                  # Campaign module output
│   ├── reviews/                    # Editor review output
│   └── writing/                    # Writing prompt output
├── series/                         # (series projects only)
│   └── series.yaml
└── campaign/                       # (campaign projects only)
    ├── sessions/
    ├── encounters/
    └── quests/
```
