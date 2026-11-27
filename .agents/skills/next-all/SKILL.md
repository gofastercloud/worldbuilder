---
name: next-all
description: Continuously work through ready-for-agent tickets batch by batch until the backlog is drained, a human approval/blocker is hit, or context/usage limits are reached.
argument-hint: "[max tickets, default 10]"
---

Run the `/next` workflow continuously in batches (up to 3 disjoint unblocked tickets per batch) until a stop condition is reached. Cap total tickets processed in one run at `$ARGUMENTS` (default `10`).

## Loop
1. Follow every rule and step in `/next` (`agent-git`, `agent-gh`, trusted maintainer `--author <owner>`, `implementer` in isolated worktree + offline `agent-box` verify, fresh-context `reviewer`, and per-repo `autonomous` vs `human-review` shipping).
2. After each batch completes and `STATUS.md` is updated, check **Stop Conditions** before starting the next batch.
3. Keep orchestrator responses between batches brief (≤4 lines) to preserve context.

## Stop Conditions (halt immediately when ANY triggers)
1. **Backlog drained:** no open, unblocked `ready-for-agent` tickets remain.
2. **Human gate / approval needed:**
   - Any ticket reports `BLOCKED:` or fails `reviewer` twice → label it `needs-human`, record the question in `STATUS.md`, and **stop** so the maintainer can unblock it.
   - On a `human-review` repo, once **3** open draft PRs are waiting for maintainer approval, **stop** (never flood the review queue).
   - Any ticket or diff touches protected paths (`.claude/`, `.agents/`, `.github/`, `AGENTS.md`, `CLAUDE.md`, `STATUS.md`) or asks for a new dependency, CI, IaC, or production change → **stop** and ask the maintainer.
3. **Context budget (~150k tokens):** run `/handoff` (rewrite `STATUS.md` ≤40 lines) and **stop** so the next session continues cleanly from a fresh context.
4. **Subscription usage pause (Claude Code):** obey the usage-stop hook immediately (schedule the resume and end the turn).
5. **Ticket cap reached:** processed `$ARGUMENTS` (default `10`) tickets in this run → update `STATUS.md` and report summary.

## Final Report (at most 10 lines)
List: tickets merged (with PR links), PRs awaiting human review, any `needs-human` blockers, remaining `ready-for-agent` count, and the stop reason.
