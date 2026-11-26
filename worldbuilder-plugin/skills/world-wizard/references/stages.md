# Stage detail

For every stage: load the named skill and follow it for the detail; this file only says what the wizard needs out of each stage. Write both sides of every link, validate, fix errors, then move on.

## Stage 1: flags and premise

Deliver: complete `project.yaml` (flags, style, calendar block), `world/overview.md` (premise, tone, the one or two "what if" ideas that make this world distinct) and `world/rules.md` (what the flags forbid and allow, in plain words, including the magic answer). Write the premise as causes, not as scenery: "an ocean current that never reaches the north" beats "a cold land".

## Stage 2: geography and climate (`geography-and-climate`)

Deliver: world shape and size, the top-level locations, then regions and settlement sites in hierarchy with `parent` links, climate zones from latitude, elevation and currents, terrain, flora and fauna, mineral and agricultural resources, rivers, passes, coasts and routes with transport modes allowed by the flags. Settlements should sit where water, food, defence or a route explain them. Leave population, factions and trade for later stages, but note in `resources` what each place can produce.

## Stage 3: peoples (`peoples`)

Deliver: sentient species (if any besides humans) with origin locations, lifespans, physiology and the pressure that shaped them; races or ethnic groups with homelands; languages with families, sound feel and naming conventions; cultures' diet, dress, housing and belief shaped by their origin place. Lifespans and generation lengths set what history can contain, so fix them now. Do not give any species supernatural traits unless magic is present and a system will own them.

## Stage 4: economy (`economy-and-trade`)

Deliver: resources and who produces them, production chains, trade routes tied to the geography routes, currency or barter, prices, institutions (guilds, markets, banks, temples), and the surplus or scarcity that will drive conflict. Population, army size, food supply and tax base must be mutually plausible.

## Stage 5: magic (`magic-systems`), only if `magic.present` is true

Deliver: one entity per system with source, cost, limits, users, institutions, and its footprint on economy (what magic makes cheap or dear), geography (where it is strong) and peoples (who can use it). Retrofit stages 2 to 4 with the footprint. If magic is absent, skip this stage and say so in the bible.

## Stage 6: history (`history-and-events`)

Deliver: finalise `world/history/calendar.yaml` with eras (each with `prefix` and strictly increasing `sort_order`) and the epoch, then events era by era, with the counts from that skill's pacing table for the chosen size. Validate after each era. Events should explain the present: every major present-day fact (borders, rivalries, trade patterns, religions) must trace to events, and every event to earlier causes in geography, resources or peoples.

## Stage 7: folklore (`folklore-and-traditions`)

Deliver: for each significant event, consider whether it leaves a tradition (a myth, custom, taboo, festival, proverb, song or oath) and write those that do, each derived from a real event with a distortion and its cause, carriers, fidelity, and present-day `drives`. Counts: S 2 to 4, M 5 to 10, L 10 to 20, XL 20 to 40. Include at least one pair of variants that contradict, with a cause for each. Respect the magic gate (beliefs only if magic is absent). Write `traces` on the events, and update the locations, routes, economy and peoples that the `drives` change.

## Stage 8: factions, characters, hooks (`peoples`)

Deliver: factions with leaders, goals, resources and rivalries grounded in the economy and history; lineages if the size calls for them; characters with birth and death dates inside lifespans, locations, factions, relationships (bidirectional), voice as prose context (description, accent, dialect, tags), secrets and goals; items that have provenance events; arcs (story threads) and a short list of hooks: open tensions a story or campaign could start from. Characters must be alive and old enough on every date they appear.

## Stage 9: bible

`world/bible.md` outline:

1. Premise (one paragraph).
2. The rules: flags in plain words, including magic yes or no and the technology ceiling.
3. The world in ten lines: shape, regions, peoples, economy, powers.
4. Causal spine: 5 to 10 chains, each "physical fact, so resource or settlement, so trade or institution, so conflict, so present tension", with the entity slugs in brackets after each link.
5. Cast and factions: one line each for the main ones.
6. Story hooks: 3 to 6.
7. Validation: the checker result, and anything knowingly left unresolved.

Show the user a condensed version (premise, the spine, hooks, validation result) in chat.
