# Economic heuristics

Rules of thumb with real-world anchors. They are for plausibility, not simulation: stay within a factor of about two unless the world gives a stated reason (magic, alien biology, different gravity). Always check the world flags (`technology.*`, `magic.*`) in `project.yaml` first. Always state which tech tier you are using.

## 1. Food

| Quantity | Rule of thumb |
|---|---|
| Adult human need | 2,000 to 2,500 kcal a day; about 250 to 350 kg grain-equivalent a year including waste |
| Non-human species | Scale by body mass and metabolism from `species` entities; if diet is unusual (minerals, blood, light, aquaculture), name the staple and its source |
| Cereal yield, pre-modern | 600 to 1,200 kg per hectare (seed return 3 to 6 to 1); irrigated rice or river-flood farming 1,500 to 3,000; modern 5,000 to 9,000 |
| Land per person | Medieval three-field: about 0.7 to 1.2 ha cropped per person (more with fallow and poor soil); intensive rice or garden farming 0.2 to 0.4 |
| Pastoral | Meat and milk give roughly a tenth of the calories per hectare of cereal; herders need 5 to 20 times the land and stay mobile or depend on trade for grain |
| Fishing and aquaculture | Coastal fishing can feed dense ports but is seasonal; ponds and aquaculture rival intensive crops |
| Storage | Grain keeps 1 to 3 years in dry stores; fresh produce, fish, meat days to weeks without salt, smoke, cold or drying |
| Famine trigger | A harvest 30 percent below normal in a region with no import route; below 50 percent is mass death |
| Fuel | Cooking and heating need about 1 to 2 tonnes of wood per household a year; cities deforest their hinterland within 50 to 100 km without coal, peat, or water transport |

## 2. Farm share and surplus by tech level

| Tier | Share of workers in farming | Typical urban share | Notes |
|---|---|---|---|
| Neolithic or tribal | 90 to 100 | under 2 | Chiefs and priests live on tribute |
| Bronze or iron age, medieval | 75 to 90 | 5 to 15 | Large cities (over 50,000) need river or sea supply |
| Early modern (printing, gunpowder, global ships) | 60 to 75 | 10 to 25 | Credit, joint-stock companies, colonial staples |
| Early industrial (steam, rail) | 35 to 55 | 25 to 50 | Rail and steamships break the food radius |
| Industrial | 10 to 25 | 50 to 75 | Fertiliser, machinery |
| Modern or post-industrial | under 5 | 75 and up | Food a small share of cost |
| Spacefaring or arcology | any; state food source explicitly (hydroponics, aquaculture, synthesis, imports) | any | Water, air, energy become the "grain" |

Population growth rates and dialect or language timescales are owned by the `peoples` skill (`references/quantities.md`); use those.

Surplus ratio: one farm family feeds itself plus S other families; urban plus elite plus soldier share is roughly S/(1+S). If 80 percent farm, S is 0.25 and at most about 20 percent can be non-farmers, most of them rural craftsmen; towns hold 5 to 10 percent.

Needed for: a city of 10,000 needs about 3,000 to 3,500 tonnes of grain a year, from roughly 4,000 to 6,000 hectares of cropped land (a circle of about 15 km radius by cart, if all of it is cropped). A city of 100,000 cannot be supplied by land carriage alone; it needs a river, sea, canal or rail line.

## 3. Transport

Relative cost per tonne-km, sea = 1 (Roman-era and medieval ratios, which hold as order of magnitude):

| Mode | Relative cost | Speed | Capacity |
|---|---|---|---|
| Sea (sail) | 1 | 100 to 200 km/day with favourable winds; seasonal | 50 to 1,000 tonnes |
| River or canal barge | 3 to 6 | downstream 40 to 60 km/day; upstream 10 to 20 | 20 to 200 tonnes |
| Rail (steam or better) | 2 to 5 (after capital cost) | 300 to 800 km/day | trainloads, thousands of tonnes |
| Ox or horse wagon on road | 25 to 50 | 15 to 25 km/day | 0.5 to 1.5 tonnes |
| Pack animal | 60 to 150 | 20 to 30 km/day | 100 to 200 kg (camel 200 to 300) |
| Porter | 150 and up | 15 to 25 km/day | 25 to 40 kg |
| Space, FTL, portal, teleport | set by the flag; state fuel, capacity and toll | | |

