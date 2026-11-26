---
name: economy-and-trade
description: Build and check a world's economy so prices, wealth and trade follow from geography and technology. Use for economy, trade, resources, currency, coinage, prices, taxes, tariffs, guilds, merchant companies, markets, supply chains, trade routes, scarcity, industry, food supply, wealth and poverty, famine, embargoes, blockades, debt, inflation, or how an event, war, new route, invention or climate shift changes who is rich and what things cost. Also use when a city, army or faction needs its size justified by food and money.
---

# Economy and trade

An economy is a consequence of the map. Every good has a source, every city has a food supply, every route has a profit logic, every price has a reason, and every shock changes something else. This skill extends the core `worldbuilding` skill (read its `SKILL.md` and `references/causality.md` first: read before you write, cause before fact, consequence sweep, write both sides). Field names come from `references/economy.md` and `assets/templates/economy/_schema.yaml`; do not invent a parallel schema.

Reference files in this skill (load only what you need):

- `references/heuristics.md`: the numbers (food, farm share, surplus, transport cost, price caps, tax, army, currency).
- `references/entity-fields.md`: how to define resource, producer, consumer, route, market, currency, institution; optional fields that close gaps in the base schema.
- `references/impact-chains.md`: how embargoes, wars, new routes, technology and climate propagate.
- `references/worked-example.md`: a compact audit of The Lattice.

## Step 0: magic gate (never skip)

Read `world_flags.magic.present` in `project.yaml`. If it is false (or `prevalence: none`), write no supernatural content: no magic currency, transport, goods, reagents or mana fuel, no `magical` resource category, no `magical_economy: true`. Offer technology, psychology or natural explanations instead. If it is unset, ask the user; the `magic-systems` skill owns the gate.

## The causal model (work in this order)

Each step may only use what the earlier steps established. If a step is missing, go back and add it first.

1. **Resources and terrain.** What can be grown, mined, quarried, felled, fished or herded here? Take it from the location's climate, terrain, rivers, coast and geology (load `geography-and-climate` if these are not yet written). Rarity follows geology and climate, never taste.
2. **Agriculture and food surplus.** Calories per hectare times land, times growing season, minus seed, waste and fallow. Total food sets the ceiling on population. Surplus (food beyond what farmers eat) sets how many non-farmers can exist. Use the species' diet, not human assumptions (load `peoples`).
3. **Population and settlement.** Settlements cluster where surplus is high or cheap to move: river valleys, deltas, coasts, junctions, defensible ports. City size is capped by the food it can import at the transport cost of its catchment.
4. **Specialisation and production.** Non-farmers make things only from inputs that exist (ore plus fuel plus labour plus skill plus tool tech). Production concentrates where inputs are cheap and a market is near.
5. **Transport cost and routes.** Cost per tonne-km depends on mode (sea, river, road, rail, air, space; magic only if the gate allows). Routes follow the cheapest passable line, not the straightest. Routes carry goods only when profit survives cost, tolls and risk.
6. **Trade and prices.** Prices are lowest at the source, rise by transport plus tolls plus risk plus margin, and are highest where supply is scarcest and demand richest. Trade flows downhill in price, never against both cost and demand.
7. **Money and credit.** Currency exists to settle trade; its form follows available metals, issuing authority, trust and tech (coin, scrip, credit, commodity, ledger; magic only if the gate allows). Supply, debasement and debt follow from state finances and trade balance.
8. **Taxation and institutions.** States, temples, guilds, companies and leagues take a share where it is easiest to collect: harvest, ports, tolls, markets, mines. Tax capacity depends on literacy, roads and administration.
9. **Wealth classes and factions.** Who owns land, ships, mines, credit, monopolies, labour. Faction income, expenses, armies and debts must balance (the optional `faction_economy` field on the faction, defined in `assets/templates/factions/_schema.yaml`).
10. **Conflict.** Scarcity, tariffs, debt, blockades, resentment of extractive contracts, and competition for routes and mines drive wars and unrest. Then loop: conflict is an event that alters steps 2 to 9 (see `impact-chains.md`).

