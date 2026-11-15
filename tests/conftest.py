"""Shared browser helpers for the Selenium tests of US4-US7 (#112).

Everything goes through headless Chrome against the running Compose app. The database is
touched only through `docker compose exec db psql`, to end a pickup window - a browser cannot
make time pass.
"""
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = os.environ.get("CAMPUSEATS_URL", "http://localhost:5000").rstrip("/")
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_USER = os.environ.get("POSTGRES_USER", "campuseats")
DB_NAME = os.environ.get("POSTGRES_DB", "campuseats")
PASSWORD = "correct-horse-1"
CAMPUS_TZ = ZoneInfo("America/Denver")  # the app reads typed times as campus time (#95)


def new_driver():
    options = webdriver.ChromeOptions()
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,900"):
        options.add_argument(arg)
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as err:
        # CI has Chrome, so a missing browser there is a failure; on a laptop it is a skip
        if os.environ.get("CI"):
            raise
        pytest.skip(f"Chrome could not start - install Chrome or Chromium to run this test ({err.msg})")


@pytest.fixture
def driver():
    d = new_driver()
    yield d
    d.quit()


@pytest.fixture
def second_driver():
    d = new_driver()
    yield d
    d.quit()


# ---------- waiting and reading ----------

def wait_for(d, by, value, timeout=10):
    return WebDriverWait(d, timeout).until(EC.visibility_of_element_located((by, value)))


def wait_for_path(d, path):
    WebDriverWait(d, 10).until(lambda x: x.current_url.split("?")[0] == BASE_URL + path)


def flash(d, category):
    return wait_for(d, By.ID, f"flash-{category}").text


def field_error_shown(d, message, timeout=10):
    """Wait for a form error with exactly this text; a click returns before the next page loads."""
    def shown(x):
        return any(e.text == message for e in x.find_elements(By.CSS_SELECTOR, ".text-danger, .field-error"))
    try:
        WebDriverWait(d, timeout).until(shown)
        return True
    except TimeoutException:
        return False


# ---------- accounts ----------

def register(d, name, role):
    email = f"sel-{role}-{uuid.uuid4().hex[:8]}@campus.test"
    d.delete_all_cookies()
    d.get(BASE_URL + "/register")
    wait_for(d, By.ID, "register-name").send_keys(name)
    d.find_element(By.ID, "register-email").send_keys(email)
    d.find_element(By.ID, "register-password").send_keys(PASSWORD)
    d.find_element(By.ID, f"register-role-{role}").click()
    d.find_element(By.ID, "register-submit").click()
    wait_for_path(d, "/login")
    return email


def log_in(d, email):
    """Sign in as `email` in this browser, dropping whoever was signed in before."""
    d.get(BASE_URL + "/login")
    d.delete_all_cookies()
    d.get(BASE_URL + "/login")
    wait_for(d, By.ID, "login-email").send_keys(email)
    d.find_element(By.ID, "login-password").send_keys(PASSWORD)
    d.find_element(By.ID, "login-submit").click()
    wait_for(d, By.ID, "nav-user")


@pytest.fixture(scope="session")
def accounts():
    """Fresh accounts made through the register page, so the tests pass on any database."""
    d = new_driver()
    try:
        made = {
            "vendor": ("Sel Deli", register(d, "Sel Deli", "vendor")),
            "vendor2": ("Sel Bakery", register(d, "Sel Bakery", "vendor")),
            "student": ("Sel Sam", register(d, "Sel Sam", "student")),
            "student2": ("Sel Riley", register(d, "Sel Riley", "student")),
        }
    finally:
        d.quit()
    return {key: {"name": name, "email": email} for key, (name, email) in made.items()}


# ---------- listings and reservations, all through the pages ----------

def _local(dt):
    return dt.strftime("%Y-%m-%dT%H:%M")


def post_listing(d, portions=5, location="Student Union", start_in=timedelta(hours=1), length=timedelta(hours=2)):
    """Post a listing as the signed-in vendor and return (id, title)."""
    title = f"Sel {uuid.uuid4().hex[:8]}"
    start = datetime.now(CAMPUS_TZ).replace(second=0, microsecond=0) + start_in
    d.get(BASE_URL + "/listings/new")
    wait_for(d, By.ID, "title").send_keys(title)
    d.find_element(By.ID, "description").send_keys("Made by the Selenium tests.")
    d.find_element(By.ID, "portions").send_keys(str(portions))
    Select(d.find_element(By.ID, "location")).select_by_value(location)
    # Chrome's datetime-local picker takes locale-specific keystrokes, so set the value the
    # way the picker does and let the form submit it as typed
    for field, value in (("window_start", start), ("window_end", start + length)):
        d.execute_script("arguments[0].value = arguments[1]", d.find_element(By.ID, field), _local(value))
    d.find_element(By.ID, "submit").click()
    wait_for_path(d, "/vendor")
    d.get(BASE_URL + "/vendor/listings")
    href = wait_for(d, By.LINK_TEXT, title).get_attribute("href")
    return int(href.rstrip("/").rsplit("/", 1)[1]), title


def open_reserve(d, listing_id, portions):
    d.get(f"{BASE_URL}/listings/{listing_id}/reserve")
    wait_for(d, By.ID, f"portions-{portions - 1}").click()  # radio choices are 1 and 2


def reserve(d, listing_id, portions):
    open_reserve(d, listing_id, portions)
    d.find_element(By.ID, "submit").click()


def reservation_card(d, listing_id):
    d.get(BASE_URL + "/reservations")
    return wait_for(d, By.CSS_SELECTOR, f'.reservation-card[data-listing-id="{listing_id}"]')


def pickup_code_from_flash(d):
    match = re.search(r"Your pickup code is ([A-Z0-9]{6})$", flash(d, "success"))
    assert match, "no pickup code in the confirmation"
    return match.group(1)


def listing_row(d, listing_id):
    d.get(BASE_URL + "/vendor/listings")
    return wait_for(d, By.ID, f"listing-row-{listing_id}")


def counts(d, listing_id):
    """My Listings' 'reserved / remaining / total' cell, as a tuple of ints."""
    cell = listing_row(d, listing_id).find_element(By.CLASS_NAME, "listing-counts").text
    return tuple(int(n) for n in cell.split("/"))


def confirm_pickup(d, code):
    d.get(BASE_URL + "/vendor/confirm-pickup")
    wait_for(d, By.ID, "pickup_code").send_keys(code)
    d.find_element(By.ID, "submit").click()


def is_not_found(d):
    return "Not Found" in d.find_element(By.TAG_NAME, "h1").text


# ---------- time ----------

def end_window(listing_id):
    """Move a listing's pickup window into the past - the one thing a browser cannot do."""
    if not shutil.which("docker"):
        pytest.skip("docker not on PATH - ending a pickup window needs `docker compose exec db`")
    sql = (f"UPDATE listings SET pickup_start = now() - interval '2 hours', "
           f"pickup_end = now() - interval '1 minute' WHERE id = {int(listing_id)}")
    cmd = ["docker", "compose", "exec", "-T", "db", "psql", "-U", DB_USER, "-d", DB_NAME, "-tAc", sql]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
    if result.returncode != 0 or "UPDATE 1" not in result.stdout:
        pytest.skip(f"could not end the pickup window: {result.stderr.strip() or result.stdout.strip()}")
