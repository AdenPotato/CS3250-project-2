"""US1 register and log in - the Selenium black box test (#8).

Drives headless Chrome against the running Compose app and never imports the app. US1.4 is
not visible in a browser, so it reads the stored hash from postgres with `docker compose exec`.
"""
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.environ.get("CAMPUSEATS_URL", "http://localhost:5000").rstrip("/")
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_USER = os.environ.get("POSTGRES_USER", "campuseats")
DB_NAME = os.environ.get("POSTGRES_DB", "campuseats")
PASSWORD = "correct-horse-1"


@pytest.fixture
def browser():
    options = webdriver.ChromeOptions()
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,900"):
        options.add_argument(arg)
    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as err:
        # CI has Chrome, so a missing browser there is a failure; on a laptop it is a skip
        if os.environ.get("CI"):
            raise
        pytest.skip(f"Chrome could not start - install Chrome or Chromium to run this test ({err.msg})")
    yield driver
    driver.quit()


def wait_for(driver, element_id):
    return WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, element_id)))


def wait_for_path(driver, path):
    WebDriverWait(driver, 10).until(lambda d: d.current_url.split("?")[0] == BASE_URL + path)


def unique_email():
    return f"sel-{uuid.uuid4().hex[:10]}@campus.test"


def register(driver, name="Selenium User", email=None, password=PASSWORD, role="student"):
    """Fill the registration form in the browser; None for role leaves both radios unticked."""
    driver.get(BASE_URL + "/register")
    for field, value in (("name", name), ("email", email), ("password", password)):
        wait_for(driver, f"register-{field}").send_keys(value)
    if role:
        driver.find_element(By.ID, f"register-role-{role}").click()
    driver.find_element(By.ID, "register-submit").click()


def log_in(driver, email, password=PASSWORD):
    driver.get(BASE_URL + "/login")
    wait_for(driver, "login-email").send_keys(email)
    driver.find_element(By.ID, "login-password").send_keys(password)
    driver.find_element(By.ID, "login-submit").click()


def db_query(sql):
    if not shutil.which("docker"):
        pytest.skip("docker not on PATH - the database checks need `docker compose exec db`")
    cmd = ["docker", "compose", "exec", "-T", "db", "psql", "-U", DB_USER, "-d", DB_NAME, "-tAc", sql]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        pytest.skip(f"could not query the db container: {result.stderr.strip()}")
    return result.stdout.strip()


def count_users(email):
    # emails are uuid-based, so there is nothing to escape in them
    return int(db_query(f"SELECT count(*) FROM users WHERE email = '{email}'"))


# US1.1 - account stored in postgres, redirected to the login page

@pytest.mark.parametrize("role", ["student", "vendor"])
def test_us1_1_register_stores_account_and_redirects_to_login(browser, role):
    email = unique_email()
    register(browser, name="Sel Register", email=email, role=role)
    wait_for_path(browser, "/login")
    assert "Account created" in wait_for(browser, "flash-success").text
    assert db_query(f"SELECT name, role FROM users WHERE email = '{email}'") == f"Sel Register|{role}"


# US1.2 - failure case: a second account with the same email is refused

def test_us1_2_duplicate_email_rejected(browser):
    email = unique_email()
    register(browser, email=email)
    wait_for_path(browser, "/login")
    register(browser, name="Someone Else", email=email)
    assert wait_for(browser, "register-email-error").text == "That email is already registered."
    assert browser.current_url == BASE_URL + "/register"
    assert count_users(email) == 1


# US1.3 - failure case: each empty required field is named and nothing is stored

@pytest.mark.parametrize(
    "empty, message",
    [
        ("name", "Enter your name."),
        ("email", "Enter your email."),
        ("password", "Enter a password."),
        ("role", "Choose Student or Vendor."),
    ],
)
def test_us1_3_empty_field_identified(browser, empty, message):
    email, name = unique_email(), f"Sel Empty {uuid.uuid4().hex[:10]}"
    values = {"name": name, "email": email, "password": PASSWORD, "role": "student"}
    values[empty] = None if empty == "role" else ""
    register(browser, **values)
    assert wait_for(browser, f"register-{empty}-error").text == message
    # matched by email or by the unique name, so the check still works when one of them is empty
    assert db_query(f"SELECT count(*) FROM users WHERE email = '{email}' OR name = '{name}'") == "0"


# US1.4 - the stored password is a hash, never the plain text

def test_us1_4_password_stored_hashed(browser):
    email = unique_email()
    register(browser, email=email)
    wait_for_path(browser, "/login")
    stored = db_query(f"SELECT password_hash FROM users WHERE email = '{email}'")
    assert stored, "the account was not stored"
    assert PASSWORD not in stored
    assert stored.split(":")[0] in ("scrypt", "pbkdf2")  # werkzeug's hash formats


# US1.5 - correct login lands on the role's home page; a wrong password stays logged out

@pytest.mark.parametrize("role", ["student", "vendor"])
def test_us1_5_login_lands_on_role_home(browser, role):
    email = unique_email()
    register(browser, name="Sel Login", email=email, role=role)
    wait_for_path(browser, "/login")
    log_in(browser, email)
    assert wait_for(browser, f"{role}-home").text == "Welcome, Sel Login"
    assert browser.current_url == f"{BASE_URL}/{role}"
    assert "Sel Login" in browser.find_element(By.ID, "nav-user").text


def test_us1_5_wrong_password_rejected_and_stays_logged_out(browser):
    email = unique_email()
    register(browser, email=email)
    wait_for_path(browser, "/login")
    log_in(browser, email, password="wrong-password-9")
    assert wait_for(browser, "flash-error").text == "Incorrect email or password."
    assert browser.find_elements(By.ID, "nav-user") == []
    browser.get(BASE_URL + "/student")
    wait_for_path(browser, "/login")  # still signed out, so the home page bounces to login
