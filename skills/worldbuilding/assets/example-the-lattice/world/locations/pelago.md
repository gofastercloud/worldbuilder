---
name: "Pelago"
aliases: ["The Deep World", "Thuranni Prime", "Blue Home"]
type: planet
parent: "thuranni-depths"
coordinates: {}
climate: "oceanic, warm"
population: "~40 billion"
faction: ""
notable_characters: []
routes: []
transport_hub: {}
dangers: ["extreme-pressure", "deep-ocean-predators", "environmental-incompatibility"]

descriptions:
  machine:
    architecture: "A water world with no permanent landmass. Thuranni cities are built on the ocean floor and along continental shelf structures, using pressure-resistant biomaterials and bioluminescent lighting. Surface platforms serve as interfaces for non-Thuranni visitors. The deepest cities reach pressures of 1000+ atmospheres."
    atmosphere: "Alien, beautiful, inaccessible. For Thuranni: warm, dark, safe, home. For non-Thuranni: a pressure-crushing abyss of darkness lit by bioluminescent cities they can only visit in armored submersibles."
    notable_features: "The Depths Assembly (Thuranni parliament), the Great Farms (aquaculture complexes visible from orbit), the Deep Cities"
  human: "Pelago is an ocean with a thin atmosphere on top — a world of water from pole to pole, with no land to speak of and no apology for it. From orbit, it's a featureless blue sphere. From a surface platform, it's an endless sea in every direction. From a submersible descending into the depths, it's another world entirely: bioluminescent cities glowing in the darkness like constellations made of living light, Thuranni swimming between structures in coordinated formations that are equal parts commute and cultural expression. It's the most beautiful place in the galaxy that will kill you if your pressure suit leaks."

first_appearance: "book-1"
tags: [ocean-world, thuranni-capital, aquaculture, underwater-cities]
terrain: "global ocean: continental shelves (100 to 500 m), deep basins and abyssal plain; no permanent landmass"
elevation_m: -4000
area_km2: 800000000
climate_profile:
  zone: oceanic
  temperature_c: { annual: [24, 30] }
  precipitation_mm: 1400
  rain_pattern: storm-track
  growing_season_days: 365
  hazards:
    - { name: "ocean storm cells", season: year-round, frequency: "weekly", effect: "surface platforms close; shuttle landings suspended" }
    - { name: "extreme pressure", season: year-round, frequency: "constant", effect: "fatal to non-Thuranni below shelf depth without armoured submersibles" }
  drivers:
    - "warm ocean world pole to pole, as described"
    - "no land to break weather systems"
hydrology: { freshwater: abundant, notes: "processed sea water; bulk water export" }
flora:
  - { species: "tide-kelp", role: staple-crop, notes: "the Great Farms, visible from orbit" }
  - { name: "bioluminescent algae mats", role: keystone, notes: "light the shelf cities" }
fauna:
  - { species: "abyssal-lanternfish", role: fishery, notes: "schools migrate between shelf and deep cities" }
  - { name: "farm-shoal fish", role: domesticate, notes: "aquaculture stock" }
  - { species: "pressure-stalker", role: apex-predator, notes: "the deep-ocean predators of the dangers list" }
resources:
  - { name: "nutrient-cultures", category: food, rarity: common, notes: "about 45% of galactic supply" }
  - { name: "water", category: custom, rarity: abundant, notes: "bulk export" }
  - { name: "biological-specimens", category: knowledge, rarity: rare }
---

## Description

Pelago is the Thuranni homeworld — a planet-spanning ocean with no permanent landmass, home to the galaxy's most alien civilization (from a dry-species perspective). Forty billion Thuranni live in deep-ocean cities that most non-Thuranni will never see, farming the aquaculture operations that feed the galaxy.

## History

Pelago is where Thuranni civilization emerged, developed, and remains centered. The Depths Assembly, the Thuranni parliament, has met in the same deep-ocean chamber for three thousand years.

## Geography & Layout

- **Surface layer** — interface platforms for non-Thuranni visitors, food processing stations
- **Shelf cities** — major population centers on continental shelf structures (100-500m depth)
- **Deep cities** — the oldest and most traditional settlements (1000-5000m depth), including the Depths Assembly
- **The Great Farms** — aquaculture complexes spanning thousands of square kilometers, visible from orbit as patterns in ocean color

## Points of Interest

- **The Depths Assembly** — Thuranni parliament, located at 3000m depth
- **The Great Farms** — planet-scale aquaculture operations
- **Surface Platform Alpha** — primary interface point for non-Thuranni visitors

## Notes

Pelago's deep-ocean cities are among the most AI-independent settlements in the galaxy. The extreme pressure environment requires specialized computing hardware that is expensive and limited. Most deep-ocean infrastructure is managed by organic systems — Thuranni bioengineering rather than AI automation. This makes Pelago a natural fallback position if the AI network's influence ever needs to be countered.
