# Campaigns (D&D-style and other tabletop)

Output is play material for a game master. The world files stay system-neutral; use stat blocks and DCs only if the user names a system (default: describe challenges and offer levels as a range, e.g. levels 1 to 4).

## Inputs to settle

Anchor date (event, era plus year, or present), starting location, party level or tier, number of sessions (one-shot, short run of about three, or custom), tone, themes, content rating. Assemble context as in `context-assembly.md`; for tabletop, also decide how much the players already know.

## Campaign frame (one page)

- **Situation**: what is true on the anchor date and what is changing. Drawn from recent events and open tensions.
- **Hook**: why the party is involved (employer, faction, rumour, disaster, debt).
- **Stakes and clocks**: see below.
- **Secret truth**: what really happened and who knows it, versus the story the world tells. Include what players can discover and how.
- **Themes and tone**.

## Session structure

For each session: opening scene and hook, 3 to 5 scenes or encounters (mix exploration, social, combat or challenge), a hub to return to, a reveal or complication, an ending state that sets up the next session. List for each scene: location, who is there, what they want, what happens if ignored, what can be learned, what it costs. Provide fallback hooks if the party goes elsewhere.

## Locations as hubs

- A hub is a place with several things to do and several ways in: a town, fortress, market, caravanserai, port.
- Pull from the location file: parent chain, terrain, climate and season (weather affects travel, rest, visibility), buildings, population, factions present, resources, regional accent.
- Routes: list outgoing routes with method, `travel_time`, distance, danger, seasonal or restricted status. Compute journeys between hubs from this data and the transport technology allowed by the flags. Put encounters on the road according to terrain, fauna and faction patrols, not at random.
- Each hub has 3 to 5 points of interest, each tied to a faction, resource or event trace.

## NPCs

- Draw from characters and faction members alive on the anchor date, in plausible places. Create new NPCs only when needed, with a species, race, faction, location and cause, and record them.
- For each NPC: role, want, fear, secret, what they know (true, official, folk), what they will trade for it, speech notes from voice fields (accent, dialect, rhythm), and one memorable physical detail from the machine description.
- Motives come from faction goals and personal history. Two NPCs from rival factions should disagree about the same events.
- Voice and mannerisms: see `dialogue-and-voice.md`.

## Rumours

Build a table per hub (d6 or d8) from traditions and events:
- **True**: accurate and useful, from someone with first-hand access.
- **Distorted**: based on a real event but changed by a named mechanism (simplified, moralised, inverted, fused). Say what the distortion is so the GM can reveal the truth.
- **False**: malicious, mistaken or invented, with a source and motive.
Mark which tradition or event each rumour traces to, who tells it, and what it costs the party if they act on it.

## Clocks from faction goals

For each active faction relevant to the campaign: goal, current progress, steps (4 to 8), what advances it each session if the party is absent, what stops it, and what the world looks like when it completes. Steps must be possible given the faction's means, locations and routes. Use real goals from faction files, not generic villainy.

## Economy hooks

Use scarcity, prices, route status and institutions: a blockaded route raising grain price, a guild monopoly, a currency in dispute, smuggling of a banned resource, a debt. Give actual price points and trade goods from the data. Rewards should fit the local economy (a village cannot pay 500 gold).

## Encounters and quests

An encounter is a situation, not a stat dump: who, where, what they want, what is at stake, terrain and weather effects, ways to resolve (fight, talk, sneak, trade), and consequences each way. A quest has a giver with a motive, an obstacle rooted in the world, a location, a truth to find, and at least two valid outcomes that change the world differently.

Magic gate: if magic is absent, so are spells, magical monsters and enchanted items; use mundane threats, beliefs, tricks and hoaxes. If present, use only systems on file.

## Consequence tracking

What the players change is canon for the next session. After each session (or when the user reports what happened):
1. List player actions that changed the world: kills, rescues, thefts, treaties, discoveries, promises.
2. Write each as an event with date, participants, location, `caused_by` (the party's choice and the situation that prompted it), `leads_to` or `open_ended`, impacts, `traces`. Link both sides.
3. Update affected characters (dead, injured, loyal, hostile), factions (leader, power, goals), locations (damaged, controlled), economy (price, route status), and traditions (new legends, rumours, a tale the party now appears in).
4. Advance clocks, including those the party ignored.
5. Run the validator and `graph.py impact` on the new events; apply the consequence sweep.
6. Prepare the next session from the updated state.

Never let the world reset to protect a plan. Player success and failure both stick.
