# Additional deterministic checks wanted in the validator (report only, not implemented)

1. **Undefined era prefix:** any event date whose `era_prefix` is not in the calendar's eras (silently makes comparisons unreliable).
2. **Era monotonicity:** calendar `sort_order` unique and increasing; `start_year`/`end_year` within an era consistent; months' days sum to `days_per_year`.
3. **Event dates inside the era:** event `era` name matches the era of its date prefix; year within the era's start and end.
4. **No future events:** events dated after the project's recorded present (unless typed prophecy).
5. **Participants vs lifespan on the date:** characters alive at the event date and, for births/deaths, consistent with `type` (a `death` event for someone with a different death date).
6. **Faction and location existence:** factions in `organizations`/`primary_factions` founded before the event and not dissolved; locations founded.
7. **Reciprocity of `caused_by`/`leads_to`:** already warned; also flag `leads_to` entries that are prose rather than slugs.
8. **Significant events without consequences:** significance important or higher with empty `immediate_consequences` or `long_term_consequences`, or with none of the four impact fields; `open_ended` set while `end_date` is in the past.
9. **Cause lag:** cause and effect with identical dates for non-same-day types, or a lag far shorter than a minimal plausible lag (warning only).
10. **Duration sanity:** `end_date` earlier than `start_date` (exists); `duration` string inconsistent with the date span.
11. **Chain terminus:** significant events whose descendants never reach any non-event entity (no place, faction or route changed).
12. **Root-condition declaration:** events with no `caused_by` and no `root_causes` beyond a declared limit (partly covered by `unrooted`).
13. **Flag vs event type:** invention/discovery of technology flagged false; magical impact when magic absent; `cataclysm` with magical cause in non-magic world.
14. **Dense clusters and long gaps:** more than N significant events in a decade or a span longer than M years with none (informational).
15. **Rival accounts:** two events with the same participants, location and overlapping dates but different outcomes and no `reliability` marker.
16. **Undated events:** events with no `date` or `start_date`, counted and listed.
17. **Death toll vs population:** `death_toll` or casualty counts exceeding the recorded regional population.
18. **Stale slug references in `leads_to`/`caused_by` pointing to non-events** (location or character slugs in event-only fields).
