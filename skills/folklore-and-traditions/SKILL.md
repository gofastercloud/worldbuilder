---
name: folklore-and-traditions
description: Create, derive and check a world's myths, legends, folktales, customs, rituals, festivals, superstitions, taboos, proverbs, songs, oaths and oral history, and the memory of events in general. Use when the user asks what people believe about something, how a story, custom or taboo arose, how history is remembered, distorted, suppressed or lost, how propaganda or lost history works, or wants folklore, traditions or mysteries added to a world. Derives each tradition from a real event and its causal chain, records who carries it and how it is distorted, and ties it to present-day behaviour.
---

# Folklore and traditions

Myths, legends, customs and superstitions are some of the best worldbuilding there is, but only when they are derived from something that happened. A causal chain can end in the past and leave only a story in the present. This skill models that story and keeps it honest.

Read `worldbuilding/SKILL.md` and `worldbuilding/references/causality.md` first if you have not this session. Load `history-and-events` to read the source events, `peoples` for the carrying culture, and `magic-systems` if the tradition touches the supernatural.

## The two chains

- **Truth chain**: events and their causes, in `world/events/`. What actually happened, as far as the author is concerned.
- **Memory chain**: what survives, who carries it, how it is distorted and why. This is the `tradition` entity, in `world/traditions/<slug>.md`.

A tradition links to the truth chain through `origin_events`, and the event links back through `traces` (write both sides). The memory chain adds a layer after culture and belief: every event may leave a trace in the present, and a story is a legitimate trace. The author always knows the truth. The in-world people usually do not.

## Fields at a glance

`name`; `kind` (myth, legend, folktale, custom, ritual, festival, superstition, taboo, proverb, song, oath, holy-day, other); `status` (living, fading, forgotten, revived, suppressed); `origin_events`; `origin_unknown` (deliberate mystery only); `fidelity` (accurate, simplified, embellished, conflated, inverted, garbled, invented); `distortions` and `distortion_causes` (strings); `held_by` (faction, race or species); `regions`; `places` (locations it governs behaviour toward); `language`; `first_attested` (year, era_prefix); `transmission` (oral, written, ritual, art, mixed); `drives` (observable present-day behaviours); `related`; `contradicts` (reciprocal); `reliability` (firsthand, well-documented, rumored, conflicting-accounts, legend, false-history); `claims_supernatural` (bool); `descriptions.machine` and `.human`; `tags`. Use the template in `../worldbuilding/assets/templates/traditions/` and the schema reference for exact formats.

## Procedure: derive a tradition from an event

1. **Pick the event.** Not every event leaves a tradition. Prefer events that were large, frightening, shared, repeated or profitable to remember. Ask of each significant event whether it leaves a tradition, and record the answer when it does not (the absence is also a fact).
2. **Read the event and its ancestry.** Read the event, its `caused_by` chain, participants, locations and `secrecy`. Know the truth completely before you distort it.
3. **Ask the memory questions.** Who survived? Who told it first, and why? Who controlled the written record, and what did they gain? Which language did it pass through? Who was forbidden to speak of it? How long ago was it, and how literate are the carriers? Who benefits from the current version?
4. **Choose distortion mechanisms** (details and examples in `references/distortion-mechanisms.md`): telescoping, hero fusion, moralising, propaganda by the victors, euphemism, mistranslation, taboo-induced silence, conflation of two events, natural-feature etymology. Choose one or two, each with a cause. Record them in `distortions` and `distortion_causes`.
5. **Set fidelity, status, reliability and transmission** from time elapsed, literacy, transmission mode and institutions (`references/transmission-and-decay.md`). Fidelity decays. An oral tradition of 300 or more years does not stay `accurate`; the validator warns on it.
6. **Choose carriers and place.** `held_by`, `regions`, `places`, `language`, and `first_attested` (never before the earliest origin event).
7. **Derive `drives`**: what do people do today because of this? Festival dates tied to the real calendar, taboo places tied to real geography, proverbs tied to real economics, naming habits, oaths, greetings, funeral rites, who will not marry whom. See `references/customs-and-taboos.md`. A tradition with empty `drives` is usually decoration.
8. **Run the consequence sweep** (below), then **write both sides**.
9. **Validate** (see Checklist).

## How customs and superstitions arise

Most customs are fossilised practical lessons with the reason forgotten. Derive them from real causes: a disease outbreak becomes a washing ritual or a food taboo; a flood becomes a ban on building in a valley; a famine becomes a festival of sparing grain; a lost trade route becomes a proverb about overpricing; a war becomes an oath, a song, a banned name. Disease, diet, disaster, trade and war are the five best sources. Walk the chain: event, danger, rule, ritual, explanation, forgotten cause. The explanation (often supernatural-sounding) is the distorted layer; the rule underneath is the true layer, and it is why the custom persisted. Examples and tables are in `references/customs-and-taboos.md`.

## Variants that contradict

