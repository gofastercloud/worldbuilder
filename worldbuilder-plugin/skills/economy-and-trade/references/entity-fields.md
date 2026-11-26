# Defining economic entities

Base field names are from `references/economy.md` and `assets/templates/economy/_schema.yaml`. They live in `world/economy.yaml` (currencies, resources, production, trade_routes, rules) and in the metadata of faction, location and event files (`faction_economy`, `economic_impact`, `resources`, `routes`). Refer to locations, factions, resources, events and species by their slug. The example `assets/example-the-lattice/world/economy.yaml` is the model.

## Known gaps in the base schema, and how to close them

The base schema is sound but permits holes. Close them with these additive, optional fields (they extend, not replace; most are now in the schema). Check that `world-validate` still passes after adding them; keep them tidy.

| Gap | Add |
|---|---|
| Resources list no source or consumers | resource (these are now optional schema fields): `sources` (list of location slugs, mirrors `production`), `consumers` (list of location, faction or species slugs), `substitutes` (resource slugs), `inputs` (resources needed to produce it) |
| Route has no mode, distance or cost reason | route: `mode` (same enum as `methods[].mode` on a location route), `via` (list of location slugs, including chokepoints), `distance`, `travel_time` (same strings as a location method), `cost_note` (why this route pays). These are now in the schema; `transport_mode`, `transport_route` and `chokepoints` are not used |
| Production has no inputs | production: `inputs` (resource slugs and amount), `caused_by` (a climate, geology or event slug) |
| Currency has no backing | currency: `backing` (commodity, metal, decree, reputation, none), `anchor` (what a day's unskilled labour buys), `status` (stable, debased, collapsing) in the schema; `metal_sources` and `mint` (location slugs) as free extras |
| Market has no home | market: see below |
| Institution fields unspecified | institution: see below |
| Categories used outside the enum (the example uses `essential`, `technology`, `finished-goods`, `scientific`) | Use the schema enum (`raw-material`, `food`, `luxury`, `strategic`, `magical`, `knowledge`, `labor`, `currency`, `fuel`, `custom`) and put the specific kind in `tags`; use `custom` with a tag if nothing fits |
| Rarity `varies` | Use the enum value that fits the main source |

## Resource (good)

Required: `name`, `category`. Also: `aliases`, `rarity`, `base_value` (state the currency and unit; relative to the anchor wage), `unit`, `perishable`, `requires_tech` (a world flag name such as `steam_power`, or `mining`), `tags`.
Plus the extension fields above. **On a location**, a resource is a string or the one shared object `{name, category, rarity, notes}` with these same enums (`name` = the resource slug). The geography vocabulary `kind` and `abundance` is not used; see the mapping in `economy/_schema.yaml`. Test: can you name a place that produces it (`production` entry), a place that wants it, and a route or mode that moves it? If not, it is not finished.

## Producer (production node)

Fields: `resource` (slug), `location` (slug), `output` (rate with unit and period, or share of world supply), `quality`, `labor_source`, `status`, `disrupted_by` (event slugs). Rules: output must be consistent with the labour and land (see heuristics); `status` changes with events (set `disrupted`, `destroyed`, `depleted`, `seasonal`, `new` and list the event); the producing location should list the resource in its own `resources`; the resource's cause (climate, geology, technique) should be visible in the location's description.

## Consumer

There is no separate schema. A consumer is a location (population, industry), faction (army, court, guild), species (diet), or magic-system (reagents). Record demand as: the resource under the consumer's `resources` needs (or `consumers` on the resource), a route `goods` entry carrying it in, and a `faction_economy.expenses` line. For a city, food is mandatory: state its staple and where it comes from (local catchment, or a named route).

## Trade route

Required for sense: `name`, `from_location`, `to_location` (both slugs), `goods` (each `resource`, `direction`: outbound is from to to, inbound is to to from, both; `volume`), `mode` (a value of the location `methods[].mode` enum; add `transport_system` to name a transport file), `annual_value`, `controlled_by` (faction slug), `tariff`, `status`, `risks`. Rules:
- Add the route to both locations' `routes` lists (shape: `to`, `methods[]` with `mode`, `distance`, `travel_time`; the mode and distance must agree with the economy entry) (and update the location `transport_hub` where relevant).
- The goods list must pass the profit test in `heuristics.md` section 4 in at least one direction, and normally offers a return cargo.
- Annual value should equal the sum of volumes times delivered prices, and tariff income to `controlled_by` should equal tariff times that value; show the number.
- Status must reflect current events (`blockaded`, `disrupted`, `new`, `seasonal`).
- A route crossing a chokepoint names who holds it.

## Market

A market is a location (a town, a bazaar, a port, a station) where several routes meet. Mark with tags `market` or `port` and, in the location's body or `descriptions.machine`, list: staples sold, specialities, which routes feed it, who licenses it, dues. If the world needs structured data, add under the location: `market: { goods: [...], dues: "...", licensed_by: faction-slug, routes: [...] }`. A market with no feeding route is a village.

## Currency

Fields: `name`, `symbol`, `denominations` (each `name`, `value` relative to the base unit, `material`), `issuing_authority` (faction slug), `accepted_in` (location slugs), `exchange_rates` (`currency`, `rate`), plus `notes` and the extension fields. Rules: denominations with a physical material need that material produced or imported (a mine, an import route); `accepted_in` reflects the authority's reach; at least one exchange rate or a statement that none is accepted abroad; mention debasement, forgery or fixed supply; `rules.primary_currency` names one of the defined currencies.

## Institutions (guild, company, state, temple, league)

These are `faction` entities with `type` (guild, company, state, temple, league, syndicate) plus the optional `faction_economy` block (defined in `assets/templates/factions/_schema.yaml`) (`wealth_level`, `income_sources` with `source`, `amount`, `reliability`, `expenses` with `category`, `amount`, `treasury`, `debts` with `creditor`, `amount`, `due`, `economic_strategy`). Add in the body:
- Legal basis (charter, treaty, conquest, custom).
- Members and what each gets.
- What it controls (production, route, market, currency, credit, entry to a trade).
- Revenue basis and who pays (name the payers; add the matching expense to their entries).
- Rivals and the conflict the privilege causes.
- Weakness (dependency on one resource, one route, one patron, debt).
Guild: sets quality, apprentice numbers and prices, needs towns; companies and leagues need long-distance margins; a state needs agriculture and tolls to support its army.
For `rules`: `guild_system`, `monopolies` (names and holder), `banking_exists`, `taxation` (sources and rates), `slavery_exists`, `black_market`, `barter_common`, `magical_economy` (only if `world_flags.magic.present`; with a note on cost).

## Event economic impact

The event keeps `economic_impact` as a prose STRING (events schema), short, naming the location, resource and faction slugs. The structured effects live in the economy file under `shocks`, one entry per event slug: `production_effects` (`location`, `resource`, `change`, `duration`), `trade_effects` (`route`, `change`, `duration`), `wealth_transfers` (`from`, `to`, `amount`, `reason`), `price_effects` (`resource`, `change`, `location`). For any significant event that touches the economy fill the lists that apply, and add the reverse changes to the affected production nodes (`status`, `disrupted_by`), routes (`status`) and factions (`faction_economy`).
