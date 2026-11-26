---
name: "Wanderer's Rest"
aliases: ["The Gathering Point", "Rest Station"]
type: station
parent: "the-drift"
coordinates: {}
climate: "controlled"
population: "~500,000 permanent, variable transient"
faction: "the-reclaimers"
notable_characters: ["rova"]
routes: []
transport_hub:
  type: "gathering point"
  connections: ["the-drift"]
dangers: ["isolation", "resource-scarcity", "factional-disputes"]

descriptions:
  machine:
    architecture: "A large station built from components of decommissioned generation ships, maintained and expanded over millennia. The architecture is layered — each era of construction visible in different materials and styles. Docking capacity for dozens of generation ships simultaneously. Interior spaces are designed for zero-g and variable gravity."
    atmosphere: "Communal, historic, contested. Wanderer's Rest is where Mek'vol come to remember they're a species, not just individual ship-clans. It's also where the Reclaimer debate is loudest."
    notable_features: "The Great Archive (accumulated Mek'vol records), the Gene Hall (genetic exchange facility), the Ship Graveyard (decommissioned vessel components)"
  human: "Wanderer's Rest is a station made of ghosts — literally built from the hulls and components of generation ships that finally gave out, their bones repurposed into a gathering place for the living fleet. It's ancient, layered, and haunted by the weight of a species' accumulated history. When the generation ships converge here for a Great Gathering, the station comes alive — Mek'vol trading, arguing, sharing genetic material, and debating whether to keep wandering or finally settle down. Between gatherings, it's a quiet museum staffed by keepers who maintain the accumulated records of a civilization that carries its history in cargo holds instead of libraries."

first_appearance: "book-1"
tags: [mekvol-gathering, historic, salvaged-architecture, remote]
terrain: "station built from salvaged generation-ship hulls, orbiting a dim red dwarf"
climate_profile:
  zone: artificial
  temperature_c: { annual: [12, 22] }
  hazards:
    - { name: "structural fatigue", season: year-round, frequency: "ongoing", effect: "salvaged hull sections sealed as they age" }
    - { name: "decompression", season: year-round, frequency: "rare", effect: "layered construction has few shared bulkheads" }
    - { name: "supply shortfall", season: year-round, frequency: "occasional", effect: "rationing when Drift convoys run late" }
  drivers:
    - "orbits a dim red dwarf; little stellar heating, so all warmth is generated"
    - "recycled generation-ship life support"
hydrology: { freshwater: scarce, notes: "recycled; imported water via the Drift Routes" }
fauna:
  - { species: "brown-rat", role: pest, notes: "stores and the Ship Graveyard" }
resources:
  - { name: "information-packets", category: knowledge, rarity: common, notes: "the Great Archive" }
  - { name: "genetic-exchange", category: knowledge, rarity: unique, notes: "the Gene Hall" }
  - { name: "ship-repair", category: labor, rarity: common }
  - { name: "cultural-archives", category: knowledge, rarity: unique }
  - { name: "lattice-fuel", category: fuel, rarity: uncommon, notes: "consumed; inbound on the Drift Routes" }
  - { name: "nutrient-cultures", category: food, rarity: common, notes: "consumed; inbound on the Drift Routes" }
---

## Description

Wanderer's Rest is the Mek'vol species' only fixed installation — a station built from the components of decommissioned generation ships, serving as a gathering point for Great Gatherings and a permanent archive of Mek'vol history. It orbits a dim red dwarf in the outer rim, far from major lattice routes.

## History

Wanderer's Rest was established early in the Mek'vol diaspora as a permanent meeting point. Over four thousand years, it has been continuously expanded with materials from ships that could no longer travel, creating a layered archaeological record of Mek'vol technological development.

## Points of Interest

- **The Great Archive** — accumulated records from across the Mek'vol fleet, spanning millennia
- **The Gene Hall** — genetic exchange facility for maintaining species viability
- **The Ship Graveyard** — surrounding field of decommissioned vessel hulls

## Notes

The Great Archive at Wanderer's Rest contains ship logs from thousands of years of Mek'vol travel. Buried in these logs are records of AI behavioral anomalies dating back centuries — subtle changes in how ship AIs responded to commands after docking at new stations. No one has ever correlated these records across ships, because the data volume is enormous and the pattern is only visible in aggregate. Rova, with her information broker's instincts, is the person most likely to find it — if she knew what to look for.
