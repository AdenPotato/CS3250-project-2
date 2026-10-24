# CS3250 Project 2 - CampusEats

A Flask web application that connects campus food vendors who have surplus food with students who want it. Vendors post listings with a pickup window, students reserve portions and get a pickup code, vendors confirm pickups. Built for CS3250 (Software Development Methods and Tools) under **Scrum**: a planning Sprint 0, then three one-week sprints, each ending in a tagged release (v1, v2, v3).

**Stack (fixed by the assignment - not a choice):** Python 3, Flask, PostgreSQL (SQLite and in-memory storage are not accepted), Docker Compose. Allowed extensions: Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate. One Selenium black box test.

This file is the entry point for every AI coding agent (Codex, Gemini, Cursor, Copilot, Claude Code and others). `CLAUDE.md` imports it, so edit the rules here, not there.

## Where things are

| Path | What |
|---|---|
| [README.md](README.md) | The assignment: backlog, acceptance criteria, sprint rules, rubric. **The source of truth.** Also holds the backlog scoring table, the release plan and the Scrum Master. |
| `src/app/` | The application package: `__init__.py` (the `create_app` factory, `db`, `login_manager`, `csrf`), `models.py`, `routes.py` (the `main` blueprint), `templates/` (`base.html` and pages), `static/`. `forms.py` arrives with the first form. Run from `src/` with `flask --app app run`. |
| `requirements.txt` | Pinned direct dependencies. The PostgreSQL driver is psycopg 3, the SQLAlchemy 2.1 default for `postgresql://` URLs. |
| `src/seed.py` | Seed accounts and sample listings, created automatically on first start. Planned. |
| `uml/class.wsd` | Domain model: User, role, Listing, Reservation, DietaryTag. |
| `uml/sequence-US#.wsd` | One story's full flow, browser to PostgreSQL, with an alternative path. |
| `scrum/sprint_#/` | `planning.md`, `daily_scrums.md`, `review.md`, `retrospective.md`, `board.png`. |
| `tests/` | The Selenium test and `manual-tests.md`. |
| `Dockerfile`, `docker-compose.yml` | `db` (postgres + named volume) and `web` (waits for `db`). |
| `.github/workflows/build-and-test.yml` | The `build-and-test` check on PRs into `dev`: compiles `src/`, builds and starts the Compose stack, runs `pytest tests`. |
| `.env.example` | Placeholder values for `DATABASE_URL` and `SECRET_KEY`. `.env` itself is never committed. |
| `burndown.xlsx` | Ideal, planned and actual lines, filled at the end. |
| `.agents/skills/` | Workflow skills, one `SKILL.md` per folder. |
| `.agents/agents/` | Role briefs: `app`, `ui`, `release`, `scrum`. |

## Rules that bind every session

