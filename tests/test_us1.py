"""US1 register and log in - black box HTTP checks against the running Compose app.

Talks to the app only over HTTP (and to postgres through `docker compose exec` for the
database checks), so it never imports the app. Start the stack first, then: pytest tests
"""
import http.cookiejar
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import pytest

BASE_URL = os.environ.get("CAMPUSEATS_URL", "http://localhost:5000").rstrip("/")
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_USER = os.environ.get("POSTGRES_USER", "campuseats")
DB_NAME = os.environ.get("POSTGRES_DB", "campuseats")
PASSWORD = "correct-horse-1"


# ---------- helpers ----------

class NoRedirect(urllib.request.HTTPRedirectHandler):
    # hand back the 302 itself so a test can read its Location header
    def redirect_request(self, *args, **kwargs):
        return None


class Browser:
    """A cookie-keeping client - one per test, like one browser session."""

    def __init__(self):
        cookies = urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        self.opener = urllib.request.build_opener(cookies, NoRedirect)

    def request(self, path, data=None):
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        try:
            resp = self.opener.open(BASE_URL + path, data=body, timeout=10)
        except urllib.error.HTTPError as err:
            resp = err  # 3xx, 403 and friends arrive here - they are still responses
        return resp.status, resp.headers.get("Location", ""), resp.read().decode()

    def get(self, path):
        return self.request(path)

    def post_form(self, path, fields, form_page=None):
        # GET the page holding the form for its CSRF token, as a browser would
        _, _, html = self.get(form_page or path)
        token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        assert token, f"no csrf_token on {form_page or path}"
        return self.request(path, {"csrf_token": token.group(1), **fields})


def location_path(location):
    return urllib.parse.urlparse(location).path


def unique_email():
    return f"us1-{uuid.uuid4().hex[:10]}@campus.test"


def register(browser, name="Test User", email=None, password=PASSWORD, role="student"):
    # None means "make one up"; an empty string is sent as empty
    fields = {"name": name, "email": unique_email() if email is None else email, "password": password}
    if role is not None:
        fields["role"] = role
    return browser.post_form("/register", fields)


def login(browser, email, password=PASSWORD):
    return browser.post_form("/login", {"email": email, "password": password})


def has_id(html, element_id):
    return f'id="{element_id}"' in html


def db_query(sql):
    """Run SQL in the db container; skip the test if docker cannot reach it."""
    if not shutil.which("docker"):
        pytest.skip("docker not on PATH - database checks need `docker compose exec db`")
    cmd = ["docker", "compose", "exec", "-T", "db", "psql", "-U", DB_USER, "-d", DB_NAME, "-tAc", sql]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        pytest.skip(f"could not query the db container: {result.stderr.strip()}")
    return result.stdout.strip()


def count_users(email):
    # emails are uuid-based, so there is nothing to escape in them
    return int(db_query(f"SELECT count(*) FROM users WHERE lower(email) = lower('{email.strip()}')"))


@pytest.fixture(scope="session", autouse=True)
def app_is_up():
    try:
        urllib.request.urlopen(BASE_URL + "/", timeout=5)
    except OSError as err:
        pytest.fail(f"CampusEats is not answering at {BASE_URL} - run `docker compose up --build` ({err})")


# ---------- US1.1 registration stores the account and redirects to login ----------

@pytest.mark.parametrize("role", ["student", "vendor"])
def test_us1_1_register_redirects_to_login(role):
    browser = Browser()
    email = unique_email()
    status, location, _ = register(browser, email=email, role=role)
    assert status == 302
    assert location_path(location) == "/login"
    _, _, html = browser.get("/login")
    assert has_id(html, "flash-success")


def test_us1_1_register_stores_account_in_postgres():
    email = unique_email()
    register(Browser(), name="Ana Stored", email=email, role="vendor")
    row = db_query(f"SELECT name, email, role FROM users WHERE email = '{email}'")
    assert row == f"Ana Stored|{email}|vendor"


def test_us1_1_password_of_exactly_8_characters_accepted():
    status, location, _ = register(Browser(), password="12345678")
    assert status == 302 and location_path(location) == "/login"


def test_us1_1_password_under_8_characters_rejected():
    email = unique_email()
    status, _, html = register(Browser(), email=email, password="1234567")
    assert status == 200
    assert has_id(html, "register-password-error")
    assert "Password must be at least 8 characters." in html
    assert count_users(email) == 0


# ---------- US1.2 duplicate email rejected ----------

def test_us1_2_duplicate_email_rejected():
    email = unique_email()
    register(Browser(), email=email)
    status, _, html = register(Browser(), name="Someone Else", email=email)
    assert status == 200
    assert has_id(html, "register-email-error")
    assert "That email is already registered." in html
    assert count_users(email) == 1


