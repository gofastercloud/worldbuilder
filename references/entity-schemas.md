# Entity Schemas Reference

Quick-lookup guide for all 11 entity types in WorldBuilder. Each schema defines required fields, enums, and relationships.

## Character Schema

**Required:** name, role, status

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Character's full name |
| role | enum | protagonist, antagonist, supporting, minor, mentioned | Narrative role |
| status | enum | alive, dead, unknown, transformed, undead, missing | Current story status |
| species | string | — | Race/species (default: human) |
| age | string | — | Age or age range |
| gender | string | — | Gender identity |
| first_appearance | string | — | Chapter/session where introduced |
| last_appearance | string | — | Where character exits story |
| location | ref | → locations | Current location |
| faction | ref | → factions | Primary faction allegiance |
| relationships | list | ally, enemy, family, romantic, mentor, rival, servant, master, friend | Character connections |
| arc | ref | → arcs | Character arc reference |
| traits | list | — | Personality traits and quirks |
| skills | list | — | Abilities and training |
| inventory | list | — | Carried items (game projects) |
| stats | dict | — | RPG stats (flexible key-value) |
| secrets | list | — | Hidden knowledge (spoiler-tagged in output) |
| ethnicity | string | — | Cultural/ethnic background |
| descriptions | object | machine, human, image_prompt | Triple-description system |
| voice | object | description, tags, accent, dialect, sample_text, instruct | TTS voice generation config |

**Voice Fields (Qwen3-TTS VoiceDesign):**
- `description` (string) — free-text voice description (primary TTS input — be vivid and specific)
- `tags` (list) — voice quality tags (e.g. male, female, deep, warm, raspy, young)
- `accent` (string) — accent for TTS (e.g. "Scottish", "Welsh", "Brooklyn"). Falls back to location regional_defaults
- `dialect` (string) — speech register (e.g. "formal court speech", "rural colloquial"). Falls back to location regional_defaults
- `sample_text` (string) — a characteristic line of dialogue used to generate the voice sample
- `instruct` (string) — optional manual TTS instruct override (bypasses auto-generation from other fields)

## Location Schema

**Required:** name, type

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Location name |
| type | enum | See below | Scale from universe to room |
| parent | ref | → locations | Spatial hierarchy parent |
| coordinates | object | x, y, lat, lon | Position on parent map |
| climate | string | — | Weather/temperature pattern |
| population | string | — | Inhabitants description |
| faction | ref | → factions | Controlling faction |
| notable_characters | list | → characters | Key inhabitants |
| routes | list | See transport section | Multi-modal travel connections |
| transport_hub | object | hub_type, capacity, services | If location is a hub |
| resources | list | — | Available materials |
| dangers | list | — | Hazards or threats |
| descriptions | object | machine, human, image_prompt | Visual descriptions |
| regional_defaults | object | ethnicity, appearance, voice | Inherited traits for inhabitants (see below) |

**Regional Defaults (for cities, towns, regions, kingdoms):**
Characters from a location inherit these traits unless they override them at the character level.
- `ethnicity` (string) — default cultural/ethnic background
- `appearance.skin_tone` (string) — e.g. "fair", "olive", "dark brown"
- `appearance.hair` (string) — e.g. "red, often curly"
- `appearance.build` (string) — e.g. "stocky", "tall and lean"
- `appearance.distinguishing` (string) — e.g. "freckles common", "ritual scarification"
- `voice.accent` (string) — regional accent for TTS (e.g. "Scottish", "Welsh")
- `voice.dialect` (string) — speech register (e.g. "formal", "archaic")
- `voice.tags` (list) — default voice quality tags

The inheritance chain walks up the location parent hierarchy until regional_defaults is found.

**Location Type Hierarchy:**
- Cosmic: universe, galaxy, star-system, planet, moon
- Continental: continent, ocean, sea
- National: country, kingdom, empire, region, province
- Local: city, town, village, district, neighborhood
- Structure: building, fortress, temple, dungeon, ruins, room
- Natural: wilderness, forest, mountain, mountain-range, river, lake, desert, island, cave, valley
- Special: station, ship, dimension, pocket-realm, portal-nexus, custom

