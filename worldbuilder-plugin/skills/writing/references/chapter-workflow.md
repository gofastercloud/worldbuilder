# Chapter workflow

## Setup

- Chapter files live in `story/chapters/` (template fields: title, number, book, pov, location, timeline_start, timeline_end, characters_present, status outline|draft|revised|final, summary, scene_breaks, notes). Books in `story/books/`. If none exists, create the file from `assets/templates/chapters/_template.md` with the user's agreement.
- `pov` and `location` must be real slugs. `characters_present` too.

## 1. Plan beats

1. Read the arc file(s) for this chapter: setup, inciting_incident, rising_action, midpoint, crisis, climax, resolution, foreshadowing, payoffs, unresolved.
2. Decide which beat this chapter carries, and what must have changed by its end.
3. For every beat, name the world fact that makes it possible and the motive that drives it. If the beat needs a fact the world lacks, add it to the world first (with causes), do not hand-wave it in prose.
4. Produce a beat list: scene, date, place, POV, goal, obstacle, outcome, new information revealed, who learns it.
5. Show the beat list to the user and wait for approval when the chapter is substantial or the user asked to see an outline.

## 2. Write scene by scene

For each scene:
- Open with the context brief for that scene's date and place.
- Ground the reader quickly: place, season, weather and light from the climate data; one or two details from the machine description that only this world has.
- POV discipline: perception, vocabulary and assumptions belong to the POV character (culture, literacy, species senses). They notice what they would notice.
- Cause and consequence on the page: characters act from motive, with the means the world gives them; the outcome changes something that persists.
- Dialogue: see `dialogue-and-voice.md`.
- Length follows style `scene_length` and `chapter_length`.
- Keep a running list of facts you introduce (names, objects, places, injuries, promises, deaths, rumours).

## 3. Consistency with machine descriptions

Before finalising, compare every physical, numeric and relational claim against the entity files: appearance, age on the scene date, distances, travel times, titles, who leads what, what a place contains. A mismatch is fixed in the prose unless it is a deliberate canon change, in which case update the entity and its causes.

## 4. Continuity pass

1. Re-read the chapter against the brief: dates, knowledge, geography, flags.
2. Load `world-validate` and run the checker on the project. Fix errors, explain warnings.
3. Load `world-review` and run at least the continuity, worldrules, geography and character personas; dialogue for dialogue-heavy chapters.
4. Respond to each finding: fix, justify, or ask the user.

## 5. Write back

Use the list of introduced facts. For each: record or cut (see SKILL.md write-back). Then:
- New or changed events: fill `caused_by`, `leads_to` or `open_ended`, impacts, `traces`; run `graph.py why <event>` and `impact <event>`.
- New characters, locations, items: create files from templates with causes and both-way links.
- Changed relationships or deaths: update both characters, factions, lineages, and the death event.
- Traditions: if the story creates a rumour or legend, record it with its origin event and distortion mechanism; if a character learns the truth, update who holds which version.
- Chapter and arc metadata: status, summary, characters_present, arc beats, foreshadowing and payoffs.
- Rerun `validate.py` and report.

## 6. Revision

When revising, treat prose edits that touch facts as world edits: run `impact` first. Never silently change a fact in one chapter that another chapter depends on; search chapters for the old fact.
