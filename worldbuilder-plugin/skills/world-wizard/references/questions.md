# Wizard questions and what to record

Ask in this order. Offer short option lists and a recommended answer. Record each answer in `project.yaml` straight away. Flags use plain values under `world_flags` in `project.yaml` (see the template); `worldbuilding/assets/templates/world_flags.yaml` documents every flag and its allowed values.

## 1. Magic (always first)

"Does your world have magic or anything supernatural (spellcasting, psionics, divine miracles, spirits, curses that really work)? Yes or no."

| Answer | Record | Consequence |
|---|---|---|
| No | `magic.present: false`, `magic.prevalence: none` | No magic systems, no working curses, no magical creatures anywhere. Religion and legend may exist as belief only. Stage 5 is skipped. |
| Yes | `magic.present: true`, then ask the rest | Stage 5 is run, and every supernatural element must belong to a system on file. |
| Unsure ("ambiguous") | Do not accept silently. Offer "no, but the people believe it", or "yes, but rare and unreliable". Record the chosen version. | |

If yes, ask:
- `prevalence`: none, rare, uncommon, common, ubiquitous. How many people can use it, or how often does it show up in daily life.
- `hardness`: hard (strict rules and costs), medium, soft (mysterious, few rules).
- `source`: where the power comes from (a field, ley lines, gods, a substance, minds, a dead civilisation).
- `cost`: what using it costs (energy, health, materials, years of life, favours, nothing).
- `heritability`: who can use it (anyone trained, bloodlines, chosen, one species).
- `public_knowledge` (true or false) and `divine_intervention` if gods are in play.

## 2. Technology

Show the genre defaults from `preset_defaults` in `world_flags.yaml` as one list and ask what to change. Key flags: `technology.level`, `gunpowder`, `printing`, `electricity`, `steam_power`, `internal_combustion`, `computing`, `spaceflight`, `ftl`, `ai`, `biotech`, `magitech` (true only if magic is present), `metallurgy`, `medicine`, `communication`, `transportation`.

These flags limit what later stages may write: transport speeds, weapons, communications, trade scale.

## 3. Basics

- `title`, `genre` (fantasy, scifi, modern, campaign, custom), `type` (novel, series, campaign, game, worldbook).
- Size S, M, L or XL: see `sizes.md`. Recommend by use: short story or one-shot S; novel or campaign arc M; series or full campaign L; sandbox or universe bible XL.
- The premise: one or two sentences, or "surprise me". Treat a seed phrase as biasing themes and cultures, not as a fixed plot.
- `themes` (list) and `tone` (list), for example grim, hopeful, wry.

## 4. Style

Pick one prose preset from `styles.yaml`: literary, pulp, young-adult, dark, gritty, epic, litrpg, cozy, horror, hard-sf, space-opera, noir, fairy-tale, or custom. Set `style.prose.preset`, `pov`, `tense`, `content_rating`. This only affects how prose descriptions are written; it never changes facts.

## 5. Optional detail (guided mode; choose yourself in YOLO)

- Physics and geography: `physics.earth_like`, `seasons`, `geography.world_shape`, `world_size`, `known_world`.
- Society: `society.governance`, `economic_system`, `slavery`, `literacy`, `religion`.
- Peoples: `peoples.species_diversity` (humans only, a few species, many), `species_relations`, `cultural_inspiration`.
- Narrative: `death_permanence`, `violence_level`, `content_rating`, `anachronisms`.
- Conflict level: peaceful, simmering, active conflict, post-war. This shapes the present-day tension that stage 6 aims at.
- Central characters: protagonist archetype (see `worldbuilding/assets/templates/archetypes.yaml`) and the main source of conflict, or leave to generation.

## Confirming

Before stage 1, show a summary of every flag and choice in a short list and ask "Go?" (guided) or just proceed (YOLO). Do not store credentials or personal data in `project.yaml`: `author` is the only personal field and can stay empty.
