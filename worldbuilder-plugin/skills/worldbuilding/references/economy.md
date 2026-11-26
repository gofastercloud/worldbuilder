# Economy System Reference

Models economic systems: resources, production, trade routes, currencies, faction wealth, event impacts.

## Architecture

Economy built from three layers:

1. **Resources** — What exists (iron, grain, mana crystals, labor)
2. **Production** — Which locations produce/consume what
3. **Trade** — How goods flow via transport routes

Economic state changes via events (wars destroy production, plagues reduce labor, discoveries open routes).

## Resource Definition

**Required:** name, category

| Field | Type | Options | Notes |
|-------|------|---------|-------|
| name | string | — | Resource name |
| aliases | list | — | Alternative names |
| category | enum | raw-material, food, luxury, strategic, magical, knowledge, labor, currency, fuel, custom | Resource type |
| rarity | enum | abundant, common, uncommon, rare, very-rare, unique | How scarce |
| base_value | string | — | Baseline value in primary currency |
| unit | string | — | Measurement (bushels, ingots, barrels, tons) |
| perishable | boolean | — | Does it spoil? |
| requires_tech | string | — | Tech flag needed to exploit (e.g., "mining" for deep ores) |
| tags | list | — | Searchable metadata |

**Category Meanings:**

| Category | Examples | Properties |
|----------|----------|-----------|
| raw-material | Iron ore, timber, stone, clay | Abundant, non-perishable, requires labor |
| food | Grain, livestock, fish, fruit | Often perishable, seasonal |
| luxury | Silk, spices, gems, perfume | Rare, high value, low volume |
| strategic | Weapons, armor, ships, siege equipment | Valuable, often monopolized |
| magical | Mana crystals, enchanted materials, reagents | Rare, high value, special handling |
| knowledge | Books, scrolls, maps, research | Unique, non-consumable |
| labor | Skilled workers, slaves, mercenaries | Variable cost, renewable |
| currency | Gold, silver, trade tokens | Standard of value |
| fuel | Coal, oil, mana, wood | Consumable, essential |
| custom | User-defined | — |

## Production Node

Each location can have multiple production entries.

| Field | Type | Options | Notes |
|-------|------|---------|-------|
| resource | ref | → resource | What's produced |
| location | ref | → location | Where it's made |
| output | string | — | Production rate (e.g., "500 bushels/year") |
| quality | enum | poor, standard, fine, exceptional, legendary | Output quality tier |
| labor_source | string | — | Who works it (guilds, slaves, machines, magic) |
| status | enum | active, disrupted, destroyed, depleted, seasonal, new | Current operational state |
| disrupted_by | list | → events | Events that affected it |

**Status Meanings:**
- **active** — Full production
- **disrupted** — Reduced output (war, plague, shortage)
- **destroyed** — Damaged, may be repaired
- **depleted** — Resource exhausted, not recoverable
- **seasonal** — Only produces certain times of year
- **new** — Recently established

## Trade Route

Overlays on transport routes with economic data.

| Field | Type | Options | Notes |
|-------|------|---------|-------|
| name | string | — | Route name (e.g., "Valdris-Library Road") |
| from_location | ref | → location | Origin |
| to_location | ref | → location | Destination |
| transport_route | string | — | Which transport mode(s) it uses |
| goods | list | resource, direction, volume | What flows and how much |
| annual_value | string | — | Estimated annual trade value |
| controlled_by | ref | → faction | Who controls/taxes it |
| tariff | string | — | Tax rate (e.g., "10%" or "2 silver per unit") |
| status | enum | active, disrupted, blockaded, destroyed, seasonal, new | Route operational status |
| risks | list | — | Bandits, pirates, monsters, weather |

**Goods.direction:** outbound (from → to), inbound (to ← from), both (bidirectional)

**Route Status:**
- **active** — Fully operational
- **disrupted** — Temporarily blocked or slow
- **blockaded** — Intentionally blocked by faction
- **destroyed** — Roads/bridges destroyed, out of service
- **seasonal** — Only passable certain times of year
- **new** — Recently opened

**Example goods entry:**
```yaml
- resource: grain
  direction: outbound
  volume: "500 bushels/year"
```

## Currency

Defines what medium of exchange exists.

