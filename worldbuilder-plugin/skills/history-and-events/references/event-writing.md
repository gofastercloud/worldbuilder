# Writing one event

File: `world/events/<slug>.md`, slug is kebab-case and matches the `name`. Use `assets/templates/events/_template.md` and `_schema.yaml`; follow the vocabulary (significance values, types) already used in the project. The schema, template and this file agree; if a project's existing events differ, keep the project's vocabulary but write schema significance values only (never legacy `major`, `critical`, `moderate`).

## Frontmatter, in order

```yaml
name: "Event Name"
type: treaty                 # from the project's allowed types
date: { year: 200, era_prefix: "CE" }      # instant events; durations use start_date and end_date instead
date_precision: exact        # exact | approximate | approximate-year | unknown
era: "Contact Era"
significance: important      # trivial | minor | notable | important | crucial | world-changing
scope: regional              # personal | local | regional | continental | global | cosmic
participants:                # each must exist, alive and present on the date
  - entity: "slug"
    role: "protagonist | antagonist | ally | beneficiary | victim | ..."
organizations:
  - entity: "faction-slug"
    role: "what it did"
locations: ["location-slug"]
primary_location: "location-slug"
caused_by: ["earlier-event-slug"]          # events only, all earlier than this one
root_causes:                               # non-event causes: terrain, climate, resource, belief, person
  - "Resource scarcity: ..."
immediate_trigger: "Why now, specifically"
leads_to: ["later-event-slug"]             # events only, all later; reverse caused_by written there
immediate_consequences:                    # days to a few years
  - "..."
long_term_consequences:                    # generations; name things that exist today
  - "..."
political_impact: "..."
economic_impact: "..."
social_impact: "..."
magical_impact: "..."                      # only if world_flags.magic.present is true; omit otherwise
outcome: decisive            # decisive | pyrrhic | stalemate | ongoing | ambiguous | reversed | subverted
winner: []
loser: []
death_toll: "~12,000 (3 percent of the regional population)"
open_ended: ""               # reason string: effects still unfolding at the present (not an ongoing date range); needs consequences filled
reliability: well-documented # firsthand | well-documented | rumored | conflicting-accounts | legend | false-history
remembered_as: "How the popular memory differs from the truth"
tags: []
descriptions:
  machine: { scene: "One factual sentence" }
  human: ""
```

## Body

`## What Happened`, `## Context & Background` (the causes in prose, naming actors' means, motive and opportunity), `## Consequences & Aftermath` (what changed, by when, and where it can be seen now). Prose must not add facts that contradict the frontmatter.

## Causal fields: how to fill them

- `caused_by`: only events. Write the reverse (`leads_to`) in each cause's file in the same session.
- `root_causes`: everything that is not an event, as concrete statements with a pointer to the file that holds the fact ("Iron ore exhausted at `kharn-mines`"). For an Era 0 root-condition event, this field is the whole explanation.
- `immediate_trigger`: the opportunity. One sentence.
- `immediate_consequences`: what changed within a few years, observable and dated where possible.
- `long_term_consequences`: each item points at something that exists later: a faction, a place, a border, a custom, a price, a grievance. Cross-check by naming the file that records it; if no file records it, either create it or edit the existing file to record it.
- Impact fields: fill the ones that apply. Economic (a prose string, naming slugs; structured price, route and flow effects go in the economy file under `shocks`): production, prices, routes, wealth shift. Social: population, migration, class, religion, language. Political: borders, leadership, laws, alliances. Do not write "none"; leave the field out if truly inapplicable, and be suspicious if all four are empty on a significant event.
- `open_ended`: a non-empty reason string. Use only for effects still unfolding at the present date, with `immediate_consequences` and `long_term_consequences` filled. An event that is itself still running (a war in progress) is a date range: set `start_date` and omit `end_date`. Never use it to avoid thinking through consequences that have had time to occur.

## Participants alive and located

For each person: check birth and death in their file (or birth/death events), age appropriate to the role (a general is an adult; an heir to a throne may be a child), travel time from their previous recorded position, and that they have not already died in a different event. For each faction: existed on the date (founding precedes the event), and was in the place. If a character's file does not record a birth or death, add one rather than guess.

## Dates

- Cause earlier than effect. Same-day causes only when truly simultaneous.
- Duration events: set `start_date` and `end_date`; the `end_date` is not before the start. A cause may predate a long event; its effects may begin before it ends but state which.
- Gaps: fill plausible lag between cause and effect (months for a rumour to become a war, years for a discovery to spread, decades for institutions).
- When uncertain, set `date_precision` and an approximate date rather than leaving it blank. Undated events cannot be checked.

## Reciprocity after writing

Edit: each `caused_by` event's `leads_to`; each `leads_to` event's `caused_by`; each location (history note, ruins, population); each faction (events list, founding, dissolution, leaders); each character (events list, death); the economy and species files where the event changes them. Then run world-validate.
