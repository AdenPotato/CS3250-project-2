---
name: new-route
description: Implement a user story's page or flow end to end - the view function, its Flask-WTF form, its role check, its Jinja template, and the evidence for every acceptance criterion. Use when building a story or one task of a story.
argument-hint: "[user story, e.g. US4]"
---

# /new-route

Build one story (or one task of it) through every layer it touches. Take the story from `$ARGUMENTS`; if none is given, take the current issue's `US#` label.

## Before writing

1. Read the story's acceptance criteria in [README.md](../../../README.md#acceptance-criteria). **Number them.** Every one must be satisfied by what you build, and the PR will list them.
2. Check its dependencies are merged into `dev` and passing. If not, stop (AGENTS.md rule 3).
3. Read `uml/class.wsd` and the current `models.py`. If the story needs a model change, do `/new-model` first.
4. If a criterion is ambiguous, stop and run `/new-design`.

## Build, in this order

1. **The form**, if the route takes input. A `FlaskForm` in `src/app/forms.py` with validators that mirror the criteria: `Length(min=8)` on the password (US1.1), `NumberRange(1, 100)` on portions (US2.1), a `validate_<field>` method for "end after start, end in the future" (US2.2). Dietary tags are a multi-select or checkboxes over the five fixed tags.

2. **The view function** in `src/app/routes.py`.
   - `@login_required` and a role check on everything except register and login.
   - Fetch rows by id **and** owner (`Listing.query.filter_by(id=id, vendor_id=current_user.id)`), 404 otherwise.
   - `form.validate_on_submit()` gates the POST branch.
   - Shared counts change atomically (see the app agent brief on US4.4).
   - Redirect after a successful POST; re-render with errors after a failed one. Errors the criteria name ("email already registered", "already have a reservation", "not enough portions") are shown as text on the page.
   - `url_for`, never a hardcoded path. Pass `title` to every `render_template`.

3. **The template** in `src/app/templates/`, extending `base.html`. Every field the criterion lists, `{{ form.hidden_tag() }}` in every form, errors beside their fields, an empty state if the page can be empty, stable `id`s on anything a test will look for.

4. **Seed data**, if the story needs something to look at on a fresh start (a listing with a future window, a reservation to confirm).

## Verify

Rebuild and run: `docker compose up --build`, http://localhost:5000. Then, criterion by criterion:

- The happy path for each criterion.
- Every failure the criteria name - and the boundary (exactly 100 portions passes, 101 fails).
- Signed out - redirect to login.
- Wrong role - denied.
- Another user's row by editing the URL - denied.

## Finish

- Add a row per criterion to `tests/manual-tests.md` (`/test-log`), or extend the Selenium test if this is the Selenium story (`/selenium`).
- If the flow differs from the sequence diagram, fix the diagram in the same change.
- Commit per [AGENTS.md](../../../AGENTS.md#git-model), PR into `dev` with `Closes #<issue>`, the criteria list, a screenshot, and a QA script for the reviewer (`/qa-steps`). Move the card to **In Review**.
