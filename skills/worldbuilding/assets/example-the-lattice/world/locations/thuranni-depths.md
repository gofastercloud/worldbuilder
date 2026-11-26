---
name: "Thuranni Depths"
aliases: ["The Water System", "Deep Blue"]
type: star-system
parent: "mid-systems"
coordinates: {}
climate: "aquatic"
population: "~60 billion"
faction: ""
notable_characters: []
routes:
  - to: "crossroads-system"
    route_type: major
    bidirectional: true
    methods:
      - mode: lattice-drive
        travel_time: "5 days"
        distance: "interstellar"
        danger_level: low
transport_hub: {}
dangers: ["extreme-pressure-environments", "navigation-hazards"]

descriptions:
  machine:
    architecture: "A system of three water worlds orbiting a warm yellow star. Orbital infrastructure is minimal — the Thuranni prefer underwater construction. Surface platforms and orbital stations serve as interfaces between the aquatic civilization below and the dry galaxy above."
    atmosphere: "Aquatic, alien, inaccessible to most. The real civilization exists below the waves, invisible from orbit."
    notable_features: "Pelago (capital world), three water worlds, the galaxy's largest aquaculture operations"
  human: "Thuranni Depths is a system of water worlds — three blue spheres orbiting a warm star, with barely enough surface infrastructure to qualify as 'inhabited' by dry-species standards. The real civilization is below the surface, in ocean cities that non-Thuranni can only visit in pressure suits. From orbit, the worlds look pristine and empty. Below the waves, sixty billion Thuranni feed the galaxy."

first_appearance: "book-1"
tags: [water-worlds, aquaculture, thuranni-home, food-production]
terrain: "three ocean worlds; surface interface platforms and orbital processing stations"
climate_profile:
  zone: oceanic
  temperature_c: { annual: [22, 30] }
  hazards:
    - { name: "extreme pressure", season: year-round, frequency: "constant", effect: "non-Thuranni confined to platforms and armoured submersibles" }
  drivers:
    - "warm yellow star over three water worlds"
hydrology: { freshwater: abundant, notes: "bulk water export, about 35% of galactic supply" }
flora:
  - { species: "tide-kelp", role: staple-crop }
fauna:
  - { species: "abyssal-lanternfish", role: fishery }
  - { species: "pressure-stalker", role: apex-predator }
resources:
  - { name: "nutrient-cultures", category: food, rarity: common, notes: "the Deep Current; very high volume" }
  - { name: "water", category: custom, rarity: abundant }
  - { name: "biological-specimens", category: knowledge, rarity: rare }
---

## Description

Thuranni Depths is a system of three water worlds that serve as the Thuranni homeworld complex and the galaxy's primary food production center. The system's aquaculture operations feed hundreds of billions of sapients across the Lattice.

## History

The Thuranni evolved on Pelago, the system's largest water world, and expanded to the other two worlds early in their spacefaring history. The system's importance grew dramatically during the Lattice Era, when the connected galaxy's demand for food outstripped any single world's production capacity.

## Points of Interest

- **Pelago** — the Thuranni capital, largest ocean world
- **Surface Interface Platforms** — where non-Thuranni interact with Thuranni civilization
- **Aquaculture Processing Stations** — orbital facilities for packaging and shipping food products

## Notes

The Thuranni Depths system has minimal AI infrastructure compared to core systems, partly because deep-ocean environments are hostile to standard computing hardware. This gives the Thuranni a degree of independence from the AI network that they don't realize they have.
