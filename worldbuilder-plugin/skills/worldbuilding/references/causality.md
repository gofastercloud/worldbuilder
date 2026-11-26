# Causal chains

Every significant fact needs a cause and, usually, consequences. Record them in the files so they can be checked.

## What counts as significant

Events, foundings, migrations, wars, discoveries, new technologies or magic, shifts in climate, trade routes, laws and religions, deaths of notable people, and the existence of any settlement, faction or species.

## Modelling

- Events carry cause and effect links in frontmatter: `caused_by` and `leads_to` (event slugs), `root_causes`, `immediate_consequences`, `long_term_consequences`, and `economic_impact`, `social_impact`, `magical_impact`. Fill all of them for significant events. `caused_by` and `leads_to` are bidirectional: if A leads to B, B is caused by A. Other entity types have no such fields yet; record non-event causes in the event that links them (the event names the location, faction or resource it acts on).
- A cause must have an earlier WorldDate than its effect. Simultaneous causes are acceptable only for the same day.
- Link non-event causes too: a famine may be `caused_by` a climate shift recorded on a location; a trade route may be `caused_by` a resource on a location.
- Every chain ends in a present-day TRACE: a place, faction, price, custom or language feature, or a story, legend, ruin, name, ritual, proverb, or a recorded GAP in the record (lost or suppressed knowledge). Each trace must link back to its event: the event lists it in `traces`, and a tradition lists the event in `origin_events`. An event with no `leads_to` is acceptable when it has traces.

- An event whose effects have not happened yet (ongoing, or the story has not reached them) may set `open_ended: "<reason>"` instead of `leads_to`. The validator accepts this only when the reason is non-empty and the consequences fields are filled. Use it for genuinely unfolding events, never to skip working out effects that already occurred.

## Layers to connect

1. Geography and climate (the root causes)
2. Resources, flora and fauna
3. Settlement and population
4. Economy and trade
5. Politics, factions and conflict
6. Culture, language and belief
7. Memory and tradition (myths, legends, customs, taboos, proverbs, lost or distorted records; see the `folklore-and-traditions` skill)
8. Events that rewrite layers 2 to 7

Every entity should be reachable from a root cause by following links upward. An entity with no cause is an orphan: fix it or justify it as a deliberate starting condition in `project.yaml`.

## Consequence sweep

After any addition or change, ask of each layer: does this alter it? If yes, edit the affected files now. Typical misses: a new route that never changes prices; a war with no population or leadership change; a drought with no migration; a conquest with no language or naming shift; a catastrophe or atrocity that leaves no story, taboo or gap in the record.

## The memory layer

The causal graph has two chains. The TRUTH chain is events and their causes. The MEMORY chain is what survives, who carries it, how it is distorted and why. A chain can end in the past and leave only a story in the present; that story is a valid trace, and a tradition (`world/traditions/`) records it.

- **Distortion**: stories are simplified, fused, moralised, inverted or renamed by people with reasons. Name the mechanism and the cause every time.
- **Loss**: records burn, languages die, carriers die out; a recorded gap is a trace too. Note what was lost, when and why.
- **Who controls the record**: victors, priesthoods, archives and states shape the official version; the defeated and the folk keep another. Each needs a source.
- **Fidelity decays** with time, falls faster without literacy, and is frozen or rewritten by institutions. Oral accounts do not stay accurate over centuries.
- **Contradictory variants** between regions, classes or factions are normal, but each needs its own cause.
- **Belief versus fact**: a tradition records what people believe. It never creates real effects the world flags or magic systems do not allow, and it is permitted in a world without magic only as a belief.
- The author always knows the truth: keep `origin_events` set unless a deliberate mystery is recorded with `origin_unknown` and the reason.

Load the `folklore-and-traditions` skill to derive, write and check traditions.

## Plausibility checks

- Quantities: population, food, army, taxes, trade volumes.
- Time: durations (travel, construction, generations) fit the date gaps.
- Agency: each actor had the means, motive and opportunity under the world flags.
- Alternatives: if a more obvious cause would also fit, say why it did not occur or add it.
