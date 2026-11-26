# Generating history forward

Aim: a timeline in which each era is explained by the one before it and by the land. Work era by era. Do not write the whole history in one pass.

## Step 0: inputs to read

Read, and quote the relevant lines in your working notes:

- `project.yaml`: world flags (technology, magic, FTL, transport, society), genre and tone, present date, world size.
- Geography and climate: terrain, rivers, coasts, passes, latitude and seasons, hazards (floods, volcanoes, drought cycles).
- Resources and economy (`references/economy.md` in the worldbuilding skill, and `world/economy.yaml` if present): what is abundant, what is scarce, trade routes and their chokepoints.
- Species and races: origin location, lifespan, reproduction rate, diet, tech affinity, relations.
- Existing locations, factions, characters (with birth and death), and any existing events (list them, read all that overlap the period).

Missing roots: if history needs a river, a metal or a species origin that is not recorded, create or request that root first. Do not let an event assume a fact that is not in the files.

Also collect: size (S/M/L/XL), how many years or eras to cover, whether the user wants peace-heavy, conflict-heavy, catastrophe-heavy or mixed history, and fixed events the user already wants (anchors). Anchors are fixed points: build the chains that lead to them and from them.

## Step 1: era plan

Draft 3 to 8 eras as a table (prefix, name, rough years, defining change, what ends it). Show the user for approval when the world is M or larger, as this is the structure everything hangs on. Eras should differ in kind: expansion, consolidation, fracture, collapse, recovery, not just numbered.

## Step 2: Era 0, founding conditions

Events here are caused by roots, not earlier events:

- Settlement: where and why (water, defensible ground, arable land, a pass, a harbour).
- Specialisation: what each region produces given its resources and climate.
- Contact: who meets whom along which route, and the first exchange (trade, raid, marriage).
- Origins of species or peoples as recorded in their files (link, do not contradict).

Each has `root_causes` naming the location, climate or resource, and `caused_by` empty with a short note that it is a root condition.

## Step 3: tension ledger

After each era, write (in your working notes, or in the era's closing event body) a ledger:

| Tension | Source event(s) | Who feels it | Pressure (low/med/high) | Resolved? |
|---|---|---|---|---|

Typical tensions: resource depletion; population above food or tax capacity; unpaid debts or tributes; contested succession; unequal treaty terms; a conquered people's grievance; technology held by one party; border or route control; heresy; refugee settlement; a ruling class that has lost its function; a rival strengthened by the last war.

## Step 4: derive the next era

For each high-pressure tension, ask what a rational or characteristic actor would do with the means they have, and when an opportunity opens. Write the event, name the tension, and record the causal link. Every significant event:

1. Names its tension and its trigger (`immediate_trigger`, `root_causes`).
2. Passes the means/motive/opportunity test (see SKILL.md section 2).
3. Resolves or sharpens at least one tension and creates at least one new one. Write the new tension in the consequences.
4. Includes at least one downstream material change (borders, prices, population, a settlement, a custom, a language shift).

Typical derived chains (use as patterns, not scripts):

- Climate or resource shift -> migration or famine -> conflict at the receiving region -> new border or treaty -> trade route and prices change.
- Discovery or invention -> early adopter gains -> rivals notice -> copying, theft or war -> new standard; displaced workers or guilds resist -> law or revolt.
- Treaty on unequal terms -> compliance, then evasion -> grievance -> rebellion when an opportunity opens (a death, a rival's distraction).
- Plague -> labour shortage -> wage rise or coercion -> social unrest -> institutional change -> long-run belief shift.
- Conquest -> language and naming shift, tribute -> collaborators and resisters -> succession crisis when the conquering ruler dies.

## Step 5: after each era

1. Write the events (full detail for significant, short for minor).
2. Consequence sweep: edit affected locations (population, ownership, ruins), factions (founding, dissolution, leaders, goals), species/races (population, relations), characters (deaths, roles), economy (routes, prices), languages (borrowings), and religion.
3. Run the world-validate skill. Fix errors before starting the next era.
4. Show the user a brief era summary (5 to 10 lines) with the open tensions, and ask whether to continue, unless they asked for the whole span in one run.

## Step 6: closing toward the present

The last era must hand the present: current factions and their grievances, the live threats, one or two events with `open_ended` (effects still unfolding) or an ongoing date range (no `end_date`). A well-formed present state is reachable from the roots by `why` on any present-day fact.

## Population and logistics sanity (quick numbers)

- Pre-industrial armies: about 1 percent of the population in the field for long, 2 percent briefly (see the `economy-and-trade` skill, heuristics); sustained campaigns need grain surplus and transport. Sieges last months, not days.
- Plagues: 10 to 50 percent mortality is catastrophic; recovery takes generations; labour shortage and mobility change follows.
- Travel: use the flag-allowed transport and terrain; compute days before writing dates for two-theatre campaigns.
- Technology diffusion: years to decades per hop, longer across barriers; the second adopter is rarely far behind.
- Dynasties: 20 to 35 years per generation for humans; use species lifespans from their files.
- Institutions: founding to corruption typically takes several generations; reform follows crisis.
