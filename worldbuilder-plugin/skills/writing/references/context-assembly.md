# Context assembly

Replicates the idea of a temporal world-state snapshot: filter the world to one moment, then brief yourself. Do it before writing anything. Read the files; do not rely on memory of earlier turns.

## 1. Anchor

State the anchor: event slug, era plus year (plus month and day if the calendar has them), or present day (`present_date` or `current_date` in `project.yaml` or `world/history/calendar.yaml`). Name the time window: a scene (hours), a story (months), a campaign (weeks to years).

## 2. Partition events by time

List events in `world/events/`, sort by WorldDate using the eras and `sort_order` in `calendar.yaml`.

- **Before**: established history. These are true and may be known, half known or forgotten.
- **During**: events in the window. These are the live situation.
- **After**: the future. Never let characters, narration or rumours reference it, except through prophecy that the world's magic and flags allow, and then it must not be reliable.

For the last three or four events before the anchor, read `immediate_consequences`, `social_impact`, `economic_impact`, `traces`. These are what the scene should show: price changes, refugees, grief, taxes, new laws, damaged buildings.

## 3. People

- Alive at the anchor: birth on or before, death after (or none). Old enough for what they do (the validator uses 16 as the minimum parent age gap; use judgement for work, war, rule).
- Where each is at the anchor: location, journey in progress, or unknown. Check against travel times: nobody crosses a mountain range in an afternoon.
- Faction, rank, relationships, secrets, goals.
- Species and race: lifespan, senses, physical traits from the machine description.
- Voice fields: description, tags, accent, dialect, `instruct`. If missing on a character, inherit `regional_defaults` up the location parent chain. Use them to shape rhythm and diction in prose and dialogue tags.

## 4. Places

For each location in the scene:
- Parent chain (building, district, city, region) and neighbours.
- Terrain, elevation, climate profile, seasons. Pick weather and light for the scene date from the climate data. If the data is missing, load `geography-and-climate`, derive it, and record it.
- Flora, fauna, resources, architecture, population, notable features, regional defaults (ethnicity, appearance, accent).
- Routes: endpoints, methods, travel_time, distance, danger, `seasonal` or `restricted` status.
- State at the anchor: damaged, besieged, prosperous, abandoned, depending on events.

## 5. Factions

Type, status, leader (must be a living character), headquarters, goals, allies and enemies, members in the scene. Decide what each faction is doing right now as a result of its goals and the recent events.

## 6. Knowledge

For each POV or speaking character and each key fact: what do they know, how, and from whom? Sources: personal experience, faction briefings, traditions they hold (`held_by`, `regions`, `language`), written records they can read. Use event `secrecy` and `known_by`. Variants: true, official, folk, distorted, forgotten. See `folklore-and-traditions`.

## 7. Languages and names

Languages spoken by those present, who is fluent, who is not, intelligibility between languages, scripts. Naming conventions of each people: order, patronymics, honorifics, place-name elements. New names invented in the scene must follow them (`peoples/references/language-and-names.md`).

## 8. Flags

Technology flags (gunpowder, printing, steam, FTL and so on) and the magic gate. If magic is absent, every apparent miracle needs a mundane cause or is belief. Check transport methods against flags.

## 9. Economy

Local resources, scarcities, prices, currency, trade route status, institutions (guilds, banks, markets). A scene in a market, tavern or camp should show prices and scarcity from the record, not generic coin amounts.

## 10. The brief

Compress into a half page: date, season and weather, place, who is present with what they know, what each wants, what has just happened, what must not be contradicted, and the secret truth versus the known story. Keep this brief visible while writing.
