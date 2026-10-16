---
name: sprint-close
description: Close a sprint - verify its stories, Scrum records, board screenshot, release tag and burndown actually exist, then hand off to the next sprint's planning. Use when a sprint ends, not to check status mid-sprint.
argument-hint: "[sprint number]"
---

# /sprint-close

Move the project from one sprint to the next. A sprint closes on **evidence that exists**, not on a feeling that the work is mostly done.

## Steps

1. **Which sprint.** From `$ARGUMENTS`, or the current one (see `/project-status`).

2. **Verify each item.** Check the artifact; do not ask whether it is finished.

   | Item | Verify |
   |---|---|
   | Stories | Every story in the sprint plan: merged into `dev`, every criterion with a latest `passed` row in `tests/manual-tests.md` (or the Selenium test) |
   | Release | `git tag --list` has `vN` on a merge commit on `main` ([`/release`](../release/SKILL.md)) |
   | Planning | `scrum/sprint_N/planning.md` dated, with the goal, the stories and a task breakdown with owners |
   | Daily scrums | `daily_scrums.md` has dated entries across the sprint, none left as `99/99/99` |
   | Review | `review.md` dated, each planned story marked done or returned to the backlog |
   | Retrospective | `retrospective.md` dated, actions with owners; from Sprint 2, the previous actions checked |
   | Board | `scrum/sprint_N/board.png` is a real screenshot taken this sprint (check the file date; the template ships one) |
   | Design (Sprint 1) | `uml/class.wsd` and a `uml/sequence-US<n>.wsd` exist, render, and match the code |
   | Burndown | the actual points remaining after this sprint entered in `burndown.xlsx` |
   | PRs | `gh pr list --state merged --base dev` - each reviewed by someone other than its author |

3. **Report what is missing.** List the gaps and stop. Do not close a sprint to make the tracker look better. A missing record cannot be honestly back-filled after the fact - say so, and let the Scrum Master decide (AGENTS.md rule 9).

4. **Unfinished stories.** Each one goes back to the backlog and into a later sprint. Recompute the remaining points and say how the plan for the next sprint changes, respecting capacity and dependencies.

5. **Hand off.** Say what the next sprint needs: its planned stories from the release plan, adjusted by step 4, and the retro actions it must carry out. Then point to `/scrum-notes planning <N+1>`.

## After Sprint 3

The final close also checks:

- `burndown.xlsx` has all three lines - ideal, planned, actual - and one or two sentences explaining any gap between planned and actual. Export a `burndown.png` if the team prefers it.
- All seven required stories pass in the `v3` deployment.
- **Every member has submitted the self and team evaluation** - **+10**, and the team's grade is held until all are in. Remind the team by name.
