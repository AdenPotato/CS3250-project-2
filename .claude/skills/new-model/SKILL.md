---
name: new-model
description: Change a SQLAlchemy model - edit models.py, reset or migrate the PostgreSQL schema, update the seed data, and update the class diagram together. Use for any change to User, Listing, Reservation, DietaryTag or their relationships.
---

# /new-model

A model change is not just an edit to `models.py`. The database lives in a Docker volume, the seed data writes to it, and the class diagram is graded for matching it. All three move together.

## Before changing anything

Ask whether it should change at all, and which acceptance criterion needs it. A change that is convenient for one route is usually the route's problem. State the reason.

Know how the schema is created in this repo - check `src/app/__init__.py`:

- **`db.create_all()`** creates missing tables and **silently ignores a changed column**. Every teammate must wipe the volume after pulling.
- **Flask-Migrate** generates a migration the container applies on start (`flask db upgrade`). No wipe needed, but the migration file must be committed.

## Steps

1. **Edit `src/app/models.py`.** Constraints the criteria depend on belong in the database, not only in the form:
   - `User.email` unique (US1.2).
   - `Listing.portions` checked 1-100, remaining portions `>= 0` (US2.1, US4.4) - a `CheckConstraint` makes "never below zero" true even if a route is wrong.
   - `Reservation.pickup_code` unique (US4.1).
   - At most one *active* reservation per student per listing (US4.3) - a partial unique index on PostgreSQL, or enforced in the route with a clear message.
   - Many-to-many `Listing` <-> `DietaryTag` through an association table.
   - Datetimes timezone-aware (`DateTime(timezone=True)`).

2. **Apply it.**
   - `create_all`: `docker compose down -v && docker compose up --build` (ask first - it deletes the local data).
   - Flask-Migrate: `flask db migrate -m "<what changed>"` inside the `web` container, read the generated file, then restart.

   Confirm the container starts with no traceback and the seed accounts still log in.

3. **Check what the change broke.**
   ```
   grep -rn "<field>" src/
   ```
   Routes, forms, templates and `seed.py` all touch model fields directly.

4. **Update `src/seed.py`** if the field is required, so a fresh start still seeds cleanly.

5. **Update `uml/class.wsd`** to match (`/uml class`). A class diagram that disagrees with `models.py` loses design points.

6. **Run it.** Log in as each seed account and walk the stories already done. A model change breaks things far from where it was made.

7. **Re-test** the affected stories and add rows (`/test-log`).

## The PR

Say in the first line: **"Model change - run `docker compose down -v && docker compose up --build` after pulling."** (or "migration included" with Flask-Migrate). Mention it at the next daily scrum too.