**Transport Routes (per location):**
- destination (ref → locations)
- methods (list: mode, travel_time, distance, cost, danger_level, requires, seasonal, notes)
- route_type (major, minor, hidden, seasonal, restricted)
- bidirectional (boolean)

**Transport Modes:** walking, horse, caravan, beast-of-burden, rowboat, sailing-ship, steamship, submarine, train, maglev, cart, coach, car, truck, airship, airplane, dragon, flying-mount, helicopter, teleportation, portal, ley-line, spirit-walk, shuttle, starship, wormhole, jump-gate, hyperspace, custom

## Faction Schema

**Required:** name, type

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Faction name |
| type | enum | military, religious, political, criminal, guild, secret-society, noble-house, academic, mercantile, custom | Organization type |
| status | enum | active, disbanded, underground, dormant | Operational status |
| alignment | string | — | Moral/ideological orientation |
| leader | ref | → characters | Primary figurehead |
| leaders | list | → characters | Multiple leaders/council |
| headquarters | ref | → locations | Primary base of operations |
| territories | list | → locations | Controlled/claimed locations |
| goals | list | — | Primary objectives |
| ideology | string | — | Core beliefs |
| heraldry | object | sigil, blazon, colors, motto, banner_description, image_prompt | Visual identity |
| resources | list | — | Assets and materials |
| military_strength | string | — | Military force size/capability |
| influence_level | enum | local, regional, continental, global, cosmic | Scope of influence |
| relationships | list | faction, relationship_type, notes | Ally/enemy/rival status |
| members | list | → characters | Known members |
| member_count | string | — | Total membership estimate |
| ranks | list | name, description, responsibilities | Organizational hierarchy |
| founding_date | string | — | When faction founded (WorldDate) |
| founding_event | string | — | Story of foundation |
| dissolution_date | string | — | When disbanded (if applicable) |
| descriptions | object | machine, human, image_prompt | Organization descriptions |

**Faction Relationship Types:** ally, enemy, rival, vassal, patron, neutral, trade-partner, enemy-of-enemy, competing-for-power, unknown

**Influence Levels:** local (town/city), regional (province/kingdom), continental (multiple nations), global (entire world), cosmic (across worlds/dimensions)

## Item Schema

**Required:** name, type

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Item name |
| type | enum | weapon, armor, artifact, consumable, tool, treasure, document, key-item, custom | Item category |
| rarity | enum | common, uncommon, rare, very-rare, legendary, artifact, unique | Rarity for games |
| owner | ref | → characters | Current owner |
| location | ref | → locations | Current location if unowned |
| previous_owners | list | → characters | Historical owners |
| creator | string | — | Who made it |
| creator_ref | ref | → characters | Creator as character (if applicable) |
| creation_date | string | — | When created (WorldDate) |
| creation_location | ref | → locations | Where made |
| creation_method | enum | crafted, forged, grown, summoned, discovered, inherited, cursed, magical, technological, natural, custom | How it came to exist |
| properties | object | magical, magical_effects, mundane_properties, power_source, limitations, cursed, curse_details | Mechanical properties |
| significance | enum | trivial, minor, notable, important, crucial, world-changing | Narrative importance |
| significance_reason | string | — | Why it matters |
| material | string | — | Primary material |
| materials | list | — | All components |
| weight | string | — | Item weight |
| dimensions | string | — | Size/dimensions |
| condition | enum | pristine, excellent, good, worn, damaged, broken, ruined | State of repair |
| stats | dict | — | RPG stats (AC, damage, bonuses) |
| history | string | — | Background and significant events |
| first_appearance | string | — | Chapter/session introduced |
| major_events | list | — | Key moments involving item |
| descriptions | object | machine, human, image_prompt | Item descriptions |

**Power Sources:** mana, artifact, charge, life-force, solar, mechanical, unknown

