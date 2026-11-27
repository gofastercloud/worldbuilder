---
name: handoff
description: Write STATUS.md so a fresh session can continue, then hand over. Use at the end of a work block, after a batch, or when the context guard says so.
---

Rewrite `STATUS.md` (at most 40 lines; replace stale content, don't append) with exactly these sections:

```
# Status (<date> <time>)
## Goal            one line: what this work block is for
## In flight       ticket -> branch -> state (implementing / in review / PR #n)
## Waiting on you  PRs to merge, questions (with issue links)
## Decisions       only ones not recorded in an issue or ADR
## Next            the first 1-3 actions for the next session
```

Then:
1. Make sure every decision that matters is in an issue, PR, or ADR, not only in this conversation.
2. If `.claude/hooks/gtq.py` is present, run `python3 .claude/hooks/gtq.py report --days 1 --by agent_type` and add the total to the Goal line as `(spend today: $X)`.
3. Tell the maintainer: "STATUS.md is current. Start a fresh session (`/clear` in Claude Code) to continue." Don't keep working after the handoff.
