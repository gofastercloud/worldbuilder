---
description: Develop a short story, novel or series premise centred around an event, myth/tradition, or era
---

Use the `writing` skill in story and series mode on the worldbuilding project in the current folder. Request: $ARGUMENTS

1. Run `python3 skills/writing/scripts/story_campaign.py story <project>` anchored to the requested `--event <slug>`, `--tradition <slug>`, `--era <prefix> [--start-year Y]`, or `--present` (with optional `--location`, `--protagonist`, `--words`, `--tone`, `--subgenre`) to assemble a spoiler-free, dated story brief.
2. Build the premise from the brief's causal ancestry, open-ended tensions, and gap between real history and remembered traditions, then outline or draft the prose on request.
3. Record any new canon characters, items, or events back into `world/` and validate with `world-validate`.
