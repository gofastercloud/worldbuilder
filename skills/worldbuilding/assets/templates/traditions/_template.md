---
name: "{{NAME}}"
aliases: []
kind: legend           # myth | legend | folktale | custom | ritual | festival | superstition
                       # taboo | proverb | song | oath | holy-day | other
status: living         # living | fading | forgotten | revived | suppressed

# ── Truth chain: what really happened ────────────────────────────────────────
origin_events: []      # [ "event-slug" ]  REAL events it descends from; each event lists this in `traces`
origin_unknown: ""     # ONLY if the origin is a deliberate mystery; say why. Leave empty otherwise

# ── Memory chain: what survives, and how it is bent ──────────────────────────
fidelity: simplified   # accurate | simplified | embellished | conflated | inverted | garbled | invented
distortions: []        # how it differs from what happened
distortion_causes: []  # why: telescoping, hero-fusion, moralising, propaganda, mistranslation,
                       #      taboo-induced silence, survivor bias
reliability: legend    # firsthand | well-documented | rumored | conflicting-accounts | legend | false-history
claims_supernatural: false   # a BELIEF, not a fact about the world

# ── Who, where, how ──────────────────────────────────────────────────────────
held_by: []            # [ "faction-or-race-or-species-slug" ]
regions: []            # [ "location-slug" ]  where it is found
places: []             # [ "location-slug" ]  places whose treatment it governs (taboo, pilgrimage)
language: ""           # language slug
first_attested:        # { year: , era_prefix: "" [, month: , day: ] }
transmission: oral     # oral | written | ritual | art | mixed
drives: []             # observable present-day behaviours: festival dates, taboos, naming, avoidance

# ── Relations ────────────────────────────────────────────────────────────────
related: []            # [ "tradition-slug" ]
contradicts: []        # [ "tradition-slug" ]  (reciprocal)

descriptions:
  machine: ""
  human: ""

tags: []
---

## What Is Told or Done


## What Really Happened


## How It Changed


## Present-Day Effects
