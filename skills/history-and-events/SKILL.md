---
name: history-and-events
description: Build, extend or query a fictional world's history. Use for calendars, eras, timelines, chronology, "what happened", founding stories, wars, plagues, migrations, treaties, discoveries, collapses, and any request to generate history, add or insert an event, explain why something happened, or show what an event changed. Generates history forward from geography, climate, resources and species origins so each era grows out of the last era's unresolved tensions, with causes, consequences and dates recorded and checked.
---

# History and events

History here is a causal graph laid out in time. Every event has causes that are earlier, effects that are recorded, participants who are alive and present, and a plausible mechanism under the world flags. Read `worldbuilding/SKILL.md` and `worldbuilding/references/causality.md` first if you have not this session; this skill applies them to the timeline.

Ground rules (from the core contract): read before you write, trace causes, trace consequences, write both sides of every link, check dates and flags, validate before finishing.

## Load on demand

| When | Load |
|---|---|
| Setting up or changing the calendar or eras | `references/calendar-and-eras.md` |
| Generating a run of history (an era, a whole world) | `references/forward-generation.md` |
| Writing or editing a single event file | `references/event-writing.md` |
| Inserting into or changing existing history; timeline queries | `references/retrofit-and-queries.md` |
| Want a model of a good chain | `references/worked-example-lattice.md` |
| Reporting gaps in the checker | `references/validator-wishlist.md` |

## Step 0: magic gate (never skip)

Read `world_flags.magic.present` in `project.yaml`. If it is false (or `prevalence: none`), write no supernatural content: no `magical_impact`, no cataclysm or war with a magical cause, no divine intervention, no magic discovery events. Offer technology, psychology or natural explanations instead (engineered disasters, belief and propaganda, natural hazards). If it is unset, ask the user; the `magic-systems` skill owns the gate.

## 1. Calendar and eras (always do first)

1. Read `project.yaml` (`calendar:` name, epoch, format; `world_flags`) and `world/history/calendar.yaml` if present. List `world/events/`.
2. If no calendar exists, create `world/history/calendar.yaml` before any event: eras (each with `name`, `prefix`, `sort_order`, `start_year`, `end_year`, `description`), months, `days_per_year`, `date_format`. Details and the template in `references/calendar-and-eras.md`.
3. WorldDate rules:
   - A date is `{ year: 200, era_prefix: "CE" }`, optionally with `month` and `day`. Bare strings such as `"CE 200"` also parse. Use one style per project (match existing events).
   - Years count within an era and restart per era. Different prefixes are ordered by `sort_order`, so every prefix used in an event must exist in the calendar, and `sort_order` must follow real time.
   - Never invent an era or prefix without adding it to `calendar.yaml`. An unknown prefix makes comparisons unreliable and hides date errors.
   - Instant events use `date`. Durations use `start_date` and `end_date`; omit `end_date` while the event itself is still running (an ongoing date range). `open_ended` is a different thing: a reason string for an event whose effects are still unfolding, valid only with the consequence fields filled.
   - Use `date_precision` honestly. Do not give a day when only the decade is known.
   - Eras are defined by what changed (a technology, a collapse, a contact), not by round numbers. An era boundary is itself an event or chain of events; link to it.
4. Fix the present: the "now" date, and which era it falls in. Nothing may be dated after the present unless it is a prophecy or plan, labelled as such.

## 2. Generating history forward

Never write history as a list of cool episodes. Derive it. Full procedure in `references/forward-generation.md`; the core loop is:

1. **Gather root conditions** (read, do not invent): world flags, geography and climate, resources and trade goods, species and their origins, population baselines, existing factions and locations. If a root layer is missing and the history depends on it, say so and ask, or create the missing root fact first and record it.
2. **Era 0 (founding conditions).** Write only what the roots directly produce: first settlements beside water and food, first specialisation around local resources, first contacts along the terrain's travel lines. Each is `caused_by` a root recorded in `root_causes` (a location, resource, climate fact or species trait).
3. **Compile the tension ledger** at the end of each era: unresolved pressures (resource scarcity, grievance, debt, succession doubt, population over carrying capacity, technology half-spread, border friction, belief schism, unpunished crime). Write it as a short list before the next era.
4. **Next era's events come from the ledger.** Each significant event must name which tension it discharges or sharpens. Then check means, motive and opportunity (below). Then sweep consequences into the affected files.
5. **Resolve some tensions, carry some forward, leave one or two open for the present.** The present should be full of inherited pressure, not a blank.

