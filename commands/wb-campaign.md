---
description: Build a D&D 5e-compatible campaign, session, encounter or quest set in a specific era or around an event
---

Use the `writing` skill in campaign mode on the worldbuilding project in the current folder. Request: $ARGUMENTS

1. Run `python3 skills/writing/scripts/story_campaign.py campaign <project>` anchored to the requested `--era <prefix> [--year Y]`, `--event <slug>`, `--tradition <slug>`, or `--present` (with `--level 1-4`, `--length one-shot|short|custom`, `--sessions`, `--location`, `--tone`, `--themes`) to assemble a spoiler-free D&D 5e campaign brief.
2. Expand the brief into playable sessions with 5e-calibrated DCs/CRs, hub routes and travel times, living NPCs with motives, d6/d8 rumour tables (true vs. distorted traditions), faction clocks, economy hooks, and magic-gate rules.
3. Include a consequence-tracking plan that writes player-caused changes back to `world/events/` with `caused_by` and re-validates with `world-validate`.
