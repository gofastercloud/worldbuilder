# Calendar and eras

## Files

- `project.yaml` has a short `calendar:` block (`name`, `epoch`, `format`).
- `world/history/calendar.yaml` holds the working calendar the checker reads (eras, months, week, date format). Create it if absent.

## Template

```yaml
name: "<Calendar name>"
eras:
  - name: "<Era name>"
    prefix: "<short unique prefix>"   # used in every date in this era
    sort_order: 1                     # strictly increasing with real time
    start_year: 1
    end_year: 3000                    # null for the present era
    description: "<what defines this era and what ends it>"
months:
  - { name: "<Month>", number: 1, days: 30 }
days_per_year: 365                    # must equal the sum of month days
date_format: "{era} {year}.{month}.{day}"
week: ["<day>", "..."]                # optional
```

## Rules

1. Prefixes are unique and short. `sort_order` is the only thing that orders eras, so it must follow real chronology, not the order you thought of them.
2. Years usually restart at 1 in each era. Same-prefix comparison uses the year; cross-prefix comparison uses `sort_order`. A date in a prefix that is not in the calendar cannot be compared and will hide errors.
3. Month days must sum to `days_per_year`. Check the arithmetic, and that the calendar suits the world: a planet's year, moons and seasons (from the geography and astronomy flags) should drive month and year length. Name months and days after something in the world (a harvest, a moon, a god).
4. Era boundaries are caused. Each era's `description` states what ends it; an event (founding, collapse, discovery, contact) must be dated at or just before the boundary and linked to the next era's first events.
5. Era length reflects the pace of change. Long eras need slow processes inside them (migrations, institutions); short eras need a violent or rapid cause.
6. Scale to lifespans. Count generations: era length divided by typical generation length. Dynasties and institutions must have plausible numbers of rulers.
7. Fix the present: say which era is current and its approximate year, and record it. If the world is a series or campaign, record the story's start date too.
8. Adding an era later: add it to the calendar with a `sort_order`, renumber others if it goes in the middle, and re-check dates in affected events.
9. Keep alternate calendars (another culture's reckoning) as `display` strings or in prose, with one canonical machine calendar for ordering.

## Converting

When two cultures count years differently, record one canonical `epoch` in `project.yaml` and give the conversion in the other culture's faction or location file, not in each event.
