# Manual tests

Each row is one acceptance criterion clicked through by hand against `docker compose up --build`; the tester fills in Tester, Date (MM/DD/YY) and Result (`passed` or `failed`).

`tests/test_us1.py` automates the same US1 checks over HTTP - run it with `pytest tests` (see the README).

| User story | Acceptance criterion | Tester | Date | Result | Notes |
| --- | --- | --- | --- | --- | --- |
| US1 | 1: registration stores account and redirects to login | Aden Lytle | 10/25/26 | passed | register as Student, then as Vendor, with a new email and an 8-character password - expect the login page and a success message |
| US1 | 2: duplicate email rejected | Aden Lytle | 10/25/26 | passed | register again with the same email (also try it in capitals) - expect "That email is already registered." |
| US1 | 3: empty field identified | Aden Lytle | 10/25/26 | passed | leave name, email, password, then role empty one at a time - expect the error under that field and no account |
| US1 | 4: password stored hashed | Aden Lytle | 10/25/26 | passed | `docker compose exec db psql -U campuseats -d campuseats -c "SELECT email, password_hash FROM users"` - expect a scrypt hash, not the password |
| US1 | 5: login lands on role home, wrong password rejected | Aden Lytle | 10/25/26 | passed | log in as the student and the vendor - expect each home page; a wrong password shows "Incorrect email or password." and stays logged out |

| US2 | 2.1: Post surplus food listing saves to the database | Isabella Eaton | 10/27/26 | passed | verified via DB inspection and successful redirect with success flash message |
| US2 | 2.2: Form validation enforces portions (1-100), future pickup windows, and multi-select dietary tags | Isabella Eaton | 10/27/26 | passed | WTForms SelectMultipleField checkboxes and SQLAlchemy/PostgreSQL CheckConstraints tested successfully |
| US2 | 2.3: Vendor-only access enforced on /listings/new route | Isabella Eaton | 10/27/26 | passed | students attempting to access /listings/new receive a 403 Forbidden abort response |

| US3 | 1: Browse available listings as student |  |  |  | logged in as student, open /listings - see listings with pickup window not ended, portions remaining > 0, not cancelled; sorted by pickup window end soonest first |
| US3 | 2: Each listing shows required fields |  |  |  | title, vendor name, pickup location, dietary tags, portions remaining, pickup window displayed |
| US3 | 3: Listings sorted by pickup window end |  |  |  | multiple listings appear in order of soonest pickup_end first |
| US3 | 4: No listings message shown |  |  |  | when no available listings exist, message shown instead of empty page |

| US4 | 1: Reserve 1 or 2 portions, get unique 6-char pickup code, portions decrease |  |  |  | logged in as student, reserve 1 or 2 portions from a listing with remaining portions - reservation stored, portions_remaining decreases, see unique 6-char pickup code |
| US4 | 2: Request more than remain - no reservation, error shown |  |  |  | try to reserve more portions than remain - no reservation created, error message shown |
| US4 | 3: Cannot reserve again if already have active reservation for listing |  |  |  | try to reserve again for same listing with active reservation - told already have reservation |
| US4 | 4: Concurrent reservations - only one succeeds, portions never go below zero |  |  |  | two students reserve last portion simultaneously - only one reservation succeeds, remaining portions never go below zero |
| US6 | 1: View my reservations with details and status |  |  |  | logged in as student, open "My Reservations" - see each reservation with listing title, vendor, location, pickup window, portions, pickup code, status |
| US6 | 2: Cancel active reservation before window ends, portions returned |  |  |  | cancel active reservation with pickup window not ended - status becomes cancelled, portions returned to listing |
| US6 | 3: No cancel option for non-active reservations |  |  |  | for non-active reservations (picked up/cancelled/no-show), no "Cancel" option shown |

| US7 | 1: Confirm pickup with valid code during window marks as picked up |  |  |  | vendor enters pickup code for active reservation on their listing during pickup window - status becomes picked up, see student name and portions |
| US7 | 2: Invalid code, wrong vendor, already used/cancelled rejected |  |  |  | code doesn't exist, belongs to another vendor, or already used/cancelled - pickup rejected with clear message |
| US7 | 3: Expired window marks active reservations as no-show |  |  |  | pickup window ended - every reservation on that listing still active shown with status no-show |
