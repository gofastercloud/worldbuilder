# Characters

## Read first
Birthplace location and its parent chain; the race (homeland, naming, language, taboos, traditions) and species (lifespan, maturity); the faction and lineage; events during their life; relatives already written; `project.yaml` calendar and flags.

## Build order
1. **Origin**: species, race, birthplace, class. Birthplace should be inside or explained against the race's homeland and territories. Moves need a cause (trade, service, exile, conquest, marriage).
2. **Time**: pick a reference date; set `age`; compute birth year; check lifespan and parents.
3. **Family**: `family_links` father, mother, spouse, children, siblings, lineage, birth_order, legitimacy, `title_inherited`. Parents exist as files (or are explicitly unnamed with a reason); write both sides. A character's parents must be of compatible species (flag), at least maturity-aged at the birth, and alive at conception.
4. **Name**: follow the race's `naming_conventions` and language sounds. If the character has a different-culture name, explain it.
5. **Languages**: `languages.native` from birthplace and parents; `spoken` from trade, work, faction, schooling or conquest; `literacy` from class and script availability.
6. **Voice**: `voice.description`, `tags`, `accent`, `dialect` are prose context describing how they sound. Derive accent and dialect from birthplace, class and age; they are not mechanics. Avoid contradicting species anatomy and language phonology (a lipless speaker does not "purr bilabials").
7. **Faction and role**: membership consistent with class, species, history and beliefs; reciprocated in the faction. A leader is alive, old enough, and a member.
8. **Motivation**: root it in the record: a loss, debt, oath, grievance or ambition that traces to an event, a family history or the character's people. Write the cause in `Backstory` and `Motivations & Goals`.
9. **Where were they**: for every event of significance in their era, decide present, absent, too young, dead, or far away, and write it in `Backstory`. If present, add them to the event's participants and the reverse link; if absent, say where they were.
10. **Skills and inventory**: from training and class (a miner has mining skill; an item owner has a route by which they acquired it). Check flags for technology and magic.

## Checks
- `age` plus reference date gives birth after parents' births by at least maturity; death (if any) within lifespan or explained (violence, plague, ritual).
- Spouse age and species compatible; children have this character as a parent in both directions.
- `lineage` member lists include them; `title_inherited` fits the succession rule and order.
- `location` is where they are now; moves between locations fit travel time and routes.
- `first_appearance` and `last_appearance` fit their life and the story timeline.
- `secrets` do not contradict the machine description.
- Both descriptions agree; image prompts, if any, follow the project's style system.

## Anti-patterns
- Orphans: an adult with no parents, home or kin in a world where everyone else has them (unless the orphaning is itself a recorded event).
- Mismatched ages: a 30-year-old parent of a 25-year-old.
- Ageless nobles: a 600-year-old ruler whose predecessors, heirs and household do not exist.
- Voices and accents that ignore birthplace.
- Motivation that is a trait list rather than a consequence of events.
- Present at events they could not have attended.
