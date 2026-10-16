---
name: release
description: Cut a sprint release - run the Docker Compose deployment from a clean clone, re-test every story so far, walk the release checklist, then merge dev into main and tag v1, v2 or v3. Use at the end of each sprint, and for any change to the Dockerfile or docker-compose.yml.
---

# /release

Get `main` into the state the instructor receives it in. Three tagged releases are **+3**, and Compose with PostgreSQL is **+5** - and every story's points depend on it passing in Compose.

The rule that makes this skill worth running: **run it from a fresh clone, not your working tree.** The uncommitted file is the most common release failure and it is invisible from where you are sitting.

## 1. The deployment files

If they do not exist yet, write them. Non-negotiables from the assignment:

- **`docker-compose.yml`** with at least `db` (official `postgres` image, **named volume**) and `web` (built from the `Dockerfile`, **waiting for `db` to be ready** - a `pg_isready` healthcheck plus `condition: service_healthy`), `web` on port `5000:5000`.
- **`Dockerfile`**: `requirements.txt` copied and installed before the source; `--host=0.0.0.0`; schema created and seeds loaded on start.
- **Config from the environment**: `DATABASE_URL`, `SECRET_KEY`. `.env.example` has placeholders; `.env` and `.venv` are in `.gitignore`.
- **`.dockerignore`** covering `.venv/`, `.git/`, `__pycache__/`, `.env`.

## 2. Run clean

```
git clone -b dev <repo-url> /tmp/release-check
cd /tmp/release-check
cp .env.example .env            # only if the README tells the grader to
docker compose up --build
```

A failure here is almost always a missing commit. Fix it by committing the file, not by copying it in. Then `docker compose down -v` when done.

## 3. Re-test every story so far, inside Compose

The assignment requires stories from earlier sprints to be re-tested before each release. At http://localhost:5000:

- Log in with each **seed account** from the README.
- Walk every acceptance criterion of every story implemented so far.
- Run the Selenium test against it.

Record each in `tests/manual-tests.md` with today's date (`/test-log`). A story that fails here is not in this release - say so at the review rather than tagging it as done.

## 4. The checklist

Report each item; do not mark one done without checking it.

- [ ] `docker compose up --build` from a clean clone serves http://localhost:5000
- [ ] Seed vendor and seed student log in; sample listings are visible
- [ ] Data survives `docker compose down` then `up`
- [ ] Every story planned for this sprint passes all its criteria in Compose, with evidence
- [ ] Earlier sprints' stories re-tested, rows added
- [ ] Selenium test passes; README says how to run it
- [ ] README lists the run command and the seed accounts, and names the Scrum Master
- [ ] `.env`, `.venv`, `__pycache__` absent from `git ls-files`; `.env.example` present
- [ ] `uml/` diagrams match the code
- [ ] This sprint's `scrum/sprint_N/` records are filled and `board.png` is in

## 5. Merge and tag

Only once `dev` passes the checklist. **A teammate runs these** - agents never merge or tag (AGENTS.md rule 8):

```
git switch main && git pull
git merge --no-ff dev -m "release vN: sprint N"
git tag -a vN -m "sprint N release"
git push origin main --tags
```

If `main` is protected, merge `dev` into `main` through a PR instead and tag the resulting merge commit. Either way the tag sits on the merge commit.

Then: `git tag --list` shows `vN`, and `git log main --oneline -1` is the merge.

## 6. Report

State what passed, what failed, and what is outstanding on the checklist. If a planned story is not releasable, say so plainly - it goes back to the backlog at the review and shows up on the burndown's actual line. Finding that out is the point of this skill.