### Causal plausibility test (apply to every significant event)

- **Means.** Does the actor have the people, food, wealth, tech and logistics, given the flags (gunpowder, magic, FTL, transport methods) and the economy? Army size must fit population and food; fleets must fit the shipbuilding base.
- **Motive.** What does the actor want, and what earlier fact gave them that want? "Because they are evil" fails. Scarcity, fear, ideology, honour debts, succession and revenge all work if themselves caused.
- **Opportunity.** Why then, and not fifty years earlier? Name the enabling change: a weakened rival, an opened route, a new weapon, a death, a bad harvest.
- **Geography.** Distances and terrain permit the movement in the time given.
- **Alternatives.** If a more obvious outcome was available (negotiation, retreat, ignoring it), say in `root_causes` or the prose why it did not happen.
- **Actors.** Named people are alive, of age, and located there on that date.

### Pacing and density

- History is lumpy: long quiet stretches of slow change (migration, drift, institutions hardening) then clusters around crises. Do not space events evenly.
- Roughly one significant event per 15 to 40 in-world years in stable stretches, and 3 to 8 in a crisis decade. Scale to lifespans: long-lived species compress events per year and stretch per generation.
- Each era needs at least one slow process (a gradual `milestone`), one event that changes a material fact (route, border, population, technology), and one cultural or belief shift.
- Not every event is a war. Aim for no more than a third of an era's events being violence; add plagues, harvest shocks, inventions, migrations, laws, marriages, successions, trade agreements, religious change.
- Quiet eras must still change something (price, population, language). If nothing changes, merge the era into its neighbour.

### How many events (guide; the user's size overrides)

"Significant" means `significance` of important, crucial or world-changing, or `scope` regional or wider. Write only the schema values (trivial, minor, notable, important, crucial, world-changing); never write legacy `major`, `critical` or `moderate`. Roughly 3 to 5 eras for S and M, 5 to 8 for L and XL.

| Size | Total events | Significant | Per era (significant) |
|---|---|---|---|
| S | 12 to 25 | 5 to 10 | 2 to 4 |
| M | 30 to 60 | 12 to 25 | 4 to 7 |
| L | 70 to 120 | 30 to 50 | 6 to 10 |
| XL | 150 to 250 | 60 to 100 | 8 to 15 |

Write significant events in full (all causal fields). Minor events may be one or two fields plus a sentence, but still need `caused_by` or `root_causes`. Generate era by era and stop after each era to sweep and validate, rather than writing all events at once.

### Event types and what each must change

