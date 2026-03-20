# WorldBuilder — Editor Personae

Each editor is a specialized review agent with a focused mandate. Rather than
one monolithic "edit everything" pass, you run targeted editors that each check
for specific classes of problems.

## How to Use

```bash
python tools/worldbuilder.py edit <editor_name> [--chapter <num>] [--project <path>]
```

Or load an editor's prompt into Claude directly:
```
Load the continuity editor from editors/continuity.yaml and review chapters 1-5.
```

## Editor Roster

| Editor | Focus | Catches |
|--------|-------|---------|
| continuity | Timeline & fact consistency | Dead characters appearing, anachronisms, timeline contradictions |
| character | Character voice & behavior | OOC behavior, voice drift, trait contradictions, forgotten arcs |
| geography | Spatial & travel logic | Impossible travel times, location contradictions, lost descriptions |
| worldrules | Magic/tech/physics rules | Magic system violations, tech anachronisms, physics inconsistencies |
| pacing | Story rhythm & structure | Pacing issues, tension drops, arc stalls, chapter length imbalance |
| dialogue | Speech patterns & voice | Voice consistency, period-inappropriate language, talking-head scenes |
| sensitivity | Cultural & representation | Stereotypes, harmful tropes, cultural insensitivity |
| prose | Line-level writing quality | Purple prose, repetition, weak verbs, show-don't-tell violations |
| plot | Plot holes & logic | Unresolved setups, logical gaps, deus ex machina, forgotten threads |

## Editor Design Principles

1. **One job, done well** — each editor checks for ONE class of problem
2. **Data-driven** — editors load relevant world data (characters, flags, timeline)
3. **Specific output** — editors produce actionable issue lists, not vague suggestions
4. **Non-destructive** — editors report problems; they don't rewrite (unless asked)
5. **Composable** — run one editor or chain them all in sequence
