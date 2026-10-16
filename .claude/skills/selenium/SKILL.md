---
name: selenium
description: Write or run the automated Selenium black box test - one user story, every acceptance criterion, at least one failure case, driven through the browser against the running Docker Compose deployment. Use when building the Selenium story or changing a page it touches.
argument-hint: "[user story, e.g. US1]"
---

# /selenium

The assignment asks for **one** automated black box test with Selenium, for **one** story of the team's choice, worth **+3**. It must cover **every** acceptance criterion of that story, including at least one failure case, and drive the app through a browser against the running Compose deployment. It **must not call the app's Python functions** - no importing from `app`, no test client.

## Step 1 - Pick the story

If the team has not picked, recommend and ask:

- **US1** (register and log in) - five criteria, all visible in a browser, no setup beyond a unique email. The safest choice.
- **US4** (reserve) - more impressive, but needs a seeded listing and its criterion 4 (simultaneous reservations) is hard to drive through a browser; it needs two drivers racing, and can be flaky.

Record the choice in the README Testing section.

## Step 2 - Map criteria to test functions

One test function per criterion, named for it, so a failing test names the failing criterion:

```
test_us1_1_register_redirects_to_login
test_us1_2_duplicate_email_rejected
test_us1_3_empty_field_identified
test_us1_4_password_not_stored_plain     (see below)
test_us1_5_login_lands_on_role_home_and_wrong_password_rejected
```

A criterion that is not observable in a browser (US1.4, hashed passwords) still needs coverage without calling Python: query PostgreSQL directly from the test (`psycopg` against the Compose `db` port) and assert the stored value is not the plain password. That checks storage, not app code, so it stays black box. Say this in the README.

## Step 3 - Write it

`tests/test_selenium_us<n>.py`, pytest style:

- **Base URL from the environment**, default `http://localhost:5000`.
- **Headless Chrome or Firefox**, via a pytest fixture that quits the driver after each test. Selenium 4's built-in manager finds the driver; no hardcoded driver path.
- **Unique data per run** - `f"test-{uuid4().hex[:8]}@example.com"` - so the test passes on a non-empty database and on a second run.
- **Find by `id`**, not by XPath into the layout. If the page lacks ids, add them (the ui agent brief) - a test that breaks on a CSS change is worse than none.
- **Explicit waits** (`WebDriverWait(...).until(EC...)`) after every submit, never `time.sleep`.
- **Assert the exact text the criterion names** ("already registered"), and the URL after a redirect.

Add `selenium` and `pytest` (and `psycopg` if used) to a dev requirements file, not the runtime image.

## Step 4 - Run it

```
docker compose up --build -d
pip install -r requirements-dev.txt
pytest tests/test_selenium_us<n>.py -v
```

All tests pass against a fresh volume **and** a second run on the same volume.

## Step 5 - Document

The README must explain how to run it - the three commands above, the browser it needs, and the environment variable for a different base URL. Screenshot the passing run for the sprint review.

## Keep it green

Any PR that changes a page this test touches runs it before review. A changed `id` or message text is a broken test, and the reviewer should hear it from the PR, not from the grader.
