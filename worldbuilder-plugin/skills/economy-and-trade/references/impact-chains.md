# Impact chains

Use this when something changes the economy. Write the change as an event (load `history-and-events`) with a prose `economic_impact` string, then record the structured effects in `world/economy.yaml` under `shocks` and update every affected entity. General order: production, route, price, wealth, population, politics, culture. Name the duration of each effect and the recovery path; effects fade, adapt, or become permanent.

## Method

1. Identify the node hit: a producer, a route, a chokepoint, a currency, a faction's income, a population.
2. List the directly dependent nodes: who consumed this output, who used this route, who borrowed from this faction.
3. For each, ask: is there a substitute (another producer, another route, another good)? If yes, the shock is cheaper but flows re-route and prices shift by the extra cost. If no, shortage and price spike.
4. Compute the size qualitatively with `heuristics.md`: size of lost flow versus total supply; extra cost of the detour; size of the budget gap.
5. Trace second-order effects: hunger, unemployment, defaults, migration, tax shortfalls, army pay, unrest.
6. Mark who gains (rival producers, smugglers, shipbuilders, neighbours with stockpiles) as well as who loses.
7. Decide the duration and write recovery or permanent change as later events or status changes.

## Shock templates

| Shock | Primary effect | Typical chain | Siblings to load |
|---|---|---|---|
| Embargo or tariff hike | Flow of named goods falls by the share the embargo covers; smuggling and re-routing begin | Importers face price rise (plus smuggling margin); exporters lose income; targeted faction seeks substitutes or breaks the embargo; third parties profit as transshippers | `history-and-events` |
| Blockade or siege | Route `blockaded`; city starves over weeks to months depending on stores | Price spike at the blockaded end, collapse at the cut-off producer end; relief convoys, surrender, or sortie | `history-and-events` |
| War | Production in the war zone `disrupted` or `destroyed`; labour drained to the army; taxes up; coin debased or loans taken | Inflation after a lag; debts to merchants and banks; post-war reparations (wealth transfer); veterans and refugees migrate | `history-and-events`, `peoples` |
| Plague or famine | Labour and demand fall; each death removes a worker and a consumer | Wages rise for survivors, rents fall, land consolidates, labour-saving methods and unrest; trade networks carry the disease along routes | `peoples`, `geography-and-climate` |
| New route (discovery, canal, rail, pass, jump lane) | Cost of one link falls; new goods become viable; old routes lose traffic | Port or town on the new line grows; old transit towns decline; tolls move; empires fight to control it; price gaps shrink toward the new cost | `geography-and-climate`, `history-and-events` |
| New technology (plough, mill, ship type, deep-mine pump, rail, AI, FTL) | Cost of one step falls or a new good appears | Workers displaced or demand for new skills; guilds resist; output and surplus rise (so population and cities rise after a generation); whoever holds the technology gains; if the flag was previously false, record it in `project.yaml` first | `history-and-events`, `peoples` |
| Climate shift (drought, cold spell, shifting monsoon, sea level) | Yield falls by a percent (see famine trigger); fisheries and rivers change | Harvest failures, migration, rise of food imports, new settlements elsewhere; ports silt up or flood; conflict over water and grazing | `geography-and-climate`, `peoples` |
| Resource depletion or discovery | A mine or forest exhausts or a new field opens | Towns boom and fail; price of the resource moves; coinage or fuel supply changes; migration | `geography-and-climate` |
| Debasement or currency reform | Coin value falls or is restored | Prices rise after a lag of one to a few years; foreign coin preferred; creditors lose, debtors gain; reform leaves hoarders and the poor hurt | `history-and-events` |
| Monopoly or guild privilege granted or broken | Entry and price of a good change | Rents flow to holder; excluded traders smuggle or relocate; breaking it lowers price and raises output but harms holders | `history-and-events` |
| Magic discovery or loss (only when the magic gate allows magic) | If magic changes a cost (food, transport, building), treat it as a technology shock; if magic is lost, the reverse | Magical goods spike, mundane substitutes rise; magic users become a class; check `magic-systems` cost | `history-and-events`, `peoples` |

## Writing it down

For each shock, make these edits (a sweep list, not optional):

- Event: `caused_by`, `leads_to`, consequences, dates, and `economic_impact` as a prose string naming slugs (use `open_ended` only for effects still unfolding today). Do not put lists or objects in the event.
- Economy file: one `shocks` entry keyed by the event slug with `production_effects`, `trade_effects`, `wealth_transfers` and `price_effects` (fill those that apply).
- Production nodes: `status`, `disrupted_by`, adjusted `output`.
- Routes (`trade_routes`): `status`, `goods` (changes to volume or direction), `controlled_by` if control moved, both endpoints' `routes`.
- Factions: `faction_economy` income, expenses, treasury, debts; `wealth_level` if a band changed; allies or enemies if politics moved.
- Locations: population, `resources`, settlement changes, migration in or out.
- Species and cultures: diet, occupation, attitudes, language borrowings.
- Currency: `status`, `exchange_rates`.
- Later events: recovery, adaptation, secondary conflict (`leads_to`).

## Checks on the result

- Nobody ends richer without a source for the gain; wealth moves, it is not created (except by real productivity gains, which need a technology or trade cause).
- Prices move in the direction and rough size predicted by the lost supply and the substitute's extra cost.
- The affected region's food, army and tax budgets still balance.
- Anything lasting more than a few years has a recovery or permanent-change story.
