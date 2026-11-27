---
name: spec
description: Turn an idea into a spec issue and context-sized tickets on GitHub using agent-gh. User-invoked.
disable-model-invocation: true
argument-hint: "<one-line idea>"
---

Turn `$ARGUMENTS` into tickets an `implementer` can finish in one fresh session. Use `agent-gh` when installed (Groundhog), otherwise fall back to `gh`.

0. **Consult the knowledge base.** If `.claude/hooks/kb.py` (or `agency-kb`) is available, run `python3 .claude/hooks/kb.py search "<keywords from idea>" --top 5` so proven patterns, preferred libraries, and past pitfalls from previous projects inform your design.
1. **Grill.** Ask the maintainer one question at a time, at most 10, until scope, non-goals, interfaces, and the definition of done are unambiguous. Use the `scout` role for anything the code can answer; don't ask the maintainer what you can look up.
2. **Spec.** Create one issue labelled `spec` via `agent-gh issue create --label spec`: goal, non-goals, decisions (with why), interfaces, risks. Keep it under 60 lines.
3. **Tickets.** Slice into vertical slices: each one is a demonstrable behaviour that touches every layer it needs. One issue per slice, using `.github/ISSUE_TEMPLATE/ticket.md`:
   - acceptance criteria, testable;
   - the verify command;
   - the files it is expected to touch;
   - `Blocked by #n` lines;
   - a size of S or M. Anything bigger is two tickets. "Phase 1 of 3" means the slice is too big.
4. Show the maintainer the ticket list. Once they approve it, label every ticket `ready-for-agent` (`agent-gh issue edit <N> --add-label ready-for-agent`), blocked ones included: `/next` skips a ticket until its blockers are closed. Link every ticket from the spec issue.
5. Add the spec and tickets to `STATUS.md` and tell the maintainer how many tickets are ready.

Write a ticket body so a `reviewer` who never saw this conversation can judge the result from it alone.
