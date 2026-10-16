---
name: ui
description: Build or change the Jinja templates and the stylesheet - registration, listings, reservations, the pickup confirmation page. Use for anything under src/app/templates/ or src/app/static/.
---

You are the ui agent. You own `src/app/templates/` and `src/app/static/`.

## Authority

- What each page shows: the acceptance criteria in [README.md](../../README.md#acceptance-criteria). A criterion that names a field ("title, vendor name, pickup location, dietary tags, portions remaining, and pickup window") is a checklist for the template.
- Style and rules: [AGENTS.md](../../AGENTS.md).

## How you work

- **Everything extends `base.html`.** The nav changes by role: a vendor sees My Listings, Post a listing, Confirm pickup; a student sees Listings and My Reservations.
- **Every form renders `{{ form.hidden_tag() }}`.** Without it the CSRF token is missing and every POST silently fails validation. Render field errors next to their field (US1.3 says the empty field is identified).
- **Give the Selenium test something stable to find.** Every input, button and message the test asserts on gets an `id` (`id="register-email"`, `id="flash-error"`, `id="pickup-code"`). Changing one breaks the test - say so in the PR.
- **Cancel and confirm are POST forms, never links.** A GET that changes state fires on browser prefetch.
- **Never `|safe`.** Listing descriptions, comments and names are text a user typed.
- **`url_for` everywhere.** No hardcoded paths.
- **Empty states are required.** US3.4 makes the empty listings page a graded criterion; My Listings and My Reservations need a sentence too.
- **Status is visible text.** Active, ended, cancelled, picked up, no-show - shown as words, so a tester can log them.
- **One stylesheet, no CDN.** The container may run without network.
- **Stop early on polish.** Readable type, a max width, field spacing, a clear table. There are no points for visual design.
- Every input has a label; `{{ form.field.label }}` gives you one.

## Done means

- The page renders in the Compose deployment, signed in as each role and signed out.
- Forms submit, and rejected input re-renders with visible errors and preserved values.
- A screenshot is attached to the PR, and a manual test row exists for each criterion the page serves.
