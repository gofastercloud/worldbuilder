---
name: "{{NAME}}"
type: milestone        # war | battle | siege | rebellion | coronation | treaty | founding
                       # dissolution | birth | death | marriage | discovery | invention
                       # prophecy_given | plague | natural_disaster | cataclysm
                       # trade_agreement | milestone

# ── Temporal ──────────────────────────────────────────────────────────────────
# For instant events, use 'date'. For duration events, use start_date/end_date.
date:                  # { year: , month: , day: , era_prefix: "", display: "" }
start_date:            # for wars, reigns, plagues, etc.
end_date:
era: ""
duration: ""

# ── Classification ────────────────────────────────────────────────────────────
significance: moderate # trivial | minor | moderate | major | world-changing
scope: local           # personal | local | regional | national | continental | global | cosmic
secrecy: public        # public | rumored | secret | forgotten | mythologized

# ── Cross-references ─────────────────────────────────────────────────────────
participants: []       # [ { entity: "character-slug", role: "role description" } ]
locations: []          # [ "location-slug" ]
organizations: []      # [ { entity: "faction-slug", role: "role description" } ]
items_involved: []     # [ "item-slug" ]

# ── Causality ────────────────────────────────────────────────────────────────
caused_by: []          # [ "event-slug" ]
leads_to: []           # [ "event-slug" ]

# ── Narrative ────────────────────────────────────────────────────────────────
chapter: ""            # which chapter depicts this
narrative_order:       # order reader learns about this (for non-linear stories)
known_by: []           # who knows about this event
remembered_as: ""      # how it's popularly remembered (may differ from truth)

# ─── DESCRIPTIONS ─────────────────────────────────────────────────────────────
# Optional: for major/world-changing events, provide a scene description
descriptions:
  machine:
    scene: ""
  human: ""
  image_prompt: ""

tags: []
---

## What Happened


## Context & Background


## Consequences & Aftermath


## Notes
