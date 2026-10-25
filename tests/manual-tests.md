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
