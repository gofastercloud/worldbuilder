---
name: retro
description: Run a post-build retrospective, log reusable patterns, library notes, and pitfalls into the cross-project BM25 knowledge base (~/.agency-kb), and suggest AGENTS.md improvements.
argument-hint: "[optional scope or spec #N]"
---

Run a concise retrospective after a `/next-all` run, completed spec, or repeated reviewer failure so learnings carry over across projects.

1. **Gather signals:**
   - Read `STATUS.md` and recent merged PRs (`agent-gh pr list --state merged --limit 10` or `gh pr list --state merged --limit 10`).
   - Run `python3 .claude/hooks/gtq.py metrics` (if present) to see first-pass reviewer rate, retries, and `.agency/verdicts.csv` failure reasons.
2. **Distil concrete learnings (3–6 max, no fluff):**
   - **Patterns (`--kind pattern`):** architectures, test strategies, or workflows that worked cleanly.
   - **Libraries (`--kind library`):** libraries/CLIs that were easy (or painful) to work with, including exact versions/gotchas.
   - **Pitfalls (`--kind pitfall`):** causes of reviewer `FAIL`s, flaky tests, or subtle bugs to avoid next time.
   - **Project retro (`--kind retro`):** 1 short summary of this build block (what shipped, first-pass rate, key takeaway).
3. **Save to the cross-project knowledge base** (defaults to `~/.agency-kb/`):
   ```
   python3 .claude/hooks/kb.py add --kind <kind> --title "<short title>" --tags "<tag1,tag2>" --project "<repo-name>" --body "<concise markdown>"
   ```
4. **Propose repo rule updates (optional):** if a pitfall is specific to this repo and happened more than once, propose a 1-line addition to `AGENTS.md` for the maintainer to approve — never edit `AGENTS.md` without approval.
5. **Report** in ≤6 lines what was added to the knowledge base and the repo's current first-pass rate.
