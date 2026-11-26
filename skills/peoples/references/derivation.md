# Deriving a people from its origin

Work top to bottom. For each layer, read the named source files first, write the answer in the entity, and note the cause in the prose body ("because ...").

## 1. Homeland (source: location files, `geography-and-climate`)

Ask: terrain, elevation, latitude and climate band, water source, seasons, hazards, flora, fauna, minerals, neighbours, travel routes. Take them from the location and its parent chain; if a field is empty, fill it via `geography-and-climate` before continuing.

Write: race `culture.homeland`, `current_territories`; species `habitat.native_terrain`, `climate_preference`, `range`. The homeland's file should list the people as inhabitants.

## 2. Biology and diet (source: homeland, species flags)

| Environment | Plausible traits |
|---|---|
| Cold, high latitude or altitude | Stocky build, fat stores, thick fur or hide, large lungs, slow reproduction, seasonal hibernation or caching of food |
| Hot, arid | Slender build, water economy, nocturnal habits, burrows, heat-tolerant skin |
| Dense forest or canopy | Climbing limbs, small to medium size, camouflage, strong hearing and smell |
| Open plains | Endurance running, herd or pack social habits, keen sight, mobility |
| Deep underground or dark | Non-visual senses (tremorsense, echolocation), pale or dark pigment, low metabolism, mineral diet |
| Aquatic or littoral | Streamlined body, gills or breath-holding, tides shaping time and work |
| Low gravity, thin air, high radiation | Frame, lung and shielding adaptations; shelter-based settlement |

Diet must be satisfiable from named local sources. Sapient omnivores in farmland need a crop calendar; carnivores need game or herd numbers; mineral eaters need accessible ore. Lifespan and maturity: slow reproduction and long lifespans go together with low birth rates, long childhoods and slow population recovery after losses. Fast breeders have shorter lives, many children and rapid recovery.

Write: species `biology` (size, lifespan, maturity_age, diet, senses, physical_traits), `habitat`. Races vary within these limits, stating the reason (altitude, diet, isolation).

## 3. Settlement and economy (source: `economy-and-trade`)

Pick settlement form from the food base: foragers and herders move (small bands, low density); farmers settle (villages to cities, density by yield); fishing and trade coasts cluster in ports; extractive sites cluster at deposits. Density per square kilometre: foraging below 0.1, pastoral 0.5 to 2, early farming 10 to 40, irrigated or river farming 50 to 200 (cities higher if food is imported). Record in the location file and in race `population.distribution`.

What they make and sell should follow resources; what they lack, they import (so trade routes and contact languages exist). If a people has a surplus, say what it buys; if a deficit, say how it is met.

## 4. Social structure, family and politics (source: settlement, economy, lifespan)

See `society.md`. Factions form at friction points: contested resource, border, tax, belief, succession dispute, trade monopoly, labour grievance. Each faction records its cause in `founding_event` or description and links an event where one exists.

## 5. Religion and myth (source: environment, history)

Beliefs encode survival knowledge and memory: what is dangerous becomes sacred or taboo; seasonal cycles become festivals; floods, famines, wars and migrations become origin myths. Religion changes after events: conquest brings syncretism or suppression; plague brings penitential cults; prosperity brings civic religion. Record the formative event (link it) and update the religion when later events change conditions. Magic and gods follow world flags.

## 6. Language (source: homeland, anatomy, contact; see `language-and-names.md`)

Sound inventory must be producible by the species' anatomy; the environment may favour certain sounds (open terrain for carrying consonants, dense forest for whistled or low sounds). Names, place names and loanwords then follow.

## 7. Customs and taboos (source: layers 1 to 6)

For each custom or taboo write one clause of "because": `traditions: "First-frost feast (the herds are culled before the pass closes)"`. Common triggers: scarce resource etiquette, disease avoidance, funerary practice tied to terrain (burial, cremation, sky burial, sea), hospitality rules where travel is dangerous, marriage rules that bind kin groups or avoid inbreeding, craft secrecy where skill is wealth.

## Questions to ask of any people

- Why here, and when did they arrive?
- What do they eat, and where does it come from?
- Who do they trade with and what words did they borrow?
- Who do they fight over what?
- Which event changed them most, and what trace does it leave in names, faith and law?
- What would be different about them if their homeland were five degrees colder or their main river dried up?