Rules:
- Overland grain roughly doubles in price per 300 to 500 km of cart haulage (Diocletian price edict ratio). Seaborne grain barely moves price over thousands of km.
- Each border, toll or customs point adds 2 to 10 percent; piracy or banditry adds an insurance premium of 5 to 20 percent or forces convoys and escorts.
- Mountains, deserts, swamps and winter close routes or raise cost by a factor of 2 to 5.
- Caravans and ships move on schedules (monsoon, ice, harvest); `status: seasonal` fits.
- A magical or FTL mode must have its own cost, capacity, speed and chokepoints; "free teleportation" collapses the whole price model and must be justified, taxed, rationed or made dangerous.

## 4. Comparative advantage and why a route exists

A route exists when the delivered price of at least one good at the far end exceeds its price at origin plus cost, tolls, risk and margin. Ask per good:

1. Source cheap? (climate, ore body, cheap labour, scale, knowledge monopoly)
2. Distant demand high? (no local production, richer buyers, elites, military need, ritual need)
3. Value per weight enough to bear the mode? (rule: freight should be under about a third of the delivered price for stable trade)
4. Return cargo? (usually a different good; otherwise the route pays double)
5. Is there a barrier that explains an unusually large gap? (monopoly, blockade, ban, guild, patent, secret technique, state-owned strategic good)

Even a place that produces everything worse still exports something it is relatively best at (comparative advantage): fine labour, ship services, banking, passage, pilgrimage, information, mercenaries.

## 5. Prices

- Price at market = production cost near source; far from source = source price + transport + tolls + risk premium + merchant profit (5 to 30 percent).
- Scarcity (blockade, bad harvest) raises price roughly by the supply shortfall times 2 to 3 for staples (a 30 percent shortfall can double grain prices), less for goods with substitutes.
- Luxuries: price 10 to 1,000 times source cost is possible because freight is small versus value, but demand depends on rich buyers.
- Anchor: state what a day's unskilled labour buys (for example 3 to 4 kg of bread grain; or one loaf and a bed). All prices are then multiples of that.
- Wages: skilled worker 1.5 to 3 times unskilled; soldiers about 1.5 to 3 times; scholars, priests vary.
- Rent and land: land is cheap where population is thin and dear near ports and rivers.

## 6. Money and credit

| Type | Needs | Failure mode |
|---|---|---|
| Barter or commodity money (salt, cattle, grain, cacao, shells) | Little | Hard over distance; local only |
| Metal coin (copper, silver, gold) | Mines, import, or plunder; a mint; trust | Debasement, clipping, shortage of small change |
| Paper, scrip, notes | Issuing authority with legal force, literacy, trust | Over-issue and inflation; run on the issuer |
| Credit, bills of exchange, ledgers | Literate merchants, courts, reputation networks, long-lived banks | Defaults cascade; banks fail when sovereigns default |
| Digital or reputation currency | Computing, networks, strong identity | Capture by whoever controls the network |
| Magic or mana currency | Rules in `magic-systems` that give it a scarce, measurable source | If creation is easy, value collapses |

Rules:
- Silver-to-gold value ratio historically about 10 to 15 to 1; copper trades in tiny value. Keep denominations at 1 : 10 or 1 : 12 style steps and say which coin buys what (copper for bread, silver for wages, gold for merchants and states).
- Money supply grows with mining, trade surplus, plunder or paper issue; it shrinks with hoarding, export of coin to pay for imports (for example to a distant luxury trade), and bullion shortage.
- Debasement (reducing precious metal in the coin) is a state response to deficit, usually in wartime; effect: prices rise after a lag of a few years, foreign merchants refuse the coin, a stable alternate coin spreads. A reform is an event with winners and losers.
- Inflation causes: debasement, bullion inflow, supply shock (famine, blockade), labour loss from plague (wages rise), war finance. Deflation: bullion drain, tight credit, hoarding.
- Exchange rates follow metal content and trust, plus a fee of 1 to 5 percent for the changers.
- Seigniorage: mints keep a few percent of metal; issuing authority gets income.