## Heuristics you can check (full tables in `references/heuristics.md`)

- Food: one adult eats about 250 to 350 kg grain-equivalent a year. A city of 10,000 needs 3,000 to 3,500 tonnes a year.
- Farm share of population: foraging-to-iron-age farming 85 to 95 percent; medieval 75 to 85; early modern 60 to 75; early industrial 35 to 55; industrial 5 to 25; modern under 5. Urban share roughly equals the farmers' surplus ratio (80 percent farmers means about 10 to 15 percent in towns and cities).
- Transport cost ratio, cheapest first: sea 1, river or canal 3 to 6, rail 2 to 5 (once built), cart road 25 to 50, porter or pack 60 to 150. Bulk staples (grain, timber, stone, ore, coal) pay off only by water or within about 50 km by land; only high value-per-weight goods (spice, silk, gems, drugs, books, fine metal, information; magical reagents only if the gate allows) cross continents by land.
- Price cap: a lasting price gap between two markets cannot exceed transport + tolls + risk premium + merchant margin unless something blocks arbitrage (monopoly, blockade, ban, war, guild closure). If you want a bigger gap, name the blocker.
- Tax capacity: pre-modern states take 5 to 15 percent of output; strong bureaucracies 15 to 25; tolls and tariffs 2 to 10 percent per jurisdiction; income tax and welfare states need modern records.
- Armies: a pre-modern state can sustain a standing force of about 1 percent of its population, 2 percent briefly, militias of 5 to 10 percent for a short season. This skill owns these numbers; `peoples` points here. A soldier costs about 3 to 5 times a labourer's subsistence.
- Money: a currency is anchored to a daily wage (say what an unskilled day buys). Debasement happens when expenses exceed revenue; inflation needs a cause (debasement, bullion inflow, supply shock, labour loss, war finance).

## Procedure (every time)

1. **Read first.** Read `project.yaml` (world flags: technology, magic, spaceflight, population scale; calendar and eras), `world/economy.yaml` if present, the locations involved and their parent chain, routes and transport systems, species diets and populations, the factions involved, and events that already touch these (`economic_impact` strings). If the user names a place, read it and its neighbours before proposing anything.
2. **Find the gap.** Ask of the area: what do people eat, who grows it, how does it arrive? What does each producer need as input and where does it come from? Where does each product go? Who profits, who taxes, who pays?
3. **State the cause in one line** for each economic fact you add ("Port X trades timber for grain because X has forest and no arable land; route is by river because carts cost 10 times as much"). If you cannot, change the idea or add the missing cause first.
4. **Define the entity** using the existing template fields (`references/entity-fields.md`). Use slugs for every reference to a location, faction, event, species.
5. **Write the consequences into every affected entity.** A route is edited on both endpoints' `routes` (location shape: `to`, `methods[].mode`) and in the economy file (`trade_routes`: `from_location`, `to_location`, `mode`, same mode enum); a resource appears under the producing location's `resources` and in every consumer's needs; a tax or tariff appears in the controlling faction's `faction_economy.income_sources` and in the payers' `expenses`; a shock is an event whose `economic_impact` is a short prose string naming the location, resource and faction slugs, plus a `shocks` entry in `world/economy.yaml` keyed by that event slug (structured `production_effects`, `trade_effects`, `wealth_transfers`, `price_effects`), the affected production entries get a `status` and `disrupted_by`, and the affected trade_routes entries get a `status`.
6. **Balance the books.** Check food, labour, army, tax and trade totals with `heuristics.md`. Show the arithmetic in the machine description or notes.
7. **Sweep.** Does it change settlement, population, migration, politics, language, culture, law? Edit those, or say what was deliberately left unchanged and why (`causality.md`).
8. **Validate**: run the `world-validate` skill and fix findings.

## Deriving prices and flows without maths

Do this per good, qualitatively:

