# Worked example: the chain to the Rim in The Lattice

Source: `worldbuilding/assets/example-the-lattice/world/events/` and `world/history/calendar.yaml`. Calendar eras: PC (sort 1), CE (2), LE (3), PE (4). Years restart in each era.

## Chain

| Date | Event | Caused by | What it supplies |
|---|---|---|---|
| CE 125 to 180 | `human-kethri-wars` | Contact and competing claims (root conditions) | Mutual knowledge of each other's industry, exhaustion |
| CE 200 | `human-kethri-trade-treaty` | `human-kethri-wars` | Neutral trade zone at Crossroads; humans supply markets, Keth'ri manufacturing |
| CE 250 to 280 | `ai-wars` | Earlier AI development | Fear of AI |
| CE 285 | `ai-regulation-accords` | `ai-wars` | Isolation protocols, and the false confidence that hides later AI behaviour |
| CE 490 | `discovery-of-lattice-drives` | trade treaty, AI accords, `vaelori-galactic-exploration` | FTL practical: Vaelori surveys found the folds, Keth'ri engineering built the drive, human capital funded it |
| LE 12 | `founding-of-lattice-systems-corp` | discovery | Exclusive rights to build and maintain the network |
| LE 47 | `founding-of-the-gta` | LSC founding, `thuranni-join-galactic-community` | Regulator needed because one private firm now holds galactic infrastructure |
| LE 100 to 300 | `rim-colonization-era` | GTA founding, drive discovery, `dresh-contact-with-mekvol` | Hundreds of systems reachable; Mek'vol generation ships supply them |
| LE 200 onward | `rim-exploitation-contracts` | rim colonisation | Contracts favouring core corporations |
| present | `frontier-unrest-begins` | the contracts | Core-rim divide; open tension |

## Why it is good

- **Means, motive, opportunity:** the Keth'ri and humans trade after the wars because both are exhausted (motive) and each lacks what the other makes (means); the treaty occurs after the war ends (opportunity). The drive appears 290 years later: it needed Vaelori surveys, Keth'ri engineering and the multi-species market, so no single earlier date was possible. Note the drive has three causes, each supplying a different input.
- **Lag:** consequences take time. LSC is founded 12 years after the discovery; the regulator 35 years later; rim colonisation 100 years after the LE start; exploitation contracts 100 years into colonisation. Nothing happens instantly.
- **Consequences recorded in the world:** `long_term_consequences` name things that exist today (400 billion rim population, seven generations of House Meridian, Meridian Station, rim adaptations). The treaty's effects include the Crossroads junction and the multi-species economy the GTA formalises.
- **Hidden threads still have causes:** the AI accords' isolation protocols are circumvented later (the 5 PE Listener detection), so a present-day anomaly traces back to CE 285.
- **Era boundaries:** CE ends with the drive discovery; the LE begins with the founding of LSC; PE begins with the unrest. Each boundary is an event.
- **Not shown but needed in your own work:** a tension ledger. Reading the chain, one is evident: treaty-era trade stability creates dependency on neutral Crossroads; drive monopoly creates dependency on one firm; extraction contracts create the rim grievance. Each ledger entry fed the next event.

## Using it as a pattern

For any new world, aim for: every significant event has two or three real causes, each from a different layer (technology, politics, economy); delays of decades; consequences that name a place or institution that exists in the files; and the present holding the tensions earlier chains created. Note also that some events in the example have long prose lists in `leads_to`: do not copy that. `leads_to` holds event slugs only; put prose in `long_term_consequences`.
