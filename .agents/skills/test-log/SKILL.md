---
name: test-log
description: Record manual test results in tests/manual-tests.md - one row per acceptance criterion tested, real dates, failures kept - and check coverage of every implemented story. Use after clicking through a story, and for the re-test before each release.
---

# /test-log

Add rows to `tests/manual-tests.md`. With the Selenium test, this is the Testing rubric (**+2** manual evidence), and it is how a story is shown to pass its criteria. Written as testing happens, not reconstructed the night before.

## The file

If it does not exist, create it with the table the assignment prescribes, exactly:

```markdown
# Manual tests

| User story | Acceptance criterion | Tester | Date | Result | Notes |
| --- | --- | --- | --- | --- | --- |
```

## Add rows

One row per criterion tested:

- **User story** - `US4`.
- **Acceptance criterion** - the number and a short name, as in the assignment's example: `2: more portions than remain rejected`.
- **Tester** - the person who clicked. If an agent drove it without a browser, say so (`Claude Code (HTTP requests, no browser)`); a grader should know.
- **Date** - `MM/DD/YY`, the real date (`date +%m/%d/%y`). Never invented.
- **Result** - `passed` or `failed`. Nothing else.
- **Notes** - what a reader needs to reproduce it: the account, the input, the message seen. "Tested against `docker compose up --build`" where it matters.

Every criterion of the story gets a row. A story with five criteria and three rows is not shown as done.

## Failures stay

A `failed` row is never edited or deleted. When it is fixed, add a **new** row for the retest and reference the failure in Notes ("retest of the 10/22/26 failure, fixed in #18"). A log with no failures reads as a log nobody used.

## Re-test before each release

The assignment requires re-testing stories from earlier sprints before each release. Before `v2`, re-test the Sprint 1 stories; before `v3`, every story. New rows with the new date - the earlier passes stay.

## Check coverage

After adding rows, report for every story implemented so far: criteria with a `passed` row / total criteria, and whether its latest result for each criterion is `passed`. The Selenium story is covered by its test, not by rows - say which story that is.

## Test well

- Test against the **Compose deployment** with a fresh volume (`docker compose down -v && docker compose up --build`) so results are reproducible. The criteria say "passes in the Docker Compose deployment".
- Use two accounts per role where isolation matters: a second vendor for US5.5 and US7.2, a second student for US4.4.
- Say what you expect before you click.
- The high-value cases are the boundaries the criteria name: 1 and 100 portions, 8-character passwords, a window ending in the past, the last portion, a used pickup code.