def test_us1_2_duplicate_email_with_other_case_and_spaces_rejected():
    email = unique_email()
    register(Browser(), email=email)
    status, _, html = register(Browser(), email=f"  {email.upper()} ")
    assert status == 200
    assert "That email is already registered." in html
    assert count_users(email) == 1


# ---------- US1.3 an empty required field is identified ----------

@pytest.mark.parametrize(
    "field, message",
    [
        ("name", "Enter your name."),
        ("email", "Enter your email."),
        ("password", "Enter a password."),
        ("role", "Choose Student or Vendor."),
    ],
)
def test_us1_3_empty_field_identified(field, message):
    email = unique_email()
    name = f"Empty {uuid.uuid4().hex[:10]}"  # unique, so "no account" can be checked by name too
    values = {"name": name, "email": email, "password": PASSWORD, "role": "student"}
    if field == "role":
        values["role"] = None  # an unticked radio is simply not sent
    else:
        values[field] = ""
    status, _, html = register(Browser(), **values)
    assert status == 200
    assert has_id(html, f"register-{field}-error")
    assert message in html
    assert count_users(email) == 0
    assert db_query(f"SELECT count(*) FROM users WHERE name = '{name}'") == "0"


def test_us1_3_whitespace_only_name_counts_as_empty():
    email = unique_email()
    status, _, html = register(Browser(), name="   ", email=email)
    assert status == 200
    assert "Enter your name." in html
    assert count_users(email) == 0


# ---------- US1.4 passwords stored hashed ----------

def test_us1_4_password_stored_hashed():
    email = unique_email()
    register(Browser(), email=email)
    stored = db_query(f"SELECT password_hash FROM users WHERE email = '{email}'")
    assert stored, "user was not stored"
    assert PASSWORD not in stored
    # werkzeug hashes look like "scrypt:32768:8:1$salt$hash" or "pbkdf2:sha256:...$salt$hash"
    assert re.match(r"^(scrypt|pbkdf2):[^$]+\$[^$]+\$[0-9a-f]+$", stored)


def test_us1_4_same_password_gives_different_hashes():
    first, second = unique_email(), unique_email()
    register(Browser(), email=first)
    register(Browser(), email=second)
    hashes = db_query(f"SELECT password_hash FROM users WHERE email IN ('{first}', '{second}')")
    assert len(set(hashes.splitlines())) == 2  # salted, so equal passwords do not match


# ---------- US1.5 login lands on the role's home; wrong password stays logged out ----------

@pytest.mark.parametrize("role, home, marker", [("student", "/student", "student-home"), ("vendor", "/vendor", "vendor-home")])
def test_us1_5_login_lands_on_role_home(role, home, marker):
    browser = Browser()
    email = unique_email()
    register(browser, name=f"Home {role}", email=email, role=role)
    status, location, _ = login(browser, email)
    assert status == 302 and location_path(location) == home
    status, _, html = browser.get(home)
    assert status == 200
    assert has_id(html, marker)
    assert has_id(html, "nav-user") and has_id(html, "nav-logout")


def test_us1_5_login_email_ignores_case_and_spaces():
    browser = Browser()
    email = unique_email()
    register(browser, email=email)
    status, location, _ = login(browser, f" {email.upper()} ")
    assert status == 302 and location_path(location) == "/student"


def test_us1_5_wrong_password_shows_error_and_stays_logged_out():
    browser = Browser()
    email = unique_email()
    register(browser, email=email)
    status, _, html = login(browser, email, password="wrong-password")
    assert status == 200
    assert has_id(html, "flash-error")
    assert "Incorrect email or password." in html
    assert has_id(html, "nav-login") and not has_id(html, "nav-user")
    status, location, _ = browser.get("/student")
    assert status == 302 and location_path(location) == "/login"


def test_us1_5_unknown_email_shows_same_error():
    status, _, html = login(Browser(), unique_email())
    assert status == 200
    assert "Incorrect email or password." in html


def test_us1_5_logged_out_student_page_redirects_to_login():
    status, location, _ = Browser().get("/student")
    assert status == 302 and location_path(location) == "/login"


def test_us1_5_student_cannot_open_vendor_home():
    browser = Browser()
    email = unique_email()
    register(browser, email=email, role="student")
    login(browser, email)
    status, _, _ = browser.get("/vendor")
    assert status == 403


def test_us1_5_logout_ends_the_session():
    browser = Browser()
    email = unique_email()
    register(browser, email=email)
    login(browser, email)
    # logout is a POST form in the nav, so its CSRF token comes from the home page
    status, location, _ = browser.post_form("/logout", {}, form_page="/student")
    assert status == 302 and location_path(location) == "/login"
    status, location, _ = browser.get("/student")
    assert status == 302 and location_path(location) == "/login"
