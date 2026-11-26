# Retrofitting history and answering timeline queries

The graph commands (`why`, `impact`, `path`, `neighbors`, `unrooted`, `stats`) belong to the world-validate skill. Load the `world-validate` skill and use its scripts (it states the exact commands); do not assume a script path from this skill.

## Inserting an event into existing history

1. **Define it.** One line: what, when, where, and the earlier fact that caused it.
2. **Read around it.** List events; read those within the date window and every event, location and faction it will touch. Read characters' birth and death for the participants.
3. **Trace upstream.** Use the graph `why` on the nearest existing event that should be its cause (or the one it will precede). Confirm the new event is dated after all its causes and root conditions.
4. **Trace downstream.** Use `impact` on the existing events that would now be downstream. List everything that changes because the new event exists: dates, who is alive, who holds what, populations, routes, prices, borders, languages.
5. **Decide the shape.** Options:
   - *Add on a branch:* a new event with its own causes and effects that does not change existing history (cheap; check no existing fact contradicts it).
   - *Insert in a chain:* A -> B becomes A -> N -> B. Update `caused_by` and `leads_to` on A, N and B, and re-examine B's `root_causes`; B may now have a nearer cause and its trigger may change.
   - *Alter existing history:* the new event contradicts a recorded one. Stop and report. Present options (change the new event, amend the old, or reconcile by changing dates or causes) with their consequences, and wait for the choice.
6. **Write.** Create the file and edit every file the sweep identified. Re-point links; do not leave stale `leads_to` entries.
7. **Re-run `impact`** on the new event and confirm every item listed has been looked at, then run world-validate.

## Changing or deleting an event

Run `impact` first. For every dependent: keep it (find a new cause), change it (update the cause fields and prose), or remove it. Never delete an event that others cite without redirecting their links. Tell the user the list and the decisions.

## Changing a date

Check every `caused_by`/`leads_to` neighbour for order, every participant's lifespan, every era boundary, and any prose that quotes the date ("seven generations later"). Consider downstream date arithmetic (a "35 years later" in another event).

## Timeline queries

All queries start by listing and reading events; do not answer from memory.

- **Range or era:** include events whose span overlaps the range. Order: era `sort_order`, year, month, day. Undated events listed separately.
- **Why X:** `why X`, then narrate root to event with dates and what each link supplied (means, motive, opportunity).
- **What X changed:** `impact X`, grouped by event consequences, places, factions, population, economy.
- **Between A and B:** `path A B`, and the dates along it, noting the elapsed years.
- **Who was alive / where was X:** character dates and the event participant lists.
- **Gaps:** eras with fewer than the expected significant events, long spans with no events, events without effects (the `unrooted` command plus manual review).
- **Consistency of one thread** (a dynasty, a technology): list its events chronologically and check each step has a cause and lag.

## Presenting a timeline

Group by era with the era's one-line definition. Per entry: date, name (slug), type, "because" (the cause in a phrase), "result" (the main consequence). Use arrows for chains, and show the chains the user cares about. Mark: ongoing (no `end_date`), effects still pending (`open_ended`), approximate dates, disputed or legendary entries (`reliability`), secret events (`secrecy`). Offer: the significant-only view, a per-faction or per-place view, a "road to the present" view (the causal chain ending at the current state). For large worlds present the significant events and offer to expand.
