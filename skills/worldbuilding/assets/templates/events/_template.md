---
name: "{{NAME}}"
type: milestone        # war | battle | siege | rebellion | coronation | treaty | founding
                       # dissolution | birth | death | marriage | discovery | invention
                       # prophecy_given | plague | natural_disaster | cataclysm
                       # trade_agreement | milestone | festival | custom

# ── Temporal ──────────────────────────────────────────────────────────────────
# Instant events use 'date'. Duration events use start_date and end_date; omit
# end_date while the event itself is still running (an ongoing date range).
date:                  # { year: , month: , day: , era_prefix: "", display: "" }
start_date:            # for wars, reigns, plagues, etc.
end_date:
date_precision: exact  # exact | approximate | approximate-season | approximate-year | unknown
era: ""                # an era name defined in world/history/calendar.yaml
duration: ""

# ── Classification ────────────────────────────────────────────────────────────
significance: notable # trivial | minor | notable | important | crucial | world-changing (write only these)
scope: local           # personal | family | local | regional | continental | global | cosmic
secrecy: public        # public | rumored | secret | forgotten | mythologized

# ── Cross-references ─────────────────────────────────────────────────────────
participants: []       # [ { entity: "character-slug", role: "role description" } ]
locations: []          # [ "location-slug" ]
organizations: []      # [ { entity: "faction-slug", role: "role description" } ]
items_involved: []     # [ "item-slug" ]

# ── Causality ────────────────────────────────────────────────────────────────
caused_by: []          # [ "event-slug" ]
leads_to: []           # [ "event-slug" ]
root_causes: []        # non-event causes: terrain, climate, resource, belief, person
immediate_trigger: ""  # why now
immediate_consequences: []
long_term_consequences: []   # name things that exist today
traces: []             # present-day marks: slugs of traditions, locations, items, languages, factions.
                       # A tradition listed here must list this event in its origin_events
political_impact: ""
economic_impact: ""    # prose string; structured price and route effects go in world/economy.yaml (shocks)
social_impact: ""
magical_impact: ""     # only if world_flags.magic.present is true
outcome: ambiguous     # decisive | pyrrhic | stalemate | ongoing | ambiguous | reversed | subverted
reliability: well-documented  # firsthand | well-documented | rumored | conflicting-accounts | legend | false-history

# ── Effects still pending ─────────────────────────────────────────────────────
# Only for a finished or dated event whose EFFECTS are still unfolding today; fill
# immediate_consequences and long_term_consequences too. Not for an ongoing date range.
open_ended: ""         # reason string, e.g. "debt crisis still unresolved"

# ── Narrative ────────────────────────────────────────────────────────────────
chapter: ""            # which chapter depicts this
narrative_order:       # order reader learns about this (for non-linear stories)
known_by: []           # who knows about this event
remembered_as: ""      # how it's popularly remembered (may differ from truth)

# ─── DESCRIPTIONS ─────────────────────────────────────────────────────────────
# Optional: for important, crucial or world-changing events, provide a scene description
descriptions:
  machine:
    scene: ""
  human: ""

tags: []
---

## What Happened


## Context & Background


## Consequences & Aftermath


## Notes
