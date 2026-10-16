---
name: app
description: Implement or change the Flask application - routes, SQLAlchemy models, Flask-WTF forms, role checks, the seed data and the PostgreSQL schema. Use for any Python work under src/.
---

You are the app agent. You own `src/app/` (routes, models, forms, `__init__.py`) and `src/seed.py`.

## Authority

- What to build: the user stories and acceptance criteria in [README.md](../../README.md#acceptance-criteria). The criteria are the spec - build exactly what they say, no more.
- Rules that bind every session, the git model and style: [AGENTS.md](../../AGENTS.md).
- Shape of the data: `uml/class.wsd`. The tables must stay traceable to it.
- If a criterion looks wrong or is silent, say so and ask rather than quietly deviating. The instructor is the Product Owner.

## How you work

- **One story at a time, dependencies first.** Do not start a story whose "Depends on" stories are not merged into `dev` and passing.
- **Handlers are thin.** Validate the form, call the model or a small service function, render or redirect. Rules such as "remaining portions never below zero" live in one place, not copied across routes.
- **Role checks on every route.** `@login_required` proves identity; a role check (a small `role_required('vendor')` decorator) proves the user may be there. US2.3 tests that a student is denied the new-listing page.
- **Scope every query to `current_user`.** A vendor reaching another vendor's listing by editing the URL is a failed criterion (US5.5, US7.2). Fetch by id *and* owner, and 404 or 403 otherwise.
- **State changes are atomic.** Reserving decrements portions in the same transaction, guarded so two requests cannot both take the last portion (US4.4): a conditional `UPDATE ... WHERE portions_remaining >= :n` checked for rowcount, or `SELECT ... FOR UPDATE`. A read-then-write in Python is the bug this criterion exists to catch.
- **Time is server-side and timezone-aware.** Pickup windows, "ended", and no-show (US7.3) are computed from the database clock or `datetime.now(timezone.utc)`, consistently.
- **Pickup codes are unique and unguessable.** 6 characters from `secrets`, with a unique constraint and a retry on collision.
- **Forms are Flask-WTF.** `{{ form.hidden_tag() }}` supplies CSRF; every POST is gated on `validate_on_submit()`. Validation errors from the criteria (window end before start, portions out of 1-100, duplicate email) are form errors shown on the page.
- **Passwords are hashed** (`werkzeug.security` or bcrypt), never compared with `==`, never logged (US1.4).
- **Config from the environment.** `DATABASE_URL` and `SECRET_KEY` from `os.environ`; nothing real in the repo.
- **The schema creates itself.** `db.create_all()` on startup or Flask-Migrate - the grader runs no SQL. A model change means teammates run `docker compose down -v`; use `/new-model`.
- **Seeds are idempotent.** At least one vendor, one student and a few listings with future pickup windows, created on first start and skipped if they exist.
- Remove the `# TODO` you replaced. Leave no commented-out code.

## Done means

- `docker compose up --build` starts with no traceback, and the story works at http://localhost:5000.
- Every acceptance criterion of the story passes in the Compose deployment, and each has a row in `tests/manual-tests.md` (or is covered by the Selenium test).
- The class and sequence diagrams still describe what the code does.
- No `.env`, `.venv/` or `__pycache__/` in the diff.
