---
name: "{{NAME}}"
aliases: []
role: supporting
status: alive
species: "human"
race: ""
ethnicity: ""              # cultural/ethnic background (e.g. "Valdrian", "Highland Dwarf")
age: ""
gender: ""
first_appearance: ""
last_appearance: ""
location: ""
faction: ""
relationships: []
arc: ""
traits: []
skills: []
inventory: []
stats: {}
secrets: []

# ─── FAMILY LINKS ─────────────────────────────────────────────────────────────
# These build the family tree. Use character slugs.
family_links:
  father: ""
  mother: ""
  spouse: []
  children: []
  siblings: []
  lineage: ""
  birth_order: 0
  legitimacy: legitimate    # legitimate | illegitimate | adopted | claimed | unknown
  title_inherited: ""

# ─── LANGUAGE ──────────────────────────────────────────────────────────────────
languages:
  native: ""               # language slug for mother tongue
  spoken: []               # additional languages the character speaks
  literacy: []             # languages they can read/write (may differ from spoken)

# ─── VOICE ────────────────────────────────────────────────────────────────────
# Voice characteristics for TTS generation (Qwen3-TTS VoiceDesign)
voice:
  description: ""           # free-text voice description (feeds into TTS instruct)
  tags: []                  # [male/female, deep/high, warm/cold, raspy/smooth, young/old, etc.]
  accent: ""               # accent for TTS (e.g. "Scottish", "Welsh", "Brooklyn", "clipped military")
  dialect: ""              # speech register (e.g. "formal court speech", "rural colloquial")
  sample_text: ""           # a characteristic line of dialogue for this character (1-2 sentences)
  instruct: ""             # optional: manual TTS instruct override (bypasses auto-generation)

# ─── DESCRIPTIONS ─────────────────────────────────────────────────────────────
# Triple descriptions: machine (source truth), human (styled prose), image_prompt (illustration)
descriptions:
  machine:
    physique: ""
    face: ""
    attire: ""
    voice: ""
    demeanor: ""
  human: ""
  image_prompt: ""

tags: []
---

## Physical Description


## Personality


## Backstory


## Motivations & Goals


## Voice & Mannerisms
<!-- How they speak, verbal tics, body language, catchphrases -->


## Family & Lineage


## Notes
