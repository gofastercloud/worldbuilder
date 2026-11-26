---
name: peoples
description: Create, extend and check the peoples of a world, covering species, races, cultures, languages, characters, NPCs, families, lineages, dynasties, factions, religions, customs, taboos, names, population, demographics, society and politics. Use when the user adds or changes who lives in the world, how they are organised, what they believe, speak or are called, how many there are, or who a person is, who their parents are, or why a faction exists. Derives each people from their homeland, diet, economy and history so nothing is arbitrary.
---

# Peoples

A people is the product of where it lived, what it ate, how it made a living, what happened to it and who it met. Build every species, race, language, character, faction and lineage by derivation from those causes, and record both the cause and the consequence in the files. Load `worldbuilding` first for the project layout, the read-before-write procedure and `references/causality.md`; this skill adds the rules for people.

Entity fields are in `worldbuilding/references/entity-schemas.md` (species, race, language, lineage, character, faction) and templates in `worldbuilding/assets/templates/`. The model of good output is `worldbuilding/assets/example-the-lattice/world/` (species/dresh.md, races/deep-dresh.md, languages/dresh-rumble.md, lineages/clan-ironvein.md, characters/drenn-ironvein.md, factions/dresh-mining-guilds.md).

## Scope and sibling skills

| Need | Load |
|---|---|
| Homeland terrain, climate, flora, fauna, distances, resources | `geography-and-climate` |
| What the people produce, trade, tax, own; currency | `economy-and-trade` |
| Migrations, wars, foundings, deaths, eras, dates | `history-and-events` |
| Final check | `world-validate` |

If a homeland, resource or event you need does not exist yet, create it with the sibling skill first (or stop and ask), do not invent it inline in a people's file.

## Step 0: magic gate (never skip)

Read `world_flags.magic.present` in `project.yaml`. If it is false (or `prevalence: none`), write no supernatural content: no psionic or innate-power species traits, no magical affinity in races or lineages, no divine intervention in religions or origin myths, no magical creatures. Offer technology, psychology or natural explanations instead (engineered abilities, belief, biology). If it is unset, ask the user; the `magic-systems` skill owns the gate.

## Procedure (every time)

1. **Read origin first.** Read `project.yaml` (calendar, eras, world flags, especially `peoples.cross_species_breeding` and technology/magic flags). Then read: the homeland location and its parent chain; neighbouring locations; the species/race you are extending and its siblings; the language and its family; the faction(s) involved; events in the relevant era that touch these places or peoples. List what you read in one line.
2. **State the cause.** One line: why does this people/language/character/faction exist and look like this? Name the earlier fact (location feature, resource, event, contact). No cause means fix the idea or add the cause.
3. **Derive** in the order below. Do not skip layers; mark any layer you deliberately leave open with the reason.
4. **Write both sides** of every link (see Reciprocal links).
5. **Run the arithmetic** in `references/quantities.md` (lifespan, generations, population, divergence time).
6. **Consequence sweep** (below), then the checklist, then `world-validate`.

## The derivation chain

Each layer must follow from the one above and be recorded where the schema allows (field names in brackets). Detail and examples: `references/derivation.md`.

1. **Homeland** [race `culture.homeland`, species `habitat`]. Terrain, climate, elevation, water, hazards, from the location files. Never place a people somewhere the location files say is uninhabitable for them.
2. **Biology and diet** [species `biology`, `habitat`]. Body plan, size, senses, lifespan, diet and reproduction follow the habitat (cold means bulk and fat stores, thin air means large lungs or low activity, darkness means non-visual senses). A diet must be satisfiable from the local flora, fauna or minerals; name the food source and where it comes from.
3. **Settlement and economy** [race `culture`, location `population`]. What the land supports sets settlement form (nomadic, village, city, hold), density and trade goods. Take the economy from `economy-and-trade`; do not describe wealth the resources cannot produce.
4. **Social structure, family and politics** [species/race `social_structure`, lineage `succession`, faction]. Kin groups, marriage, inheritance and rule come from how people make a living and how long they live (see `references/society.md`). Factions form where interests collide: scarce resource, contested border, shared trade, belief, grievance.
5. **Religion and myth** [`culture.religion`, `values`, `taboos`, `traditions`]. Derive myths, customs and taboos from real events with the `folklore-and-traditions` skill (tradition entities, with `held_by` this people). Beliefs encode the environment (what is feared, what is sacred, what must be paid for) and the people's recorded events (a famine, a conquest, a migration becomes a festival or a taboo).
6. **Language** [language entity; race `naming_conventions`]. Sound inventory fits the speakers' anatomy and environment; names fit the language; loanwords record contact and trade; dialects drift with distance and time (see `references/language-and-names.md`).
7. **Customs and taboos** [`traditions`, `taboos`]. Every custom and taboo should trace to layers 1 to 6. If one cannot be explained, drop it or add the cause.

## Hard rules (checkable)

