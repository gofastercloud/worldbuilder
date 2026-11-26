# Factions and lineages

## Faction formation
A faction exists because something made it worth organising. Record in `founding_event`, `founding_date` and the description:
- **Cause**: resource scarcity or control, contested border, trade interest, labour grievance, belief or schism, conquest and resistance, mutual defence, succession dispute, technological or magical change. Link an event where one exists (use `history-and-events` to create it with causes and effects).
- **Constituency**: which people, race, class or species gain; which lose, and so become enemies.
- **Date**: after the cause; leaders alive and mature at founding.
- **Type and structure** follow the economy and culture: guilds in trade or craft economies, clan councils in kin-based societies, military orders where borders are contested, religious orders where a faith has surplus and schisms.
- **Resources and territory**: `territories` and `headquarters` exist, are reachable, and list the faction; `resources` are produced or acquired by explained means (`economy-and-trade`).
- **Size** (`member_count`, `military_strength`) fits the people's population and food supply.

## Membership and leadership
- Each character `faction` is mirrored in the faction `members`; `leader` and `leaders` are living members (status not dead).
- Rank structure (`ranks`) fits scale; a faction of 20 does not have eight ranks.
- Leadership changes follow the faction's rule (election, seniority, appointment, inheritance); record the last change and cause.
- A faction that spans species or races needs a shared language or an interpreter class.

## Relationships and rivalries
- Each relationship has a reason (contested resource, historical event, doctrine, debt, marriage) and is written on both sides, with compatible types (ally to ally, enemy to enemy, vassal to patron).
- Rivalries derive from conflicting interests; alliances from shared enemies or trade. If two factions with opposed interests are "allies", state the bargain.
- Wars and treaties are events; update both factions and the territories involved.

## Lifecycle
Factions grow, split, merge and die. Dissolution or decline needs a cause event and a `dissolution_date`; a faction with `status: disbanded` cannot have living recent leaders or active territory. Splits create new factions with their own cause.

## Lineages
- **Origin**: `founder` (a character file, or a stated unnamed origin) and `founded` date that precede members' births.
- **Seat and faction**: seat is a location that lists them; the lineage's role in a faction is reciprocated.
- **Succession**: `succession.rule` fits the culture's inheritance custom, the species' reproduction and lifespan. `succession.history` is chronological, each ruler alive during their reign, reigns do not overlap (unless co-rulers are stated), gaps are explained (regency, interregnum, usurpation, extinction and refounding).
- **Members**: every listed member has `family_links.lineage` set, plausible parents within the lineage or marriage-ins (`marriage_alliances`), and ages that fit the generation arithmetic in `quantities.md`.
- **Bloodline traits** (`inherited_traits`) must obey species biology and the world's magic flag; inherited powers need a source.
- **Rivals and allies** reciprocal, with a cause (land, title, feud, marriage alliance).
- **Long histories**: a lineage claiming N generations needs enough named or summarised links, and a record of survival through hard events (wars, famines, plagues). Extinction and survival both have causes.
- **Status**: `extinct` or `scattered` lineages have an end event; `ended` is after `founded`; a `hidden` lineage explains why it is hidden and how members know.

## Anti-patterns
- Factions as scenery (no cause, no members, no territory).
- Dead or absent leaders.
- Every faction at war with the nearest neighbour for no stated reason, or no faction ever changing in a thousand years.
- A lineage with one head and no members, no founder, and a succession history written only as "numerous elders".
- Alliances recorded on one side.
- Dynasties with rulers whose reigns exceed lifespans or begin before maturity.
