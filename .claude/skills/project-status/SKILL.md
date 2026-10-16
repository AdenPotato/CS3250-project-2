---
name: project-status
description: Report where the project stands - the current sprint and its goal, each user story's status against its acceptance criteria, the rubric with points earned and at risk, missing Scrum evidence, and what to do next. Use at the start of a session or before a sprint review.
---

# /project-status

Read the state, report it, recommend the next move. **Read-only** - this skill changes nothing.

## Gather

1. **Sprint** - which sprint is current (the highest-numbered `scrum/sprint_#/` with a filled `planning.md` and an empty `review.md`; none filled means Sprint 0). Its goal and planned stories.
2. **Stories** - for each of US1-US10, from the code and the evidence, not from memory:
   - Is there code for it? (`grep -rn` for its route or model in `src/`.)
   - Is it merged into `dev`? (`git log dev --oneline --grep US#`.)
   - Does every acceptance criterion have a `passed` row in `tests/manual-tests.md`, or is the story the Selenium one?
3. **Scrum evidence** - for every sprint so far: `planning.md`, `daily_scrums.md`, `review.md`, `retrospective.md` filled and dated (not the `99/99/99` template), and `board.png` present and not the template.
4. **Sprint 0** - the README's Scrum Master line, the scoring table and the sprint plan table: filled or still placeholders.
5. **Deployment** - `Dockerfile`, `docker-compose.yml`, `.env.example` exist; `.env` and `.venv` are in `.gitignore` and absent from `git ls-files`.
6. **Design** - `uml/class.wsd` has at least User, a role, Listing, Reservation, DietaryTag with multiplicities; a `uml/sequence-US<n>.wsd` exists (not the `US#` template) with an `alt` block.
7. **Git** - `git branch -a`, `git tag --list`, `git log dev --merges --format='%an' | sort | uniq -c` (every member should appear).

## Report

Short. Six sections, no preamble:

**Sprint** - which one, its goal, days left.

**Stories** - one row per story planned so far: `US# | status | criteria passing N/M | owner`. Status is `not started`, `in progress`, `in review`, or `done` - and `done` means every criterion passes in Compose with evidence.

**Rubric** - a compact table of anything not yet earned, with points. Then one line: `earned N / at risk M / not started K` out of 100.

**Penalties and gates** - state the **-3** (no Scrum Master in the README) every time until it is cleared, and the self/team evaluation (**+10**, grade held until everyone submits) near the end.

**Drift** - anywhere the plan, the board, the code and the evidence disagree. A story marked done with no test rows. A diagram that no longer matches `models.py`. A sprint with no `board.png`. Name the file.

**Next** - two or three concrete actions, highest points-per-hour first. Prefer work that unblocks others: US1 before everything, the class diagram by the end of Sprint 1, the Compose setup before the first release.

## Judgement

- "The code is written" is `in progress`. A story is `done` only when it passes in Compose and its evidence exists.
- Scrum evidence is 21 points and cannot be reconstructed honestly after the fact. Missing daily scrums for past days are a loss to report, not a gap to back-fill.
- If the clock is short, say which stories are realistically reachable this sprint and which will slip. A team that knows it will miss a story can tell the Product Owner at the review.