## Magic System Schema

**Required:** name, type

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Magic system name |
| type | enum | arcane, divine, natural, psionic, technological, cosmic, blood, elemental, custom | Magic classification |
| source | string | — | Where magic comes from (ley-lines, gods, nature, etc.) |
| origin_event | string | — | How this system came to exist |
| rules | list | — | What magic can/cannot do |
| can_do | list | — | Specific abilities |
| cannot_do | list | — | Hard limitations |
| mechanics | string | — | How spells/effects are cast |
| cost | object | type, amount, side_effects | Resource cost to use |
| limitations | list | — | Usage restrictions |
| learning_difficulty | enum | trivial, easy, moderate, difficult, very-difficult, nearly-impossible | How hard to learn |
| counter_magic | string | — | Methods to counter it |
| weaknesses | list | — | What weakens this magic |
| practitioners | list | type, requirement | Who can use it |
| famous_practitioners | list | → characters | Known masters |
| ranks | list | name, description, requirements | Power levels/mastery tiers |
| forbidden_uses | list | — | Things that cannot be done |
| forbidden_consequences | string | — | What happens if broken |
| ethical_stance | enum | universally-accepted, widely-accepted, neutral, controversial, widely-forbidden, universally-forbidden | Social acceptability |
| interaction_with_tech | object | enhances, interferes, incompatible, notes | Tech interactions |
| interaction_with_other_magic | string | — | Interaction with other systems |
| cultural_significance | string | — | How it affects society |
| first_documented_use | string | — | When/where first discovered |
| history | string | — | Evolution over time |
| descriptions | object | machine, human, image_prompt | Magic descriptions |

**Cost Types:** mana, life-force, memory, sanity, time, materials, ritual, currency, favor, sacrifice, custom

## Arc Schema

**Required:** name, type

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Arc name/title |
| type | enum | main, subplot, character-arc, faction-arc, world-arc | Type of narrative arc |
| status | enum | planned, in-progress, completed, abandoned | Progress status |
| books | list | → books | Which volumes it spans |
| chapters | object | start, end, start_number, end_number | Chapter range |
| characters_involved | list | → characters | Central characters |
| factions_involved | list | → factions | Involved factions |
| locations | list | → locations | Key locations |
| themes | list | — | Major themes explored |
| hook | string | — | How arc begins |
| inciting_incident | string | — | Event setting it in motion |
| climax_summary | string | — | What happens at climax |
| resolution_summary | string | — | How it resolves |
| cliffhangers | list | — | Unresolved questions |
| revelation_count | number | — | Major plot twists |
| setup_threads | list | from_arc, thread_description | Plot threads from earlier |
| payoff_threads | list | resolves | What gets resolved |
| setup_for_next | list | — | Threads for future arcs |
| pacing_notes | string | — | Story rhythm notes |
| act_structure | object | act_1, act_2, act_3 | Three-act breakdown |
| key_scenes | list | — | Most important scenes in order |
| emotional_arc | string | — | Emotional journey |
| stakes | string | — | What is at risk |
| central_question | string | — | The question arc answers |

## Event Schema