| Field | Type | Options | Notes |
|-------|------|---------|-------|
| name | string | — | Currency name (e.g., "Crown") |
| symbol | string | — | Symbol (e.g., "₵") |
| denominations | list | name, value, material | Coin/note types |
| issuing_authority | ref | → faction | Who mints/controls it |
| accepted_in | list | → locations | Where it's valid |
| exchange_rates | list | currency, rate | How it converts to others |

**Denomination structure:**
```yaml
- name: "gold crown"
  value: 100       # relative to base unit
  material: gold
```

**Example exchange rates:**
```yaml
- currency: "Valdrian Crown"
  rate: 1.0
- currency: "Northern Mark"
  rate: 0.85
- currency: "Merchant Token"
  rate: 0.5
```

## Faction Economics

Added to faction metadata to track economic power.

| Field | Type | Options | Notes |
|-------|------|---------|-------|
| wealth_level | enum | destitute, poor, modest, comfortable, wealthy, rich, vast, incalculable | Economic tier |
| income_sources | list | source, amount, reliability | Where money comes from |
| expenses | list | category, amount | Where money goes |
| treasury | string | — | Current cash reserves |
| debts | list | creditor, amount, due | Outstanding debts |
| economic_strategy | string | — | Wealth approach (hoarding, investing, military, etc.) |

**Wealth Levels:**
| Level | Annual Income | Typical | Notes |
|-------|--------------|---------|-------|
| destitute | <100 gold | Refugees, exiles | Survival only |
| poor | 100-1K gold | Rural villages | Limited resources |
| modest | 1K-10K gold | Towns, minor nobles | Comfortable living |
| comfortable | 10K-50K gold | Cities, regional powers | Significant wealth |
| wealthy | 50K-500K gold | Large cities, major factions | Economic influence |
| rich | 500K-5M gold | Major powers, kingdoms | Major influence |
| vast | 5M-50M gold | Empires, major leagues | Continental influence |
| incalculable | 50M+ gold | Gods, ancient powers | Beyond measurement |

**Income Source reliability:**
- **unstable** — Varies wildly (depends on random events)
- **seasonal** — Predictable but varies by season
- **steady** — Consistent year-to-year
- **guaranteed** — Certain, backed by law/force

**Example faction economics:**
```yaml
wealth_level: wealthy
income_sources:
  - source: "Tariffs on Valdris-Library Road"
    amount: "50K gold/year"
    reliability: steady
  - source: "Mining operation (silver)"
    amount: "30K gold/year"
    reliability: steady
  - source: "Military contracts"
    amount: "20K gold/year"
    reliability: unstable
expenses:
  - category: "Standing army (500 soldiers)"
    amount: "60K gold/year"
  - category: "Infrastructure maintenance"
    amount: "15K gold/year"
  - category: "Salaries and administration"
    amount: "10K gold/year"
treasury: "200K gold"
debts:
  - creditor: "The Banking Consortium"
    amount: "50K gold"
    due: "In 2 years"
economic_strategy: "Military expansion — investing surplus in conquest"
```

## Event Economic Impact

Added to event metadata to track how events affect the economy.

| Field | Type | Options | Notes |
|-------|------|---------|-------|
| production_effects | list | location, resource, change, duration | How production changes |
| trade_effects | list | route, change, duration | How trade routes change |
| wealth_transfers | list | from, to, amount, reason | Wealth flowing between factions |
| price_effects | list | resource, change, location | Price changes |

**Production change types:**
- **destroyed** — Production completely halted (may never recover)
- **halved** — Output cut to 50%
- **disrupted** — Reduced, timeline uncertain
- **reduced** — Reduced by X% for duration
- **unchanged** — No effect
- **increased** — Boosted
- **doubled** — Output × 2
- **new** — New production opened

**Trade route change types:**
- **destroyed** — Routes physically destroyed
- **blockaded** — Intentionally blocked (can be cleared)
- **disrupted** — Partially blocked, slow
- **rerouted** — Must take alternate path
- **unchanged** — No impact
- **opened** — New route available
- **expanded** — Existing route improved/faster

**Price change types:**
- **crashed** — Worth 10-25% of normal
- **dropped** — Worth 50% of normal
- **stable** — Normal price
- **rose** — Worth 150% of normal
- **spiked** — Worth 200%+ of normal
- **unavailable** — Cannot be found at any price

