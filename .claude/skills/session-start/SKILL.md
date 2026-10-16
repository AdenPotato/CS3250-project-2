---
name: session-start
description: Open a working session - sync dev, read the assignment and the current sprint's records, report where the sprint stands, propose the next task, and cut the branch once a teammate approves. Use at the start of a session, before any code.
argument-hint: "[user story or issue number]"
---

# /session-start

The start-of-session checklist, in this order. Nothing is written and no branch is cut until Step 5.

## Step 0 - Sync `dev` (guarded)

Start from the integrated state, so the branch is not cut off yesterday's `dev`.

**Skip this step** if resuming a topic branch or the working tree is dirty (`git status --short` non-empty). Never pull into a topic branch mid-task - say so and continue on the current branch.

If the tree is clean:

```bash
git switch dev
git pull --ff-only
git fetch --prune
```

Then delete local branches whose PRs have merged. **Do not use `git branch --merged`** - it only lists ancestors of the current branch, so anything squashed on merge is silently kept:

```bash
for b in $(git branch --format='%(refname:short)' | grep -vE '^(main|dev)$'); do
  state=$(gh pr list --head "$b" --state all --json state --jq '.[0].state' 2>/dev/null)
  if [ "$state" = "MERGED" ]; then git branch -D "$b"; fi
done
```

If there is no repo or no `dev` branch yet, stop and say so. Creating `dev` from `main` is the first task of the project.

## Step 1 - Read the context (in parallel)

Read all of these before forming any opinion:

- [README.md](../../../README.md) - the backlog, the acceptance criteria, the release plan, the rubric.
- The current sprint's `scrum/sprint_#/planning.md` - the goal, the stories, who owns which task. The current sprint is the highest-numbered one with a filled planning record and no filled review.
- That sprint's `daily_scrums.md` - the latest blockers.
- The previous sprint's `retrospective.md` - the actions this sprint promised to carry out.
- `tests/manual-tests.md`, if it exists - which criteria have evidence.

If the last daily scrum or PR says a model changed, act on it first: `docker compose down -v && docker compose up --build`.

## Step 2 - Report where things stand

Gather and render exactly as [`/project-status`](../project-status/SKILL.md) specifies. Do not invent a second format; that report is defined once.

Two additions for a session start:

- **After pulling**, say what has to be run before the app will start.
- **Open issues for this sprint**, so the plan and the board agree:

  ```bash
  gh issue list --state open --limit 50 \
    --json number,title,labels,assignees,milestone \
    --jq '.[] | "#\(.number)\t\([.labels[].name] | map(select(test("^US[0-9]+$"))) | join(","))\t\([.assignees[].login] | join(",") // "unassigned")\t\(.milestone.title // "no sprint")\t\(.title)"'
  ```

  Flag anything with no `US#` label, anything unassigned in the current sprint, and anything whose sprint has already closed.

## Step 3 - Propose one pick

End the report with a single proposal from the **current sprint's plan**. Within it: required before optional, a story whose dependencies are merged, and work that unblocks a teammate first.

```
Pick:        <issue #> - <title> (US#)
Why now:     <one line - dependency, sprint goal, or who it unblocks>
Branch:      US#-short-slug
Deliverable: <the concrete artifact> -> <the acceptance criteria it closes>
Verified by: <Selenium, manual-tests.md rows, or both>
Shape:       <two or three steps>
```

Then ask for a go, or for a different pick.

This is a recommendation and never an auto-start. If `$ARGUMENTS` names the work, plan around that instead of proposing your own.

## Step 4 - Wait

No branch, no edits, no `gh issue edit` before a teammate answers.

## Step 5 - Read what the pick touches, then cut the branch

Read the story's acceptance criteria in full, then the code and diagrams it touches, and say which files you read and why.

**Confirm the deliverable before any code.** Name which criteria it closes. If a criterion is unclear, stop and run [`/new-design`](../new-design/SKILL.md) or ask a teammate - never guess a requirement (AGENTS.md rule 7).

Only then:

```bash
gh issue edit <n> --add-assignee @me     # claim it before coding
git switch -c US#-short-slug             # off dev
```

Move the card to **In Progress** on the board.

## Notes

- **Sprint discipline.** If the pick belongs to a later sprint, say so. Pulling work forward is a Sprint Planning decision, not a session one.
- **Dependencies are binding.** A story whose prerequisites are not merged and passing is not startable, however small it looks.
- **Day one comes first.** No `dev` branch, no Scrum Master in the README, or no Sprint 0 plan is the pick, whatever else is on the board.
