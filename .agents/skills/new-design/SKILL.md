---
name: new-design
description: Settle a design decision before any code is written - run the one-at-a-time questionnaire, record the answer where it belongs (the class or sequence diagram, or the story's issue), and propose the build tasks. Use when an acceptance criterion is ambiguous or a change touches the model, a route and a template at once.
---

# /new-design

Design in this project is **not** open-ended. The acceptance criteria fix what each story does, so a design session settles the decisions they leave open - and nothing else. Nothing is written until the questionnaire is finished.

## Rules

- Questions are asked **one at a time**, never as a list.
- After each question, say how many remain ("3 questions remaining").
- Wait for an answer before asking the next one.
- If an answer contradicts an acceptance criterion or the class diagram, say so immediately and stop rather than carrying the contradiction forward.
- Only after every question is answered and the summary is confirmed is anything written.

## Step 1 - Find the story

Ask: **what decision is this session settling, and which story and criterion does it serve?**

Every decision traces to a user story (US1-US10) and usually to a numbered criterion in [README.md](../../../README.md#acceptance-criteria). Work that maps to none is out of scope until a teammate says otherwise (AGENTS.md rule 1). Say that plainly and stop.

Check the story's dependencies and its sprint in the release plan. Designing a Sprint 3 story in Sprint 1 is fine; building it is not.

Then read what the decision touches, so settled decisions are not reopened: the story's criteria, `uml/class.wsd`, any `uml/sequence-*.wsd`, and the current `src/app/models.py` and `routes.py` if they exist.

## Step 2 - Build the questionnaire

List the decisions and edge cases the criteria do not answer. Cover:

- **Scope** - which criteria, and what is explicitly not included (often a neighbouring optional story).
- **Data model** - new or changed tables, columns, constraints (unique pickup code, portions 1-100, one active reservation per student per listing), and whether teammates must `docker compose down -v`.
- **Roles and ownership** - who may reach the route, and how a vendor is kept out of another vendor's rows.
- **State** - the statuses involved (listing: active, ended, cancelled; reservation: active, picked up, cancelled, no-show), what moves between them, and whether a status is stored or computed from the clock. "No-show" after the window ends (US7.3) is the usual case to decide.
- **Concurrency** - anything that decrements a shared count (US4.4), and how the database guarantees it.
- **Form and validation** - what is validated server-side, and the exact message the user sees.
- **Template** - which page, which fields it shows, and the empty state.
- **Edge cases** - the boundary values in the criteria (1 and 100 portions, a window ending now, the last portion), a signed-out visitor, the wrong role, another user's id in the URL.
- **Testing** - which criteria the Selenium test covers if this is the Selenium story, and which need manual rows.

## Step 3 - Run the questionnaire

One question, then wait.

> **Question 1:** [question]
> *(N questions remaining)*

When the assignment is genuinely silent, that is a question for the team or the Product Owner, not a decision to invent (AGENTS.md rule 7). Flag it and carry it into the summary as an open item.

## Step 4 - Confirm

Present every decision as a short list, plus open items. Ask for confirmation before writing anything.

## Step 5 - Record it where it will be read

This project has no design docs folder. Decisions go where the team already looks:

- **Data model decisions** -> `uml/class.wsd` (via [`/uml`](../uml/SKILL.md)). The tables are graded for being traceable to it.
- **Flow decisions** (order of checks, the alternative paths) -> the story's sequence diagram, if it has one.
- **Everything else** -> the story's GitHub issue, as a `Design decisions` comment, so the person building it reads it.

Defined once. If a decision changes something already recorded, fix that record in the same change.

## Step 6 - The visible-surface gate

If the decision changes what a page shows, name the fields and the empty state in prose, check them against the criteria's wording, and get a teammate's confirmation before anyone opens a template. There are no points for visual design.

## Step 7 - Propose the build tasks

A design session is finished when the work it implies is tracked, or explicitly declined.

1. **List the tasks in dependency order** - usually model, then route and form, then template, then tests.
2. **Name the story** each task belongs to (its `US#` label) and the sprint.
3. **Propose them** - title, one-line scope, story - and wait for a go before running `/new-issue`.
4. **A design that produces no build work says so.** Silence is not an outcome.
