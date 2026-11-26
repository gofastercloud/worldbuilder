# Stories and series

## Finding the premise in the world

Look for tension that already exists. Candidates, with where to find them:

| Source | Where | What it gives |
|---|---|---|
| Unfolding event | events with `open_ended` | A situation whose consequences nobody has seen yet |
| Rival versions | traditions with `contradicts`, regions that differ, official vs folk | Conflict between people who each believe they are right |
| Unrooted mysteries | `graph.py unrooted`; traditions with `origin_unknown` | Something the world cannot yet explain: a story to uncover |
| Blocked faction goal | faction `goals` vs resources, routes, rivals | Motive with real obstacles |
| Scarcity or price shock | economy data, disrupted routes | Pressure on ordinary people |
| Ungrieved consequence | `immediate_consequences` and `traces` of recent events | An aftermath to dramatise |
| Secret truth vs known story | event `secrecy: secret`, tradition `fidelity` low | Dramatic irony and reveal |

Pick one primary tension and one or two secondary ones. State the premise as: who wants what, what in the world stands in the way, what is at stake, and what the world will look like if they succeed or fail.

## Plot from consequences

- Each major beat is an event in the world: it has a cause (a character's choice, a faction move, a natural event) and consequences that the next beat must honour.
- Escalation comes from consequences stacking, not from new surprises. When stuck, run `graph.py impact` on the last beat and use what it lists.
- Antagonists have their own goals, means and knowledge. Run their clock in the background: what they do if the protagonist does nothing.
- Reversals use knowledge gaps: the protagonist learns the folk version is wrong, or the official version hid something. Decide in advance exactly who knows the truth and why they kept silent.
- Endings: either close the chains (effects land, traces left) or leave `open_ended` events and `unresolved` arc entries on purpose. Never end with the world unchanged.

## Secret truth as engine

Keep two ledgers: the TRUTH (events, causes) and the STORY (what each character and faction believes). Plan reveals as moves of information between ledgers: who learns what, when, from what evidence, at what cost. When a reveal happens in the story, update the record: the character's knowledge, the tradition's `held_by` or variant, the event's secrecy if it becomes public, and any new event the reveal causes (arrests, schism, war).

## Structure

- Short story: one tension, one change, one POV usually, 1500 to 6000 words. Select a single event or decision as the hinge; everything else is texture from the world.
- Novel: use arc fields as the beat sheet; chapters map to beats; subplots are `subplot` arcs touching the main arc at least at midpoint and climax.
- Rotating POV: each POV has a distinct knowledge set and voice; list who knows what per chapter.
- Always decide the in-world span first and compute elapsed time, travel and seasons across chapters.

## Series

- Book-level arcs use `book`, `continues_in`, `continued_from`. Keep `unresolved` lists as the hand-off to the next book.
- Between books, advance the world: run the date forward, let `open_ended` events resolve into recorded events with consequences, age characters, change prices, let traditions decay or mutate. The world does not wait for the protagonist.
- Track a series bible implicitly in the files: what each book changed (events with `caused_by` links across books).
- Foreshadowing: plant as `foreshadowing` in the arc and as real world facts (a trace, a rumour, a scarcity) so the payoff is explained by the record, not by authorial convenience.
- Do not let later books contradict earlier recorded events; if a retcon is needed, list dependents with `impact` and fix them all or tell the user what breaks.

## Outputs

Premise (one paragraph), arc file(s) filled in, chapter outline with dates and POV, list of world facts needed (and created), then prose on request. Offer to write the first chapter through `wb-write`.
