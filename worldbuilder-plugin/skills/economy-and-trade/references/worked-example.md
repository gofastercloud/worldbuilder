# Worked example: auditing The Lattice

Model: `assets/example-the-lattice/` (sci-fi; world flags: spaceflight, FTL, AI, no magic). Source files: `world/economy.yaml`, `world/locations/crucible.md`, `world/locations/pelago.md`, `world/factions/dresh-mining-guilds.md`, `world/events/rim-exploitation-contracts.md`.

## What it already does well (copy these patterns)

- Currencies tied to issuers and to trust: Galactic Credit (GTA digital), Keth'ri Exchange Unit (labour-indexed), Dresh Ore Token (physical, backed by assayable mineral, because the Dresh distrust AI processing), Free Trade Scrip (reputation-backed). Each currency explains where it is accepted and why.
- Production with sources: lattice fuel and null-crystal from `crucible` by Dresh guilds; AI cores and manufactured goods from `keth-prime`; nutrient cultures from `pelago` and water from `thuranni-depths`.
- Routes with controlling factions and risks: The Rim Run (`crossroads-system` to `dresh-holdings`, controlled by `dresh-mining-guilds`), The Deep Current (`thuranni-depths` to `crossroads-system`).
- Causal event: `rim-exploitation-contracts` records transfer of rim mineral value to core corporations, leads to `frontier-unrest-begins`, and the economy rules list "Rim worlds pay more per unit of trade" as the cause of unrest.

## Audit using the procedure

1. **Read.** `crucible` is volcanic, surface about 180 degrees C, toxic atmosphere, about 12 billion people, producer of lattice fuel, rare minerals and null-crystal. `pelago` produces food and water. `dresh` species metabolise minerals but need carbon-based foods for amino acids (`species/dresh.md`).
2. **Find the gap.** Food: 12 billion people at about 300 kg of food each is 3.6 billion tonnes a year (or the equivalent in nutrient culture), and no local farmland exists on a 180 degree surface. `economy.yaml` shows The Rim Run carrying fuel, minerals, null-crystals, manufactured goods and cores to or from `dresh-holdings`, but no food or water inbound. The Drift routes and The Deep Current carry nutrient cultures elsewhere. So the largest population in the setting has no recorded food supply and no way to pay for one beyond what the Rim Run's goods show. That is the "city with no food supply" anti-pattern.
3. **State the cause.** Dresh need only supplementary carbon food (species file), so per capita imports are small, but they are still non-zero and must come from somewhere: the cheapest source is Thuranni aquaculture at `pelago` or `thuranni-depths` over The Deep Current to `crossroads-system`, then the Rim Run.
4. **Define the missing entity** (using base fields plus `via`):

```yaml
- name: "The Rim Run"            # existing route, add goods
  from_location: "crossroads-system"
  to_location: "dresh-holdings"
  goods:
    - { resource: "nutrient-cultures", direction: outbound, volume: "supplementary protein ration for the Dresh population; low volume, high value per kg" }
    - { resource: "water", direction: outbound, volume: "closed-loop make-up for mining habitats" }
  cost_note: "Dresh pay in lattice fuel and null-crystal, which are high value per kg and carried on the same hulls, so the return leg is never empty"
```

5. **Write consequences into the affected entities.**
   - `world/economy.yaml`: add the goods above; show `nutrient-cultures` and `water` with consumers `dresh-holdings` (via `consumers`).
   - `pelago` and `thuranni-depths`: record the Dresh as customers in their notes and and, since `thuranni` is only a route controller in the economy file with no faction entity, either create that faction or put the income in the Thuranni species notes.
   - `dresh-mining-guilds`: add an expense line for food and water imports and a vulnerability (a blockade of the Rim Run starves Crucible faster than it starves anyone else); this deepens the existing conflict with `lattice-systems-corp` and gives `rim-exploitation-contracts` a concrete hold over the Dresh (contracts can specify food supply terms).
   - `rim-exploitation-contracts` event: add `economic_impact` entries (`price_effects`: nutrient cultures, `location: dresh-holdings`) so the exploitative terms show up as prices.
6. **Balance.** Imports per head are small, but at 12 billion people even 10 kg each is 120 million tonnes a year, so the Rim Run needs very large hulls or a much smaller Crucible population; this either supports the existing "very high" volumes or points to lowering the population figure. State which in the location file.
7. **Sweep.** Does it change politics (a blockade is now a decisive weapon, so Dresh defence and anti-AI stance carry a cost)? Update `frontier-unrest-begins` and relevant factions. Does it change the story (a plot point: the Free Trade League offers cheaper food)? Record it.
8. **Validate** with `world-validate`.

## Lesson

A good economy file already has producers, currencies and routes. The gaps are where a big consumer has no supply line, or where a route lists goods in a single direction. Always run the consumer side of the audit: for each large settlement, army and industry, list what it eats and what it burns, then find the route that brings it.
