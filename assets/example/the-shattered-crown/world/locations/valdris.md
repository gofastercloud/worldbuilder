---
name: "Valdris"
aliases: ["The Shining City", "Crown City"]
type: city
parent: ""
coordinates: { x: 500, y: 300 }
climate: "temperate"
population: "~50,000"
faction: "the-silver-order"
notable_characters: ["kael-dawnblade", "queen-morwen"]
routes:
  - to: "the-sunken-library"
    route_type: major
    bidirectional: true
    methods:
      - mode: horse
        travel_time: "4 days"
        distance: "120 miles"
        danger_level: moderate
      - mode: walking
        travel_time: "8 days"
        distance: "120 miles"
        danger_level: high
      - mode: caravan
        travel_time: "6 days"
        distance: "120 miles"
        cost: "15 silver"
        danger_level: moderate
  - to: "the-sunken-library"
    route_type: hidden
    bidirectional: true
    methods:
      - mode: portal
        travel_time: "instant"
        distance: "n/a"
        danger_level: moderate
        requires: ["Weave attunement", "Gate key"]
transport_hub:
  hub_type: nexus
  capacity: "Major trade hub"
  services: [stabling, smithing, inns, market, Silver Order garrison]
resources: [iron, timber, grain]
dangers: []
first_appearance: ""
tags: [capital, trade-hub, fortress]
---

## Description
The greatest city of the Age of Crowns. Valdris sits atop a plateau overlooking three river valleys, its white walls visible for miles. The throne room where Queen Morwen fell still bears the scars.

## History
Founded in 2A 12 after the Sundering reshaped the land. Built around one of the few intact Weave Gates.

## Geography & Layout
Three concentric rings: the Outer Ring (markets, common folk), the Middle Ring (guilds, military), and the Crown Ring (palace, Silver Order chapter house, the Weave Gate).

## Culture & Customs
A martial city. The Silver Order's presence is felt everywhere. Annual remembrance of the Sundering.

## Points of Interest
- The Shattered Throne: Where Queen Morwen died
- The Silver Bastion: Headquarters of the Silver Order
- The Weave Gate: Ancient portal, heavily guarded

## Transport & Access
Primary hub of the King's Road network. All major overland routes converge here. A hidden Weave Gate connects to the Sunken Library, but few know of its existence.

## Secrets & Hidden Features
The Weave Gate beneath the palace is cracking. The Silver Order's astrologers believe it may fail within a generation.

## Notes