**Required:** name, type

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Event name/title |
| type | enum | war, battle, birth, death, founding, discovery, plague, cataclysm, trade_agreement, coronation, rebellion, treaty, milestone, marriage, festival, catastrophe, custom | Event type |
| date | string | — | When occurred (WorldDate, year, era) |
| date_precision | enum | exact, approximate, approximate-season, approximate-year, unknown | How precise we know the date |
| end_date | string | — | End date for duration events |
| duration | string | — | How long event lasted |
| significance | enum | trivial, minor, notable, important, crucial, world-changing | Narrative importance |
| scope | enum | personal, family, local, regional, continental, global, cosmic | Geographic/social impact |
| historical_importance | string | — | How historians regard it |
| participants | list | entity, role, impact | Involved entities with roles |
| primary_characters | list | → characters | Main characters |
| primary_factions | list | → factions | Major factions |
| locations | list | → locations | Where it occurred |
| primary_location | ref | → locations | Main location |
| caused_by | list | → events | Events that led here |
| root_causes | list | — | Underlying reasons |
| immediate_trigger | string | — | What specifically started it |
| leads_to | list | → events | Events this caused |
| immediate_consequences | list | — | What happened right after |
| long_term_consequences | list | — | Long-term effects |
| political_impact | string | — | Power structure changes |
| economic_impact | string | — | Trade/wealth effects |
| social_impact | string | — | Cultural/population effects |
| magical_impact | string | — | Magic/creature effects |
| death_toll | string | — | Lives lost |
| casualties | object | death_count, injured_count, missing_count | Casualty counts |
| outcome | enum | decisive, pyrrhic, stalemate, ongoing, ambiguous, reversed, subverted | Resolution clarity |
| winner | list | → characters/factions | Who benefited |
| loser | list | → characters/factions | Who was harmed |
| narrative_significance | string | — | Why it matters to story |
| turning_point | boolean | — | Fundamentally changes story? |
| public_knowledge | boolean | — | Is it widely known? |
| descriptions | object | machine, human, image_prompt | Event descriptions |
| sources | list | — | Where we know this from |
| reliability | enum | firsthand, well-documented, rumored, conflicting-accounts, legend, false-history | Knowledge reliability |

**Participant Roles:** protagonist, antagonist, ally, witness, victim, beneficiary, facilitator, observer, affected, custom

## Species Schema

**Required:** name, sentience

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Species name |
| sentience | enum | sapient, semi-sapient, non-sapient, hive-mind, artificial, unknown | Intelligence level |
| biology | object | See below | Biological traits |
| habitat | object | native_terrain, climate_preference, range, population_estimate, population_trend | Where they live |
| culture | object | See below | Sapient-only fields |
| races | list | → races | Known subraces |
| relationships | list | species, disposition, can_interbreed, notes | Relationships to others |
| creature | object | danger_level, domesticable, uses, pack_size, territorial | Non-sapient fields |
| origin | string | — | How species came to exist |
| first_appearance | string | — | First mention in story |

**Biology.classification:** humanoid, beast, avian, aquatic, insectoid, reptilian, plant, fungal, elemental, undead, construct, aberration, celestial, fiend, fey, dragon, ooze, custom

**Biology.size:** tiny, small, medium, large, huge, gargantuan, colossal, variable

**Biology.reproduction:** sexual, asexual, budding, spore, magical, constructed, unknown

**Biology.diet:** omnivore, herbivore, carnivore, photosynthetic, mana-absorbing, scavenger, parasitic, none, custom

**Culture.social_structure:** tribal, feudal, democratic, theocratic, meritocratic, hive, nomadic, anarchic, imperial, corporate, council, custom

**Culture.technology_level:** stone-age, bronze-age, iron-age, medieval, renaissance, industrial, modern, post-modern, space-age, post-singularity, magical-equivalent, custom

**Creature.danger_level:** harmless, nuisance, dangerous, deadly, apocalyptic

**Species Relationships.disposition:** allied, friendly, neutral, wary, hostile, predator-prey, symbiotic, parasitic, unknown

## Race Schema

**Required:** name, species

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Race/subrace name |
| species | ref | → species | Parent species |
| variation | object | distinguishing_traits, average_height, average_build, lifespan_modifier, unique_abilities | Biological differences |
| culture | object | See below | Cultural identity |
| relationships | list | race, disposition, history | Relationships to other races |
| faction_affiliations | list | → factions | Commonly affiliated factions |
| population | object | estimate, distribution, trend | Demographic data |
| origin | string | — | How race diverged from base species |
| magic_affinity | string | — | Relationship to magic |
| first_appearance | string | — | First appearance in story |

**Culture.homeland:** ref → location (ancestral territory)

**Culture.language:** ref → language (primary language)

**Culture.social_structure:** string (may differ from species norm)

**Culture.naming_conventions:** object with pattern, examples, notes

