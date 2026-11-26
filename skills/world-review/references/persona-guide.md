# Persona guide

Persona definitions live in the worldbuilding skill, relative to the plugin root: `skills/worldbuilding/assets/editors/<name>.yaml`. Read the file for each persona you run. Each has `role`, `personality`, `context_requirements`, `checks` (id, severity, method) and `output_format`. The overview and check tables are in `skills/worldbuilding/references/editors.md`.

## Roster, order and cross-links

| Order | Persona (file) | Use when | Also load |
|---|---|---|---|
| 1 | worldrules (`worldrules.yaml`) | Tech, magic or physics may break flags; any magic on the page | `magic-systems`; `world-validate` (mandatory) |
| 2 | geography (`geography.yaml`) | Travel, directions, terrain, weather, place descriptions | `geography-and-climate` (travel in its `transport-and-travel` reference); `world-validate` graph `path` |
| 3 | continuity (`continuity.yaml`) | Dates, ages, who is alive or where, facts repeated across chapters | `history-and-events`; `world-validate` (mandatory) |
| 4 | character (`character.yaml`) | Behaviour, motive, knowledge, arc | `peoples` |
| 5 | sensitivity (`sensitivity.yaml`) | Cultures, groups, tropes, content rating | `peoples`, `folklore-and-traditions` for cultures drawn from real ones |
| on demand | plot (`plot.yaml`) | Logic, setups and payoffs, deus ex machina | `history-and-events` (causal chains), `world-validate` `why` |
| on demand | dialogue (`dialogue.yaml`) | Speech patterns, period language, samey voices | `peoples` (`language-and-names`, voice and accent fields) |
| on demand | pacing (`pacing.yaml`) | Rhythm, tension, chapter length, saggy middle | none |
| on demand | prose (`prose.yaml`) | Line-level craft | none |

Other cross-links to use when a persona's finding touches a layer: economy details in dialogue or scene (prices, wages, goods) go to `economy-and-trade`; legends or customs characters cite go to `folklore-and-traditions`; a character's knowledge of past events is checked against the event's traces and any tradition (people remember through distortion, not the record).

## Choosing personas from the request

| User says | Run |
|---|---|
| "continuity check", "does this match the world" | continuity, worldrules, geography |
| "world rules check", "does the magic work" | worldrules (plus magic-systems cross-check) |
| "travel", "distances", "weather" | geography |
| "pacing", "drags", "rushed" | pacing (add plot for setup and payoff) |
| "dialogue", "everyone sounds the same" | dialogue (add character) |
| "prose critique", "line edit" | prose |
| "sensitivity read" | sensitivity |
| "plot holes" | plot, continuity |
| "review my chapter", "manuscript review", "edit this" with no detail | default order of five, then ask whether to add plot, dialogue, pacing, prose |

## What each persona leans on in the world

- worldrules: `world_flags` in `project.yaml`, magic system files (costs, limits), technology keywords per flag, `physics` flag.
- geography: location hierarchy and `routes`, `elevation_m`, climate profiles, transport allowed by flags, calendar for season.
- continuity: events and calendar, character birth, death and status, faction roles by date, prior chapters' fact sheet.
- character: character files (traits, goals, relationships, arc), what each character could know at that date.
- sensitivity: `cultural_inspiration` and content rating in `project.yaml`, species, race and culture files.
- plot, pacing: arc files, chapter order, setups introduced earlier.
- dialogue: character `voice` fields, origin location `regional_defaults`, language files.
- prose: the project's prose style cascade (`worldbuilding/references/style-system.md`); judge the text against the chosen style, not a generic ideal.

## Persona boundaries

Keep to each persona's one job. Typical boundary cases:

- A dead character speaking: continuity reports it; dialogue does not.
- A musket in a no-gunpowder world: worldrules, not continuity.
- A character knowing a secret: character (`knowledge-violation`); the plot persona only if the logic of the plot depends on it.
- Repeated word: prose. Repeated fact that changes: continuity.

When a finding fits two personas, report it once under the earlier in run order and cross-reference it from the other.