Two regions, two classes or two factions should often tell the same event differently, and each variant needs its own cause: who the local survivors were, which side wrote it down, what the local landscape suggested, what the local power wants it to mean. Create each variant as its own tradition, link them with `related`, and set `contradicts` on both (it is reciprocal). Do not vary for variety's sake: an unexplained variant is as bad as an unexplained identical one.

## Scholars versus the folk

In-world scholars, archivists and priests hold a version too, and it is not the truth either. Record it as a separate tradition (`transmission: written`, usually `reliability: well-documented` or `conflicting-accounts`, sometimes `false-history` when the institution rewrote the record) and let it contradict the folk version. Sometimes the scholar is right and the folk wrong; sometimes the reverse (next section). Never let the scholarly version simply equal the author's truth, unless the records were in fact preserved and you can say how.

## The story as an unreliable witness

A tradition can preserve a true fact that the written record lost or suppressed. A nursery rhyme names the real culprit; a taboo forbids the true site of a disaster; a festival date marks the true day when the official record gives another. Use this to plant discoverable truths: the character who notices that the folk version and the archive disagree, and works out which detail is the survivor. Make sure the surviving true detail is real in the event file, and say in the tradition's machine description which detail is true.

## Planting mysteries

A mystery is a tradition whose origin the world has lost. The author must still know the truth. Keep `origin_events` set to the real event wherever you can. Use `origin_unknown` (a string saying what is unknown, to whom, and why: records burned, language dead, carriers gone) only for a deliberate mystery whose truth you intend the story to reveal later, and write the truth into the event file or `world/rules.md` notes now, even if unlinked. A mystery with no author-side answer is just a gap. A recorded gap (lost or suppressed knowledge) is a valid trace: see `causality.md`.

## Belief, not fact, and the magic gate

A tradition records what people believe, never what is true in the world.

1. Read `world_flags.magic.present` in `project.yaml` before writing any supernatural content.
2. **Magic absent**: myths of gods, spirits, curses and miracles are fine as beliefs. Set `claims_supernatural: true`. They must never cause a real supernatural effect: the haunted valley is avoided because people believe it is haunted (and perhaps because of the real mine collapse or fever behind the belief). Characters may act on belief; the world does not honour it. Provide the mundane cause in the origin event.
3. **Magic present**: check the claim against the magic-system rules on file. A myth may exaggerate real magic, misattribute it, or be wrong about its cost, but a tradition must not quietly add capabilities the system does not have. If a belief is true, it is a magic-system fact: write it there, not here.
4. **Magic unset**: ask the user and record the answer first.

## Consequence sweep

A tradition changes behaviour, so update the affected entities for each `drives` item, not just the tradition file:

- `geography-and-climate`: a taboo place or sacred site means a route is avoided, land left unsettled, a pass left unused; record it on the location and route.
- `economy-and-trade`: avoided routes, festival markets, forbidden foods and materials, offerings and tithes change prices, volumes and trade. Record in the routes and economy entities.
- `peoples`: naming habits, marriage rules, funerary customs, language features (a euphemism that replaced a word), religion entries on the culture or race.
- `history-and-events`: the event's `traces`, `remembered_as`, and any later event the tradition caused (a pilgrimage, a feud, a persecution).
- Factions and characters: oaths, loyalties, who exploits the story, who is shunned. Propaganda needs a faction that made it.

## Anti-patterns

- Myths that are fantasy fluff with no origin event (and no `origin_unknown` reason).
- Every culture's myths identical, or every culture's story told the same way about the same event.
- Perfect oral fidelity over millennia.
- A legend nobody believes, that changes nothing and drives no behaviour.
- Villains in legend with no propaganda source: someone had to make them villains.
- Distortion with no cause ("it got garbled"). Say what garbled it.
- Supernatural claims treated as true in a world where magic is absent.
- Traditions that appear the moment after the event; folklore needs time, except propaganda, which can be immediate.
- Forgetting the winners wrote the record, or that the losers also remember.

## Checklist before finishing

- [ ] Each tradition has `origin_events` (or a deliberate `origin_unknown` with a reason) and the author's truth is on file.
- [ ] Each origin event lists the tradition in `traces`; both sides written.
- [ ] Distortions each have a cause; fidelity matches elapsed time, literacy and transmission.
- [ ] `first_attested` is not before the earliest origin event; status fits the elapsed time.
- [ ] Every tradition has `drives`, and each is reflected in the affected locations, routes, economy, peoples or factions.
- [ ] Variants that disagree are linked with `contradicts` (both ways) and each has its own cause.
- [ ] Magic gate respected; `claims_supernatural` set on every supernatural belief.
- [ ] Regional variation exists; not every culture remembers the same way.
- [ ] Load `world-validate` and run its checker; use `why <tradition>` to confirm the origin chain.

## References (load when needed)

- `references/distortion-mechanisms.md`: the nine mechanisms with causes and examples.
- `references/transmission-and-decay.md`: fidelity, status and reliability by time, literacy and institutions.
- `references/customs-and-taboos.md`: deriving customs, taboos, proverbs, festivals, names and oaths from causes.
- `references/worked-example.md`: two traditions derived from the-lattice's events.