`founding` (a place/faction/institution that now exists), `war`/`battle`/`siege`/`rebellion` (borders, population, leadership, grievance), `treaty`/`trade_agreement` (prices, routes, obligations that later strain), `discovery`/`invention` (what becomes possible, who profits, who is displaced), `plague`/`natural_disaster`/`cataclysm` (population, migration, labour, belief), `coronation`/`death` (succession, policy; the person's file shows the dates), `milestone` (slow processes, including migrations and cultural drift), `custom` only when none fit. Use the types in the project's `_schema.yaml`.

## 3. Writing one event

Details, field reference and a template in `references/event-writing.md`. Minimum for a significant event:

- `name`, `type`, `date` or `start_date`/`end_date`, `era`, `significance`, `scope`.
- `locations` and `participants`/`organizations`, all existing slugs; every named person alive and located there.
- `caused_by` (event slugs) and `root_causes` (non-event causes: terrain, climate, resource, belief, person). Both unless it is a deliberate Era 0 starting condition.
- `immediate_trigger` (why now), `immediate_consequences`, `long_term_consequences`, and whichever of `political_impact`, `economic_impact`, `social_impact`, `magical_impact` genuinely apply.
- `leads_to` for every downstream event that exists, with the reverse `caused_by` written on that event.
- `open_ended: "<reason>"` only if effects are still unfolding at the present date (not for an ongoing date range, which just omits `end_date`); consequence fields still filled with what is known.
- `economic_impact` is a prose string. Structured price, route and flow effects go in the economy file (`shocks`, see `economy-and-trade`).
- Body sections: What Happened, Context and Background, Consequences and Aftermath.
- Long-term consequences must name things that exist today (a place, faction, custom, price, word, border). If you cannot, the event is probably trivial or its effects are unrecorded.

## 4. Retrofitting an event into existing history

Load the `world-validate` skill and use its scripts (it states the exact commands): `why <slug>` for an event's ancestry and `impact <slug>` for everything downstream. Procedure in `references/retrofit-and-queries.md`:

1. Read the neighbouring events and every entity the new one touches.
2. Run `impact` on the nearest downstream event and `why` on the nearest upstream one.
3. Place the event between a real cause and the real effects; do not add it as an orphan.
4. Decide what it changes. Update every event, location, faction, character and economy file the sweep names, including re-pointing `caused_by` when the new event is now the nearer cause.
5. If it contradicts established history, stop and tell the user what breaks; offer options (change the date, drop the link, amend the old event) rather than silently rewriting.

## 5. Timelines and queries

Sort by WorldDate (era `sort_order`, then year, month, day), with durations placed by start date. Answer queries from the files, never memory:

- "What happened in era X / between A and B": filter by date range, include durations that overlap.
- "Why did X happen": run `why` and narrate the chain root to effect, citing slugs and dates.
- "What did X change": run `impact`.
- "Who was alive then": check character birth and death.

Present a timeline as a table or list: date, event, type, one-line cause arrow ("because of ..."), and one-line result. Group by era, mark open-ended items, flag undated events separately, and mark disputed or legendary entries via `reliability`. Show the causal chains the user asked about as arrows between dated items, not as isolated bullets. Offer the lean version (significant events only) first for large worlds.

## 6. Anti-patterns (reject on sight)

- **Deus ex machina.** A rescue, invention or villain arrives with no earlier cause, or a convenient natural disaster fixes a plot problem. Find the cause or cut it.
- **Reset.** A collapse or war that wipes the slate while the same institutions, prices and borders persist afterwards. Real collapses leave ruins, debts, refugees and grudges.
- **Instant consequences.** A discovery that transforms society in a year, a famine with no migration, an army raised with no logistics. Spread effects over plausible years and record them.
- **Forgotten effects.** A war with no casualties on the population, a treaty with no price change, a conquest with no language or naming shift, a plague with no labour shortage.
- **"Ancient civilisations" with no cause.** Ruins or precursors that exist because they are cool. Give them geography, resources, a rise, a fall, and an effect on today.
- **Rival timelines.** Two files that disagree about who founded what, when, or why, without `reliability` marking one as legend or false history. Merge, or mark honestly.
- **Evil by default, villains by decree, convenient idiots.** Motives must be derived and decisions must serve the actor's interests.
- **Everyone is present.** Characters at battles they could not reach, or after death.
- **Even spacing, all wars, no peace.** See pacing.
- **Era names as decoration.** An era boundary with no event behind it.
- **Magic or technology out of nowhere.** Not allowed by flags, or arriving with no discovery event and no lag.
- **Orphan events, and dangling `open_ended`.** Using `open_ended` as an excuse for not working out consequences that should already have happened.

## Memory of events

Significant events may leave traces in the present, including stories, customs, taboos and gaps in the record. Add them to the event's `traces` and use the `folklore-and-traditions` skill to derive the tradition (events with `traces` need not have `leads_to`).

## 7. Checklist before finishing

- [ ] Calendar exists; every prefix used is defined; the present is fixed.
- [ ] Every new event has a date; durations have an `end_date`, or omit it while the event is still running; `open_ended` only for effects still pending.
- [ ] Every cause is earlier than its effect; era boundaries are consistent.
- [ ] Each significant event states means, motive and opportunity (or the earlier facts supply them); flags respected.
- [ ] Every event has `caused_by` or `root_causes`; no orphan, unless a declared starting condition.
- [ ] Every significant event has immediate and long-term consequences naming things that now exist, plus the impact fields that apply.
- [ ] `leads_to`/`caused_by` reciprocal in both files; participants, locations and factions reference real slugs with reverse links.
- [ ] Participants alive, of age and in place on the event date.
- [ ] Consequence sweep done: locations, factions, population, economy, species, language, and characters edited where the event changes them.
- [ ] Pacing: quiet periods exist; violence not dominant; each era leaves tension for the next.
- [ ] No anti-patterns from section 6; no rival accounts of the same event.
- [ ] Present-day state reachable from root causes by following links (use `why` on a few present-day facts).
- [ ] Run the **world-validate** skill, fix every error, explain any warning left, and report the result to the user.