1. **The acceptance criteria are the definition of done.** A story is done only when every one of its criteria passes in the Docker Compose deployment. Every task maps to a user story (US1-US10) or a rubric line in the [README](README.md#rubric). Work that maps to neither is out of scope until a teammate says otherwise.
2. **Required before optional.** US1-US7 are 49 points; US8-US10 are bonus. No optional story is started while a required one in the current sprint is unfinished.
3. **Respect dependencies.** A story cannot start until every story it depends on is merged into `dev` and passing its criteria. The "Depends on" column in the backlog is binding.
4. **Every story leaves test evidence.** The Selenium story is covered by its test; every other implemented story gets rows in `tests/manual-tests.md`, re-tested before each release.
5. **Never commit to `main`.** `main` is reached only by merging `dev` at the end of a sprint, and the merge commit is tagged `v1`, `v2` or `v3`.
6. **Never commit secrets.** `.env` and `.venv` are in `.gitignore`. The database URL and secret key are read from the environment; `.env.example` holds placeholders only.
7. **Ask when the requirement is ambiguous.** The assignment is the source of truth; the instructor is the Product Owner. When it is silent, ask a teammate rather than inventing a requirement.
8. **AI agents never commit.** No AI agent runs `git commit`, `git push`, `git merge` or `git tag`, or merges PRs - it edits files and a teammate reviews and commits them. The one exception: when a teammate asks, an agent may open a PR into `dev` for a GitHub issue, from a branch the teammate has pushed, with the issue linked in the body. Never add a `Co-Authored-By` trailer or a "Generated with" line for any AI tool to a commit message, PR, or issue, including drafts written for a teammate.
9. **Scrum records are the team's, written on time.** An agent may draft a scrum record from what a teammate tells it; it never invents participants, dates, or what was said. A record written after the fact carries the real date of the event, not today's.
10. **Never break a graded artifact to make a change convenient.** The file names, the folder layout, the `manual-tests.md` table format and the scrum record files come from the assignment; changing one needs a stated reason.

## Git model

| Branch | Rule |
|---|---|
| `main` | Releases only. Reached by a PR from `dev` at sprint end, merged with **"Create a merge commit"** (the only method the `Protect main` ruleset allows). The merge commit is tagged `v1`/`v2`/`v3`. |
| `dev` | The default branch and integration. Everything lands here through a reviewed PR merged with **"Squash and merge"** (the only method the `Protect dev` ruleset allows). |
| `<issue#>-short-slug` | One task, off `dev`, named with its GitHub issue number, e.g. `25-reservation-model` for issue #25. Deleted automatically after merge. |

- PRs into `dev` are reviewed and approved by a teammate **other than the author** (enforced: 1 approval). `dev`'s history must show work from every team member - spread the work so it does.
- Each PR links the GitHub issue it closes (`Closes #12`).
- Commits and PR titles: `CS-<issue number> <message>` - one logical change, present tense, lowercase, no trailing period: `CS-12 add reservation model with pickup code`. The squash commit on `dev` takes the PR title, so the title matters most.
- The `build-and-test` check must pass before a PR into `dev` merges. It needs `.env.example` to hold values Compose can start with, since CI copies it to `.env`.
- Never rewrite pushed history.

## Skills

Skills live in `.agents/skills/<name>/SKILL.md`. When a skill or doc says `/new-model`, it means "read and follow `.agents/skills/new-model/SKILL.md`". Read the whole skill before starting its first step.

| Skill | Use when |
|---|---|
| `session-start` | Opening a working session, before any code. |
| `project-status` | Reporting where the project stands: sprint, stories, rubric, Scrum evidence. |
| `backlog` | Sprint 0: scoring the backlog and writing the release plan. |
| `scrum-notes` | Recording a sprint planning, daily scrum, review or retrospective. |
| `new-design` | A requirement is ambiguous, or a change touches model, route and template at once. |
| `new-model` | Changing a SQLAlchemy model or the schema. |
| `new-route` | Implementing a user story's page or flow. |
| `uml` | Writing or refreshing the class or sequence diagram. |
| `selenium` | Writing or running the automated black box test. |
| `test-log` | Recording manual test results in `tests/manual-tests.md`. |
| `qa-steps` | Writing a QA script for the PR reviewer. |
| `new-issue` | Opening a GitHub issue a teammate approved. |
| `release` | Clean-clone Compose check, merging `dev` into `main`, tagging the sprint release. |
| `sprint-close` | Verifying a sprint's deliverables and evidence before the next sprint starts. |

## Roles

For focused work, take on the matching brief in `.agents/agents/`: `app.md` for Python under `src/`, `ui.md` for templates and CSS, `release.md` for Docker, Compose, env config and tags, `scrum.md` for the `scrum/` folder, the board and the burndown.

## Guardrails

Claude Code enforces these through `.claude/settings.json`. Other tools must follow them by hand.

- **Never read** `.env` files, `*.pem` or `*.key`.
- **Never run** `git push --force` (or `-f`, `--force-with-lease`), `git push origin main`, or `docker compose down -v` without being asked (it deletes the database volume).
- **Ask first** before `gh issue create`, `gh pr create`, `gh pr merge`, creating a branch, `git merge`, `git tag`, `docker compose up`, `docker compose down`, or `docker build`.
- **Free to run:** `pytest`, `docker compose ps`, `docker compose logs`, `pip install -r requirements.txt`, and read-only git (`status`, `diff`, `log`, `branch`).

## Running the app

From the repo root:

```bash
cp .env.example .env              # once, then fill in real values
docker compose up --build         # http://localhost:5000
docker compose down               # stop, keep the data
docker compose down -v            # stop and wipe the database volume - after a model change
```

The seed accounts are listed in the README.

## Writing style

Plain, specific, lowercase-first prose in docs and comments. No em-dashes - use a hyphen with spaces. Say what the code does and why it is there; skip decoration. Comments cap at three lines; anything longer belongs in the README or a scrum record.
