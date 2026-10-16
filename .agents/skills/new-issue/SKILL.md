---
name: new-issue
description: Open a GitHub issue for one task - labeled with its user story, assigned to its owner, in its sprint milestone, and added to the board. Use when a teammate has approved tracking the work, usually at sprint planning.
---

# /new-issue

The assignment asks for **one GitHub issue per task, labeled with its user story (for example US4), assigned to its owner, and linked from the pull request that completes it**. The board built from these issues is **+3** for planning and **+3** for board use.

**Teammate-gated.** Only run this once someone has asked for the issue or approved it. Never open one unilaterally, not even a follow-on. If you have spotted work that wants an issue, **propose it - title plus one-line scope - and wait for a go.** Claude Code has a mechanical backstop in `.claude/settings.json`; other tools may not, so the gate is on you - ask before any `gh issue create`.

## Before anything

```bash
gh repo view --json nameWithOwner -q .nameWithOwner
```

If that fails, the team repo is not set up yet - say so and stop.

## Step 1 - Draft it

**Title** is `US#: <task, lowercase>` - `US4: reserve form and atomic portion decrement`. Work that belongs to no story uses a prefix instead: `Deploy:` (Docker, Compose), `Design:` (UML), `Test:` (Selenium, manual tests), `Scrum:` (records, burndown), `Fix:`.

**Body** carries four things and nothing else:

```markdown
**Story** - US# and the acceptance criteria this task satisfies, by number.

**Scope** - what is in, and the obvious neighbouring thing that is out.

**Deliverable** - the concrete artifact that closes this. A page that passes US4.1-4.3 in Compose, a diagram that renders, a test that runs.

**How it is verified** - manual-tests.md rows, the Selenium test, or both.
```

For a task touching `models.py`, add a **database reset** line.

Present the draft, then ask for: the **owner**, the **sprint** (milestone), and the **estimate** if the team tracks tasks in points or hours. Do not proceed until confirmed.

## Step 2 - Make sure the labels and milestone exist

Idempotent; ignore "already exists":

```bash
gh label create US4 --color 1D76DB --description "As a student, I want to reserve portions" 2>/dev/null || true
gh api "repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/milestones" --jq '.[].title'
```

Milestones are `Sprint 1`, `Sprint 2`, `Sprint 3`. If the needed one is missing, propose creating it.

## Step 3 - Create it

```bash
gh issue create \
  --title "<title>" \
  --body "<body>" \
  --label "US#" \
  --assignee <github-login> \
  --milestone "Sprint N" \
  --project "<board name>"
```

Keep the issue URL. The card starts in **To Do**.

## Step 4 - Confirm

```bash
gh issue view <number> --json number,title,labels,assignees,milestone \
  --jq '"#\(.number) \(.title)\nlabels: \([.labels[].name] | join(", "))\nassignee: \([.assignees[].login] | join(", "))\nsprint: \(.milestone.title // "none")"'
```

Show the URL. If the work starts now, the branch is `US#-short-slug` off `dev`, and the PR body says `Closes #<number>` so the issue is linked and closes on merge.

## Team

Fill this in at Sprint 0 - the team need not be the same as Project 1. The assignee is the GitHub login.

| Person | GitHub | Role |
|---|---|---|
| `<name>` | `<login>` | Scrum Master |
| `<name>` | `<login>` | Developer |

Board: `<board name and URL>`, columns **To Do, In Progress, In Review, Done** (the minimum the assignment requires).

## Constraints

- **One task per issue, one story per task.** A story is usually three or four tasks - model, route and form, template, tests - so two people can work on it at once.
- **Every member owns issues every sprint.** `dev` must show merges from everyone.
- **Do not open an issue for work already done.**
- **Cards move as work moves**, not at the end of the sprint. The board screenshot is graded on looking used.