## 7. Taxation and institutions

| Source | Typical rate or share | Needs |
|---|---|---|
| Land or harvest tax, tithe | 5 to 20 percent of crop | Surveys, local officials or landlords |
| Poll or hearth tax | small per head | Census |
| Tolls and tariffs | 2 to 10 percent per jurisdiction | A chokepoint and force to hold it |
| Market and sales dues, licences | 1 to 5 percent | Market towns |
| Monopolies (salt, tobacco, spices, alcohol) | large | Control of production or entry |
| Tribute, plunder, conquest | variable | Superior force |
| Seigniorage | few percent of coin | Mint |
| Income and corporate tax | 10 to 40 percent | Literate administration, banks, modern records |

A state that tries to collect more than its administration can enforce gets evasion, smuggling and revolt. Collection cost is 5 to 30 percent of what is collected, pre-modern.

Army sizing (pre-modern): sustainable standing force about 1 percent of population (2 percent for a short time); levy or militia for a season 5 to 10 percent; cost per soldier 3 to 5 labourer-subsistence incomes (pay plus food, fodder, kit). An army of 30,000 for a campaign needs about 50 to 60 tonnes of food a day plus fodder for animals; beyond about 50,000 it cannot live off the land, only by sea or river supply or in friendly rich country. Fleets cost more than armies per head. Magic or tech armies still eat and need logistics.

Institution examples: guilds (limit entry, set quality and prices, fund their members; need a town and a legal charter); merchant companies and leagues (pool capital and risk, get privileges, own fleets, often raise private forces; need long routes with high margins); temples (tithes, land, banking, charity); states (tax, army, courts, mint); clans or families (land, marriage alliances); criminal syndicates (smuggling where tariffs are high).

## 8. Wealth classes

Pre-modern: top 1 to 5 percent (landed elite, merchants, clergy, officials) hold 30 to 50 percent of wealth; 10 to 20 percent artisans and traders; 75 to 85 percent peasants and labourers near subsistence. Middle class grows with trade, credit, literacy and cities. Slavery or bonded labour exists where labour is cheap to coerce and output valuable; it needs a source of slaves (war, debt, raid) and a market; say so. Industrial worlds add a wage proletariat, owners, and organised labour.

Faction wealth must reconcile: income (taxes on a named base, rents, tariffs on a named route, production) minus expenses (army per above, administration, building, debt service) equals treasury change. Use the base `wealth_level` bands in `references/economy.md` and stay consistent with the world's currency anchor.

## 9. Production

- Iron: 1 tonne of pre-industrial iron needs roughly 5 to 10 tonnes of charcoal (about 20 to 50 tonnes of wood) and 3 to 5 tonnes of ore; smelting sites cluster by forest, ore and water. Coal or coke changes this; state when.
- Mines: grade, depth and water set cost; deep mines need pumps and ventilation (technology.steam_power or magic); mines deplete over decades to centuries (`status: depleted`).
- Textiles: wool or flax from farms, spinning (slow without machines), weaving, dyeing (mordants and dyes can be strategic).
- Shipbuilding needs timber, pitch, iron, rope and a shipyard town near all of them.
- Salt: needed by every community for diet and preservation; sources are sea evaporation, brine, mines; always trade it or produce it.
- Each producer's own inputs are demands elsewhere; trace one level of inputs for every major product.
- Population limits: the labour force is about 40 to 50 percent of population; a mine of 1,000 workers sustains 4,000 to 5,000 residents who must be fed.