Use these as pass/fail checks. Full formulas in `references/quantities.md`.

- **Generations versus lifespan.** Generation length is about `maturity_age` to roughly 1.5 times `maturity_age` (mean age at parenthood), never more than the lifespan. N generations span about N times that. Do not claim "ten generations in 100 years" for a 25-year generation. A parent is at least `maturity_age` older than a child, and alive and fertile at the child's birth.
- **Lifespan arithmetic for characters.** `age` is at a stated date. Birth year = date minus age. Birth must follow the parents' births by at least their maturity, and a character cannot witness an event before birth or after death, nor lead anything before maturity.
- **Population versus carrying capacity.** Population cannot exceed what the territory's food output feeds. A people with N million needs a stated food source and area. Sustained pre-industrial growth is about 0.1 to 1 percent a year; above about 3 percent is never sustained (`references/quantities.md`). For food, farm-share and army numbers see the `economy-and-trade` skill, heuristics.
- **Species traits are inherited.** A race may vary a species trait modestly; it cannot contradict it (an aquatic species' race does not live on dry plateaus without explanation). Lifespan modifiers are stated relative to the species.
- **Language divergence needs time.** Two related languages need elapsed time and separation proportional to difference: dialects within about 200 to 500 years of separation (mostly intelligible), distinct languages after 1000 to 1500 years, a family after 3000 or more. Set `divergence_date`, `parent_language` and `intelligibility` consistently with the dates. Faster drift needs a stated cause (isolation, conquest, mass migration).
- **Names follow language.** A culture's names use its language's sounds, patterns and meanings; a naming scheme in `naming_conventions` must match the examples. Foreign-sounding names must be explained by contact, conquest, conversion or marriage.
- **Migrations leave traces.** A recorded migration or conquest produces at least one of: place names in the source language, loanwords, a dialect, a shared script, a shared deity, a diaspora race. Record it in both languages and both locations.
- **Inheritance matches lineage.** A lineage's `succession.rule` decides the order of heirs; a character's `title_inherited` must be reachable under that rule from their position. Succession history must be unbroken by lifespan: no ruler reigning past death, no gap without a stated interregnum or regency.
- **Interbreeding follows the flag.** Cross-species children exist only if the species `can_interbreed` and the `peoples.cross_species_breeding` flag allows it.
- **Every faction has a cause, a leader who is alive, and members who exist.** See `references/factions-and-lineages.md`.

## Characters

Full procedure: `references/characters.md`. Minimum for any character:

- `species` and `race` resolved to files; `location` and birthplace consistent with that race's homeland or an explained move; `faction` and `family_links.lineage` set and reciprocated.
- `age` with a date reference; parents consistent with the lifespan rules; `languages` consistent with homeland, faction and travel (a native language from the culture, plus second languages explained by trade, service or schooling).
- A name that fits the naming convention of their race and language.
- Motivation rooted in the record: what their people, family or faction has suffered or gained, and an event they were present at, absent from or too young for. Put "where they were" for each notable event in `Backstory`, and add them to the event's participants.
- `voice` describes how they sound, as prose context only. Accent and dialect come from their birthplace and class, not from the author's whim.

## Factions and lineages

Full rules: `references/factions-and-lineages.md`.

- **Formation cause.** State the grievance, resource, belief, conquest or trade interest that made the faction, with a date and (ideally) a `founding_event` linking an event file. A faction without a cause is an orphan.
- **Membership and leadership.** `leader` is a living character who is also a member and old enough. Rivalries and alliances are reciprocal and each has a reason (contested resource or border, historic event, doctrinal difference).
- **Lineages** have a founder or a stated origin, a seat, a faction link, a succession rule and an unbroken succession history with dates inside plausible lifespans. A lineage claiming to be ancient must show how it survived (heirs, adoption, regencies), not simply exist.

## Reciprocal links (write both sides)

| If you set | Also set |
|---|---|
| race `species` | species `races` lists the race |
| race `culture.language` | language `speakers.native_races` lists the race |
| species `culture.native_language` | language `speakers.native_species` lists the species |
| language `family.parent_language` | parent's `family.child_languages` lists it |
| character `faction` | faction `members` lists the character (and `leader`/`leaders` characters are members) |
| character `family_links.father/mother` | parent's `children` lists the child; siblings share a parent |
| `spouse`, `siblings` | the other character lists the same |
| character `family_links.lineage` | lineage `members` lists the character (head, founder too) |
| lineage `faction` | faction records the lineage in its description or members |
| lineage `allied_lineages`/`rival_lineages` | the other lineage lists the same |
| faction `relationships` | the other faction lists the reverse relationship |
| race/faction `homeland`/`headquarters`/`territories` | the location file notes the people or faction that lives or rules there |
| event `primary_characters`/`participants` | the character's backstory and `last_appearance` or timeline agree |

## Consequence sweep

After any addition or change, ask each question and edit the affected files now:

- **Geography and climate** (`geography-and-climate`): does the people need, or change, terrain, water, a settlement or a hazard? A new people's homeland should exist; a mass migration changes where cities and fields are.
- **Economy and trade** (`economy-and-trade`): what do they eat, make, sell and buy? Which route or price changes? A new people with no economic role is suspicious.
- **History and events** (`history-and-events`): which event founded, split, moved or killed them? Add or link it, with cause and effect, and update later events they should have joined.
- **Language and names**: does contact create loanwords or a pidgin? Does an elite shift name fashions? Update both languages.
- **Politics**: new faction, split, alliance or rivalry means updating every faction it touches. A death or birth means updating succession, leadership and household.
- **Population**: did numbers rise or fall? Update race/species `population`, location population, and anything that depends on labour or army size.

## Anti-patterns

- Monocultures: one race, one religion, one economy per species. Real peoples vary by region and class (use races and dialects).
- Humans with ears: a species whose biology, diet and senses change nothing about society, language or architecture.
- Names unrelated to language: a "Dwarvish" name list with no Dwarvish language entity, or characters whose names ignore the culture's pattern.
- Immortal lineages without succession: a bloodline with no heir history, or a long-lived species with no accounting for how heirs, inheritance and power turn over.
- Factions with no cause: a guild, order or rebel group that simply exists.
- Culture ignoring environment: seafarers inland with no river, horse nomads in a jungle, a desert people with water-based festivals and no explanation.
- Population with no food: cities of millions with no farmland, fishery, import route or magic supply.
- Instant divergence: two languages, dialects or races separated in fewer generations than needed.
- Backstory-only characters who were never at any event, or who attended events after they died.
- Writing the new file but not the reverse links.

## Checklist (before reporting done)

- [ ] Read homeland chain, neighbours, language family, faction and era events; listed them.
- [ ] One-line cause stated for each new entity; chain from homeland to custom is complete.
- [ ] Diet, settlement and population are supported by locations and economy; numbers stated.
- [ ] Lifespan, maturity, generation and character age arithmetic done and written down.
- [ ] Language, names, loanwords and migration traces agree with each other and with dates.
- [ ] Every faction/lineage has cause, founding date, living leader, succession rule and history.
- [ ] Every reciprocal link above written on both sides.
- [ ] World flags respected (cross-species, magic, technology).
- [ ] Consequence sweep done across geography-and-climate, economy-and-trade and history-and-events as needed.
- [ ] Ran the `world-validate` skill, fixed or reported every finding.

## Worked example (the-lattice, Dresh)

Cause chain, each step living in a file: `locations/crucible` is a volcanic, deep world with abundant ore -> `species/dresh`: silicon-based, lithivore, dense, tremorsense, heat and vacuum tolerance, lifespan 150-200, maturity 25 (so a generation is about 25 to 40 years, and Clan Ironvein's "millennia" of elders is about 25 to 40 generations) -> economy: mining; clan-guilds control territories because ore bodies are fixed, so kin groups hold the claims -> `factions/dresh-mining-guilds`: clan elders form a council; formed during the Contact Era to bargain with buyers (cause: outside demand for minerals, an event-era fact) -> `culture.religion` Stone Memory: minerals record history, a belief drawn from a life spent in rock -> `languages/dresh-rumble`: very low-frequency tonal speech with a touch component, because sound carries through stone and not air; script Stone Marks, written boustrophedon because it was carved along tunnels; evidentials in grammar; geological time words -> `races/deep-dresh` (stayed underground, darker, larger, +20 years lifespan from lower stress) versus `surface-dresh` (station traders, intermediaries): divergence is geographic and economic -> names `Forge-name + Clan` with geological clan names (Drenn Ironvein) -> `characters/drenn-ironvein`: age 80 against 150-200 lifespan means mid-life, Clan Elder for forty years (so elder since about age 40, past maturity 25), `lineage: clan-ironvein`, `faction: dresh-mining-guilds`, native language `dresh-rumble`, `voice` as prose context (rumbling Galactic Standard).

What to tighten in that example, as the rules above would flag: the Ironvein `founder` is empty while the history names "Ironvein the Founder" (create or link the character or state the origin); `divergence_date` and `parent_language` are empty on Dresh Rumble, so contact-era loanwords into Galactic Standard are asserted but not dated; Drenn's parents and children are blank although the lineage claims continuity. These are gaps to fill, not patterns to copy.

## References

- `references/derivation.md`: layer-by-layer derivation with examples and questions to ask.
- `references/society.md`: family forms, inheritance, politics, religion and customs from environment.
- `references/language-and-names.md`: sound inventories, naming schemes, loanwords, dialect drift, scripts.
- `references/quantities.md`: formulas for generations, ages, population, divergence times.
- `references/characters.md`: character procedure, timeline of presence, family trees.
- `references/factions-and-lineages.md`: faction and lineage formation, membership, succession.
