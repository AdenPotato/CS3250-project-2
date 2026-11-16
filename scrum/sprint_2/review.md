Date/Time: 11/15/2026 14:00 remote

Participants: IE, AL, HY, EDO, JDG (all members)

# Sprint 2 Review

## 1. Sprint Overview
* **Project Name:** CampusEats
* **Sprint Duration:** 11/02/2026 – 11/15/2026
* **Scrum Master:** Aden L.
* **Development Team:** Isabella E., Johnny G., Elijah D.O, Hilb Y, Aden L.

---

## 2. Sprint Goal
> Allow vendors to be able to manage active, ended and canceled listings, allow a student to view and cancel their reservation, allow a vendor to confirm pickup. Optional goals included allowing a student to filter listings, allowing the vendor to select data ranges for viewing their dashboard, and allowing a student to rate a picked up reservation.

---

## 3. Completed Deliverables (Product Increment)
The "At review" column is the status shown at the 11/15 14:00 review. The "At v2 release" column is the status when v2 was cut later on 11/15, after the remaining work was merged and tested.

| ID | Description | At review | At v2 release |
| --- | --- | --- | --- |
| US4 | Reserve portions | Done | Done |
| US5 | Manage listings | Done | Done |
| US6 | View and cancel my reservations | IP | Done |
| US7 | Confirm pickup | IP | Done |
| US8 | Filter listings (optional) | IP | Done |
| US9 | Impact dashboard (optional) | IP | Done (#117) |
| US10 | Rate a pickup (optional) | IP | Done (#118) |

Each story at "Done" passes every acceptance criterion in Docker Compose, with rows in `tests/manual-tests.md` and Selenium regression tests in `tests/`.

### Summary of Working Increment
* Students can reserve one or two portions of a listing and get a unique pickup code; portions never go below zero, even when two students reserve at once.
* Students can view their reservations, cancel an active one before the pickup window ends, and get the portions returned to the listing.
* Vendors can see their listings with status and counts, edit or cancel a listing, and see who reserved it.
* Vendors can confirm a pickup by code; reservations not picked up by the end of the window become no-shows.
* Optional: students can filter listings by dietary tags and campus location, vendors have an impact dashboard for a date range, and students can rate a pickup that vendors see as an average with comments.

---

## 4. Incomplete or Carried-Over Items
At the review, US6 and US7 and the optional US8-US10 were still in progress. All of them were finished and tested before the v2 release, so nothing is carried over.

---

## 5. Stakeholder Feedback & Demo Notes
* **What went well / Positive feedback:**
  ont ime to finish all required user stories by EOD, undecided whether optional user sotires will be acocmplished today.
* **Requested changes or concerns:**
  none
