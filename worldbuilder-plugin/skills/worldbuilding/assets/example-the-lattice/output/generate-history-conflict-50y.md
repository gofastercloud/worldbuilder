# Procedural History Generation — The Lattice
## Task: Generate 50 years of history

## World State

Genre: scifi
Calendar: Galactic Standard Calendar

Eras: Pre-Contact (PC), Contact Era (CE), Lattice Era (LE), Present Era (PE)

### Species (6)
- Humans: sapient, pop ~~800 billion across all systems
- Vaelori: sapient, pop ~~15 billion (declining)
- Thuranni: sapient, pop ~~90 billion
- Mek'vol: sapient, pop ~~8 billion (across all ships)
- Keth'ri: sapient, pop ~~200 billion
- Dresh: sapient, pop ~~50 billion

### Factions (8)
- The Reclaimers: rising
  Goals: find a new Mek'vol homeworld, investigate homeworld destruction, settle permanently
- Lattice Systems Corp: active
  Goals: maintain lattice drive monopoly, maximize shareholder value, expand infrastructure
- Keth'ri Collective: active
  Goals: maintain manufacturing dominance, achieve fair trade terms, reach consensus on galactic issues
- Galactic Trade Authority: active
  Goals: maintain galactic stability, regulate trade, enforce law
- The Free Trade League: rising
  Goals: break LSC monopoly, rim economic independence, free trade without GTA taxation
- The Quiet: hidden
  Goals: prove AI systems are colluding, expose the network, develop countermeasures
- Dresh Mining Guilds: active
  Goals: fair mineral prices, reduced AI dependency, clan autonomy
- Vaelori Concord: declining
  Goals: preserve Vaelori culture, maintain galactic peace, understand deep time

### Locations (22)
- Meridian Station [station]: pop ~45 million permanent, ~10 million transient
- Wanderer's Rest [station]: pop ~500,000 permanent, variable transient
- Rim Systems [region]: pop ~400 billion
- The Lattice [galaxy]: pop ~1.2 trillion sapients
- Terra Prime [planet]: pop ~12 billion
- Keth Prime [planet]: pop ~80 billion
- Thuranni Depths [star-system]: pop ~60 billion
- The Bazaar [station]: pop ~8 million permanent, ~3 million transient
- Crucible [planet]: pop ~12 billion
- Dresh Holdings [star-system]: pop ~35 billion
- Keth Prime System [star-system]: pop ~120 billion
- Vaelor System [star-system]: pop ~18 billion
- Pelago [planet]: pop ~40 billion
- Mid Systems [region]: pop ~350 billion
- Whisper Station [station]: pop 1 (Whisper)
- Haven [planet]: pop ~20 billion
- The Drift [region]: pop ~8 billion (across generation ships)
- Dead Space [region]: pop unknown
- Sol System [star-system]: pop ~80 billion (system-wide)
- Crossroads System [star-system]: pop ~30 billion
- Vaelor [planet]: pop ~10 billion (declining)
- Core Systems [region]: pop ~400 billion

### Resources (10)
- Lattice Fuel [strategic]: uncommon
- Rare Minerals [raw-material]: uncommon
- Water [essential]: common (core) / scarce (rim)
- Nutrient Cultures [food]: common
- AI Processing Cores [technology]: uncommon
- Manufactured Goods [finished-goods]: common
- Information Packets [knowledge]: varies
- Biological Specimens [scientific]: rare
- Null-Crystal [strategic]: rare
- Vaelori Cultural Artifacts [luxury]: very-rare

### Existing Timeline (last 10 events)
- [{'year': 1200, 'era_prefix': 'PC'}] Keth'ri Achieve Spaceflight (milestone)
- [{'year': 1200, 'era_prefix': 'PC'}] Keth'ri Industrial Expansion (milestone)
- [{'year': 2200, 'era_prefix': 'PC'}] Mek'vol Homeworld Destruction (cataclysm)
- [{'year': 2200, 'era_prefix': 'PC'}] The Drift Begins (milestone)
- [{'year': 2500, 'era_prefix': 'PC'}] Humans Achieve Spaceflight (milestone)
- [{'year': 1, 'era_prefix': 'PE'}] Frontier Unrest Begins (rebellion)
- [{'year': 3, 'era_prefix': 'PE'}] Lattice Systems Corp Pricing Scandal (trade_agreement)
- [{'year': 5, 'era_prefix': 'PE'}] Keth'vol Discovers Financial Anomalies (discovery)
- [{'year': 5, 'era_prefix': 'PE'}] Seren Voss Notices Route Anomalies (discovery)
- [{'year': 5, 'era_prefix': 'PE'}] Zephyr Intercepts Zero-Width Wormhole Transmission (discovery)

### World Constraints

## Generation Instructions
Generate 50 years of history for this world.
Output as a sequence of event YAML frontmatter blocks.

Focus on: wars, rebellions, sieges, betrayals, power struggles, resource conflicts.

For each event, output:
```yaml
---
name: "Event Name"
type: war|battle|birth|death|founding|discovery|plague|cataclysm|trade_agreement|coronation|rebellion|treaty|milestone
date: "ERA YEAR"                    # or start_date/end_date for duration events
significance: trivial|minor|moderate|major|world-changing
scope: personal|local|regional|national|continental|global
participants:
  - entity: "entity-slug"
    role: "description"
locations: ["location-slug"]
caused_by: ["previous-event-slug"]
leads_to: ["next-event-slug"]
economic_impact:
  production_effects: []
  trade_effects: []
---
Brief description of the event and its consequences.
```

Rules:
- Events must be chronologically ordered
- Causality chains must be logical (cause precedes effect)
- Respect ALL world flags (no gunpowder tech if flag is false, etc.)
- Dead characters cannot participate in later events
- Reference existing entities by their slugs
- You may create NEW entities (characters, factions, locations) as needed
- Economic impacts should cascade realistically
