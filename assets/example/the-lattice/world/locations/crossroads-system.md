---
name: "Crossroads System"
aliases: ["The Junction", "Trade Center"]
type: star-system
parent: "mid-systems"
coordinates: {}
climate: "varied"
population: "~30 billion"
faction: ""
notable_characters: []
routes:
  - to: "sol-system"
    route_type: major
    bidirectional: true
    methods:
      - mode: lattice-drive
        travel_time: "6 days"
        distance: "interstellar"
        danger_level: low
  - to: "keth-prime-system"
    route_type: major
    bidirectional: true
    methods:
      - mode: lattice-drive
        travel_time: "4 days"
        distance: "interstellar"
        danger_level: low
  - to: "thuranni-depths"
    route_type: major
    bidirectional: true
    methods:
      - mode: lattice-drive
        travel_time: "5 days"
        distance: "interstellar"
        danger_level: low
  - to: "dresh-holdings"
    route_type: major
    bidirectional: true
    methods:
      - mode: lattice-drive
        travel_time: "12 days"
        distance: "interstellar"
        danger_level: moderate
transport_hub:
  type: "major junction"
  connections: ["sol-system", "keth-prime-system", "thuranni-depths", "dresh-holdings"]
resources: ["trade-goods", "services", "information", "transit"]
dangers: ["piracy", "smuggling", "market-volatility"]

descriptions:
  machine:
    architecture: "A busy system centered on Haven (primary planet) and The Bazaar (largest free market station). Infrastructure is mixed — high-quality trade facilities alongside improvised docking for frontier vessels. Multiple lattice drive route connections make this the most strategically positioned system in the galaxy."
    atmosphere: "Frenetic, cosmopolitan, deal-making. Crossroads System is where money changes hands, where information changes owners, and where the core and rim meet face to face."
    notable_features: "Haven (cosmopolitan trading world), The Bazaar (largest free market), junction of four major lattice routes"
  human: "Crossroads is exactly what it sounds like — the place where every route in the galaxy eventually passes through. Four major lattice connections meet here, making it the most strategically positioned system outside the core. Haven, the system's primary world, is the kind of place where a Dresh mineral trader can share a bar with a Vaelori philosopher and a Mek'vol information broker while a Keth'ri Speaker negotiates a shipbuilding contract at the next table. It's messy, noisy, and essential."
  image_prompt: "Sci-fi concept art. A busy star system with multiple lattice drive route lines converging. A habitable planet and a large market station visible. Dense ship traffic from multiple species' vessel designs. Junction aesthetic — multiple routes meeting. Cinematic, detailed, realistic. Negative prompt: cartoon, anime, bright colors, watermark, text, logo"

first_appearance: "book-1"
tags: [trade-junction, cosmopolitan, strategic, multi-route]
---

## Description

Crossroads System sits at the intersection of four major lattice drive routes, making it the galaxy's most important trade junction. Ships traveling from core to rim, from Keth Prime to Thuranni Depths, all pass through here. This strategic position has made it wealthy, diverse, and permanently chaotic.

## History

Crossroads was a minor system until lattice drive route mapping revealed its position at a natural junction. Within a century of lattice drive deployment, it became the galaxy's busiest transit point and most important neutral trading ground.

## Points of Interest

- **Haven** — cosmopolitan trading world
- **The Bazaar** — the galaxy's largest free market station

## Notes

Crossroads System is where Keth'vol is stationed — and where the financial irregularities that begin unraveling the AI secret are first detected. The system's position at the junction of multiple trade routes means it processes an enormous volume of financial transactions, making statistical anomalies more visible here than anywhere else.
