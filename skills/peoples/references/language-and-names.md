# Language, names, loanwords, dialects, scripts

## Entities and fields
Language entity: `status`, `family` (`family_name`, `branch`, `parent_language`, `child_languages`, `divergence_date`), `intelligibility`, `script`, `speakers`, `characteristics` (`phonology`, `grammar_notes`, `registers`, `loanwords_from`, `loanwords_to`), `special`, `origin`. Race `culture.naming_conventions` (`pattern`, `examples`, `notes`).

## Sound inventory
- Must fit anatomy: a species without lips has no labials; low-frequency speech suits subterranean or large-bodied speakers (the Dresh sample); whistled or click speech suits open terrain or forest; colour or pheromone languages need the matching organs (`special.nonverbal_component`).
- Pick a small, consistent set: 10 to 25 consonants, 3 to 7 vowels, allowed syllable shapes, and stress. State it in `characteristics.phonology` as a compact summary (for example "CV(C), no clusters, vowels a e i o u, stress first syllable, voiced stops common").
- All names and place names of that language follow the same inventory and shapes. Check by reading ten names aloud against the rule.

## Naming schemes (follow the language and culture)
- Define `pattern`: for example given + kin name, given + patronymic, given + place, title + given, single name, clan + given.
- Give 5 or more examples that obey it, and notes saying what the parts mean in the language (a root list of 10 to 20 words is enough: stone, river, iron, bright, elder, child, north).
- Name meanings reflect the culture's environment and values (herding words in a herder culture, mineral words for miners).
- Name changes at life events (coming of age, first expedition, marriage, accession) are fine if recorded in `traditions`.
- Place names come from the language of the first or dominant settlers; later layers show conquest (a different language's names, translated names, or hybrid). A map with only one naming style across a region of several peoples needs explanation.
- Foreign names appear through contact: trade (merchant names), conquest (elite names adopted), religion (saints' or scriptural names), marriage, exile. Name the reason.

## Loanwords and contact
- Trade produces nouns for goods and units; conquest produces government, law and military terms; religion produces ritual vocabulary; intense contact produces a pidgin or creole (a `constructed` or `living` language with `is_lingua_franca: true`).
- Record `loanwords_from` on the borrower and `loanwords_to` on the source, with the event, route or location that caused it in the prose.
- The direction follows prestige and power: the dominated language borrows more.
- A migration or conquest must leave at least one trace: place names, loanwords, a substrate dialect, script, or a diaspora race.

## Divergence and dialect drift
- Drift scales with time and isolation. Rules of thumb: about 5 to 10 percent core vocabulary change per millennium under normal conditions; dialects of one language arise within 200 to 500 years of limited contact; mutual unintelligibility within 1000 to 1500 years; recognisable family after 3000 or more years. Writing, a prestige standard, schools and a central state slow drift; isolation, migration, conquest and no writing speed it.
- Intelligibility score: dialects 0.7 to 0.95; sister languages 0.2 to 0.6; distant relatives below 0.2 (shared cognates only). Directional asymmetry is real: speakers of the more conservative or prestigious form understand the other better, or the reverse where one has heard the other through trade.
- Distance gradient: neighbouring communities are mutually intelligible, ends of a long chain are not (dialect continuum). Geographic barriers (mountains, seas, deserts) mark boundaries.
- Dates: `divergence_date` of a child must precede the present and fit the separation event (migration, collapse of empire, schism); parent and child entries agree, and the parent lists the child in `child_languages`.
- Long-lived species: the same elapsed years yield fewer generations; drift tracks generations of learners, so drift per year is slower, but written standards matter even more.

## Scripts and registers
- Script type follows medium and use: carving gives angular, boustrophedon or linear scripts; brush or ink gives cursive; trade needs compact abjads or syllabaries; religious languages keep archaic scripts. Literacy follows surplus and administration.
- Registers (formal, ritual, trade, intimate) follow class and contact; a sacred language may be a dead parent (`status: dead`, `is_sacred: true`) kept for ritual.
- Languages tied to a race must be spoken by that race: `native_races` and race `culture.language` agree.
