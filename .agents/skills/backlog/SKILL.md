---
name: backlog
description: Sprint 0 - estimate every user story in story points, compute priority scores, rank the backlog, set team capacity, and split the stories across three sprints respecting dependencies. Fills the README tables. Use before Sprint 1 starts, or when the release plan has to change.
---

# /backlog

Fill the **Scoring and Prioritizing** and **Sprint Planning** tables in [README.md](../../../README.md). Worth **+3** on its own, and every later sprint is planned from it.

The team estimates; this skill runs the method and checks the rules. **Never invent an estimate.** Story points come from the team (planning poker, or whatever Activity 17 used).

## Step 1 - The Scrum Master

If the README still says `Scrum Master: <student's name>`, ask who it is and fill it first. Leaving it is **-3**.

## Step 2 - Story points

Ask for each story's points, one story at a time, US1 to US10. Use the scale the team used in Activity 17 (usually Fibonacci: 1, 2, 3, 5, 8, 13). If the team wants help, give a short note per story on what drives its size - for example US4 carries the concurrency criterion, US5 has five criteria and touches two roles - but the number is theirs.

## Step 3 - Priority score and rank

```
Priority score = User value / Story points
```

Two decimals. Rank highest score first; break ties by higher user value, then by fewer dependencies. Fill the table, including the Total row (sum of user value and of story points).

## Step 4 - Capacity

Ask for the team's capacity in story points per sprint and a one or two sentence justification (team size, hours available, course load). Fill the code block.

Sanity check: the required stories (US1-US7) must fit in 3 x capacity. If they do not, say so now - either the estimates or the capacity is wrong, and the rule says all seven must be planned.

## Step 5 - Split across sprints

Place stories in this order of rules, and show the reasoning:

1. **Required first.** US1-US7 all go in Sprints 1-3.
2. **Dependencies.** A story goes in the same sprint as a story it depends on only if the plan lists the dependency earlier in that sprint; otherwise a later sprint. From the backlog: US1 has none; US2 needs US1; US3 needs US2; US4 needs US1, US3; US5 needs US2, US4; US6 needs US4; US7 needs US4; US8 needs US3; US9 and US10 need US7.
3. **Capacity.** No sprint exceeds it.
4. **Priority.** Within those limits, higher-ranked stories go earlier.
5. **Optional stories** only in space left over.

Fill the sprint table: stories in order, points planned, points remaining after the sprint, and `Y` in Dependencies checked only after checking every story against rule 2.

## Step 6 - Planned burndown

List the story points remaining at the start (sum of all planned stories) and after each sprint. These numbers are the **planned** line in `burndown.xlsx`; put them there too.

## Step 7 - Confirm, then write

Show both tables exactly as they will appear and write nothing until a teammate confirms. Then fill the README tables in place, keeping their format.

Propose (do not create) one GitHub milestone per sprint (`Sprint 1`, `Sprint 2`, `Sprint 3`) and one issue per Sprint 1 task, for `/new-issue`.