**Example event economic impact:**
```yaml
economic_impact:
  production_effects:
    - location: "Southern Iron Mine"
      resource: "iron"
      change: "destroyed"
      duration: "Permanent"
    - location: "Grain Fields (Valdris Region)"
      resource: "grain"
      change: "reduced"
      duration: "1 year (crop failure)"
  trade_effects:
    - route: "Valdris-Library Road"
      change: "blockaded"
      duration: "6 months (enemy army holds road)"
    - route: "Northern Pass"
      change: "disrupted"
      duration: "2 months (landslides)"
  wealth_transfers:
    - from: "Valdris (losing military expenditure)"
      to: "War Lords (plunder)"
      amount: "200K gold"
      reason: "Military defeat, tribute paid"
  price_effects:
    - resource: "iron"
      change: "spiked"
      location: "Valdris (supply shortage)"
    - resource: "grain"
      change: "rose"
      location: "Regional"
```

## Economy Configuration File

Located at `world/economy.yaml` in your project.

**Basic structure:**
```yaml
# ─── CURRENCIES ───────────────────────────────────────────────────────
currencies:
  - name: "Crown"
    symbol: "₵"
    denominations:
      - name: "gold crown"
        value: 100
        material: gold
      - name: "silver mark"
        value: 10
        material: silver
    issuing_authority: "The Kingdom"
    accepted_in: ["Valdris", "The Sunken Library"]

# ─── RESOURCES ────────────────────────────────────────────────────────
resources:
  - name: "Iron"
    category: raw-material
    rarity: common
    base_value: "2 silver marks per ingot"
    unit: "ingots"
    perishable: false

# ─── PRODUCTION ───────────────────────────────────────────────────────
production:
  - resource: "iron"
    location: "Southern Iron Mine"
    output: "200 ingots/year"
    quality: standard
    labor_source: "Mining Guild"
    status: active

# ─── TRADE ROUTES ─────────────────────────────────────────────────────
trade_routes:
  - name: "Valdris-Library Road"
    from_location: "Valdris"
    to_location: "The Sunken Library"
    goods:
      - resource: "grain"
        direction: outbound
        volume: "500 bushels/year"
    annual_value: "~2000 crowns"
    controlled_by: "The Kingdom"
    status: active

# ─── ECONOMIC RULES ──────────────────────────────────────────────────
rules:
  primary_currency: "Crown"
  barter_common: true
  banking_exists: true
  taxation: "Flat 10% on all trade"
  slavery_exists: false
  guild_system: true
  monopolies: ["salt", "spices"]
  black_market: true
  magical_economy: false
```

## Economic Workflow

1. **Define resources** — What exists in world
2. **Create production nodes** — Where things are made
3. **Define currencies** — How value is measured
4. **Map trade routes** — How goods flow
5. **Add faction economics** — Track faction wealth
6. **Document event impacts** — How history changes economy

## Quick Reference: Impact Chains

When something happens, trace economic effects:

```
Battle at Bridge
  ↓
Trade route blockaded 6 months
  ↓
Iron supply drops 60% in Valdris
  ↓
Iron price spikes 200% in Valdris
  ↓
Military construction halted (can't afford supplies)
  ↓
Construction jobs eliminated
  ↓
Unemployment rises in Valdris
  ↓
Potential unrest/rebellion
```

## Common Mistakes

❌ **Don't:**
- Leave trade routes undefined (no geographic sense of commerce)
- Ignore faction wealth in conflicts (who can afford longer wars?)
- Forget event impacts are temporary (economic recovery timeline)
- Create prices without supply scarcity context
- Assume all resources are equally abundant

✓ **Do:**
- Define production capacity per location
- Track wealth transfers during major events
- Remember blockades/disruptions have cascading effects
- Consider seasonality (harvests, shipping seasons)
- Use economy as plot driver (food shortage → migration → conflict)

## Economy as Plot Driver

Economics can create story tension:
- **Scarcity conflicts** — Two factions competing for rare resource
- **Debt** — Faction must take risky action to pay debts
- **Trade wars** — Economic pressure between factions
- **Inflation** — Currency devaluation causes social unrest
- **Labor shortage** — Population loss from plague/war affects production
- **New resources** — Discovery opens new conflicts

Example: Event (plague kills half farmers) → production cut → food prices spike → poor starve → rebellion → new political order.