1. Where is it cheapest (source) and where is it dearest (far from source, high demand, or taxed)?
2. Which mode connects them, and is the cost of moving it less than the price gap? If not, it does not move that way.
3. What comes back? Prefer a return cargo (an empty backhaul doubles the cost of the route). A route with goods in one direction only needs a stated reason (pilgrims, tribute, fuel supply, ballast, tied contract).
4. Who controls the choke point (strait, pass, river mouth, jump gate), and what do they charge?
5. Write the price as a relation ("grain at Port X costs about 3 times its price at the delta, which is why the city taxes the grain fleet") and use `base_value` per currency, keeping the anchor wage consistent.

Price levels also follow wealth: luxuries are bought where elites live; staples are bought where population is dense; strategic goods are bought where wars are fought or expected.

## Propagating shocks

Every shock is an event with a prose `economic_impact` string; the structured price, route and flow effects go in the economy file under `shocks`. Trace in the order: production (effect on source) then route (effect on flow) then price (effect at each end and on substitutes) then wealth (who gains, who loses, who defaults) then population (hunger, migration, deaths, labour shortage) then politics (unrest, tax change, war) then culture (cuisine, proverbs, language borrowings). Load the sibling skills when you cross layers:

- `history-and-events`: record the shock as an event, fill `caused_by`, `leads_to`, consequences and dates; recoveries are later events.
- `geography-and-climate`: if the cause is drought, flood, ice, harbour silting, a river changing course, or a new mine or strait; and to place producers, ports and passes correctly.
- `peoples`: if diet, taboo, labour, migration, caste, or species traits shape demand or supply.

Details and the full list of shock templates (embargo, blockade, war, plague, new route, new technology, climate shift, resource depletion, debasement, tariff change) are in `references/impact-chains.md`.

## Anti-patterns (reject or repair)

- A resource that no location produces, or a producer whose own inputs come from nowhere.
- A city or army with no food supply: no farmland in its catchment, no river or sea route for imports, and no import line in any route.
- Gold-standard or silver-coin fantasy with no mines, no import route and no explanation of who minted it.
- A trade route with goods in one direction only, or goods that cost more to carry than the price gap pays, or a route nobody profits from or controls.
- Bulk goods crossing a continent by cart; luxuries ignored in favour of staples; every location producing everything.
- Endless wealth: a faction with income that does not match its army, buildings and population; treasuries that never shrink.
- Prices that stay static after a war, famine, plague, blockade or new route.
- Magic or technology that ignores economics: free food, transmutation or teleportation with no effect on prices, jobs, guilds, taxes or military logistics; a labour-saving invention with no displaced workers.
- A single currency used everywhere with no exchange, minting or trust story; coins whose metal is not mined or traded.
- Economic facts that never reach the people: no wages, no rents, no hunger, no debt, no black market.
- Ports, passes and bridges with no toll or controlling faction.
- Guilds or companies with no legal basis, no members' interest, no rival.

## Checklist before finishing

- [ ] Every resource has at least one producer location with a stated cause (climate, geology, tech).
- [ ] Every settlement with significant population has a food source and a route or catchment for it.
- [ ] Every route has endpoints reciprocated in both locations' `routes`, a transport mode that fits terrain and flags, goods flowing for a reason, and a controlling faction or open status.
- [ ] Price gaps are explained by transport, tolls, risk or a named blocker.
- [ ] Currency: metal or backing has a source; issuing authority exists; accepted areas fit the faction's reach; anchor wage stated.
- [ ] Faction income, expenses, army and debts are plausible together; tax rates match administrative capacity.
- [ ] Any shock has an event with an `economic_impact` string and a `shocks` entry, and affected production nodes and routes have updated status.
- [ ] Technology and magic used by the economy are allowed by the world flags (magic gate included) and have costs.
- [ ] Both sides of every reference written; consequence sweep done across settlement, politics, culture, language.
- [ ] Run the `world-validate` skill and report the result honestly.