**Race Relationships.disposition:** allied, friendly, neutral, wary, hostile, rival, vassal, overlord

## Language Schema

**Required:** name, status

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Language name |
| status | enum | living, endangered, dead, extinct, constructed, divine, ancient, proto | Current status |
| family | object | family_name, branch, parent_language, child_languages, proto_language, divergence_date | Family tree |
| intelligibility | list | language, score, direction, notes | Mutual comprehension (0.0-1.0) |
| script | object | name, type, direction, shared_with, literacy_rate | Writing system |
| speakers | object | native_species, native_races, as_second_language, total_speakers, geographic_range | Who speaks it |
| characteristics | object | phonology, grammar_notes, registers, loanwords_from, loanwords_to | Language features |
| special | object | is_lingua_franca, is_sacred, magical_properties, can_be_spoken_by, nonverbal_component | Special properties |
| origin | string | — | How language came to exist |
| first_appearance | string | — | First appearance in story |

**Script.type:** alphabet, syllabary, logographic, abjad, abugida, runic, pictographic, telepathic, magical, none

**Intelligibility.direction:** mutual, one-way-to, one-way-from

**Status Meanings:**
- living: actively spoken by community
- endangered: few remaining speakers
- dead: no native speakers, but understood (like Latin)
- extinct: no speakers, no comprehension
- constructed: deliberately created
- divine: language of gods/cosmic entities
- ancient: predates recorded history, partially reconstructed
- proto: reconstructed ancestor language (never directly spoken)

## Lineage Schema

**Required:** name

| Field | Type | Key Values | Notes |
|-------|------|-----------|-------|
| name | string | — | Dynasty/family name |
| type | enum | royal, noble, common, divine, magical, clan, corporate, custom | Lineage type |
| species | ref | → species | Primary species |
| race | ref | → race | Primary race (if relevant) |
| seat | ref | → locations | Ancestral home/seat of power |
| faction | ref | → factions | Controlling organization |
| heraldry | object | sigil, colors, motto, words | Visual identity |
| bloodline | object | inherited_traits, inherited_powers, genetic_weaknesses, blood_purity | Family traits |
| founder | ref | → characters | Earliest ancestor |
| current_head | ref | → characters | Current family leader |
| members | list | → characters | All known members |
| succession | object | rule, title, history | Succession rules and history |
| status | enum | active, declining, extinct, exiled, hidden, ascendant, scattered | Current status |
| founded | worlddate | — | When lineage established |
| ended | worlddate | — | When ended (if applicable) |
| allied_lineages | list | → lineages | Allied families |
| rival_lineages | list | → lineages | Rival families |
| marriage_alliances | list | member, married_into, date, political | Political marriages |
| first_appearance | string | — | When first mentioned |

**Succession.rule:** primogeniture, male-primogeniture, ultimogeniture, elective, meritocratic, combat, divine-selection, custom

**Succession.history items:** ruler (ref), reign_start, reign_end, how_ended (death, abdication, deposition, conquest, disappearance, custom)

---

## Cross-Reference Relationships

**Character ↔ Others:**
- → locations (location, first_appearance location)
- → factions (faction)
- → arcs (arc)
- → characters (relationships list)
- → items (inventory)
- ← lineages (members, founder, current_head)

**Location ↔ Others:**
- → locations (parent in hierarchy, routes to other locations)
- → characters (notable_characters)
- → factions (faction owner)
- ← characters (location)
- ← items (location if unowned)
- ← events (primary_location, locations)

**Faction ↔ Others:**
- → characters (leader, leaders, members)
- → locations (headquarters, territories)
- → factions (relationships)
- ← characters (faction)
- ← events (primary_factions)

**Event ↔ Others:**
- → characters (primary_characters, participants)
- → factions (primary_factions, participants)
- → locations (primary_location, locations)
- → events (caused_by, leads_to)
- ← characters (no direct ref, but timeline tied)
- ← events (causality links)

**All Entities:** descriptions (machine, human, image_prompt)
