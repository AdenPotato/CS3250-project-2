---
name: qa-steps
description: Write a numbered QA script for a branch - every step with an exact action, an exact expected result, and a blank for the result, keyed to the story's acceptance criteria. Use when handing a PR to the reviewer, or when a QA round found problems and the next round has to be precise about what to re-check.
argument-hint: "[branch or user story]"
---

# /qa-steps

Turn "ready to review" into a script a teammate can run without designing the test themselves.

**Why this exists.** Every PR into `dev` needs approval from someone other than its author, and the reviewer's job is to pull the branch and **run** it. "Have a click around" produces "looks fine", which cannot be logged. A numbered script produces "4b failed, remaining portions went to -1" - which is a defect report, a reproduction, and a `manual-tests.md` row at once.

## When to run it

- A PR is open and about to be reviewed.
- A QA round found problems and the next round has to state exactly what to re-check.

Skip it for a change with no observable surface: a scrum record, a diagram, a README edit.

## Step 1 - Preconditions

**Before writing a single step, say what the tester will be looking at and confirm it is this branch's code.**

```bash
git fetch && git switch <branch> && git pull
docker compose down -v               # fresh seeded database - ask the tester first, it wipes local data
docker compose up --build            # http://localhost:5000
```

Then name, concretely:

- **The accounts** - the seed vendor and student from the README, plus a **second** of whichever role the isolation steps need. Give the emails and passwords to create.
- **The data** - which seeded listing to use, or what to create first.
- **The clock** - a step about an ended window needs a listing whose window has ended. Say how to get one (a seed listing, or create one with a short window and wait).

## Step 2 - Derive the steps from the criteria and the diff

In this order:

1. **Each acceptance criterion of the story**, in its numbered order - so step numbers line up with criteria where possible.
2. **The failures the criteria name** - duplicate email, too many portions, a used pickup code.
3. **The security surface** - signed out, wrong role, another user's id in the URL.
4. **What must not have changed** - the previous stories this one builds on (a reservation change can break US3's portions-remaining display).

## Step 3 - Write the steps

**Numbering is the contract.** Top-level steps are numbers; sub-steps are letters, so "4c failed" means the same thing to both people.

Every step has three parts:

- **Do** - one concrete action.
- **Expect** - the exact observable result. Not "the portions update" but "the listing shows `Portions left: 3`".
- **Result** - blank, for the tester.

Rules: one assertion per sub-step; exact values and exact message text; say what the near-miss failure looks like ("if it shows -1, the decrement is not guarded"); never write a step whose result you already know.

## Step 4 - Render it

This goes in the PR description or a comment, not a file. The permanent record is `tests/manual-tests.md`.

```markdown
## QA script - <branch> (US#)

**Preconditions**
- Branch: `<branch>`, pulled
- `docker compose down -v && docker compose up --build` -> http://localhost:5000
- Accounts: seed vendor `<email>` / `<pw>`, seed student `<email>` / `<pw>`, plus register `student2@example.com` / `password2`
- Roughly: <minutes>

### 1. US#.1 - <criterion short name>
**Do:** <action>
**Expect:** <exact observable>
**Result:**

### 2. US#.2 - <criterion>
**Do:** <action>
- **2a. Expect:** <one observable>
  **Result:**
- **2b. Expect:** <another observable>
  **Result:**

### 5. Regression - <what must not have changed>
...

**Report back as:** the step number, what you saw, and a screenshot for anything visual.
```

## Step 5 - Close the loop

1. **Every step that ran becomes a `manual-tests.md` row** via [`/test-log`](../test-log/SKILL.md), keyed by story and criterion.
2. **A failed row stays.** The fix gets a new row for the retest.
3. **Re-issue only the affected steps**, plus any regression step the fix could touch.
4. **The reviewer approves the PR only when every step passed.**
