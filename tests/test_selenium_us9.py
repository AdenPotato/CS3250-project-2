"""US9 impact dashboard - Selenium black box tests. Helpers are in conftest.py."""
from datetime import datetime

from selenium.webdriver.common.by import By

from conftest import (BASE_URL, CAMPUS_TZ, confirm_pickup, end_window, field_error_shown, log_in, pickup_code_from_flash,
                      post_listing, register, reserve, wait_for)

STATS = ("listings-posted", "portions-posted", "portions-picked-up", "no-shows", "no-show-rate")


def show_range(d, start, end):
    """Open the dashboard and pick a date range the way the date pickers would."""
    d.get(BASE_URL + "/vendor/dashboard")
    for field, value in (("dashboard-start", start), ("dashboard-end", end)):
        d.execute_script("arguments[0].value = arguments[1]", wait_for(d, By.ID, field), value)
    d.find_element(By.ID, "dashboard-submit").click()


def stats(d):
    wait_for(d, By.ID, "stat-no-show-rate")
    return {name: d.find_element(By.ID, f"stat-{name}").text for name in STATS}


def test_us9_1_and_9_2_counts_and_no_show_rate(driver, accounts):
    # a vendor of its own, so other tests' listings never change the expected numbers
    vendor = register(driver, "Sel Dashboard", "vendor")
    log_in(driver, vendor)
    picked_id, _ = post_listing(driver, portions=6)
    missed_id, _ = post_listing(driver, portions=4)

    log_in(driver, accounts["student"]["email"])
    reserve(driver, picked_id, 2)
    code = pickup_code_from_flash(driver)
    reserve(driver, missed_id, 1)
    log_in(driver, accounts["student2"]["email"])
    reserve(driver, missed_id, 1)

    log_in(driver, vendor)
    confirm_pickup(driver, code)
    end_window(missed_id)  # both reservations on it become no-shows

    today = datetime.now(CAMPUS_TZ).date().isoformat()
    show_range(driver, today, today)
    # 2 no-show portions out of 4 reserved
    assert stats(driver) == {"listings-posted": "2", "portions-posted": "10", "portions-picked-up": "2",
                             "no-shows": "2", "no-show-rate": "50.0%"}


def test_us9_3_empty_range_shows_zeros(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    show_range(driver, "2020-01-01", "2020-01-31")
    assert stats(driver) == {"listings-posted": "0", "portions-posted": "0", "portions-picked-up": "0",
                             "no-shows": "0", "no-show-rate": "0%"}


def test_us9_end_before_start_is_a_form_error(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    show_range(driver, "2020-02-01", "2020-01-01")
    assert field_error_shown(driver, "The end date cannot be before the start date.")
    assert not driver.find_elements(By.ID, "stat-listings-posted")


def test_us9_students_cannot_open_the_dashboard(driver, accounts):
    log_in(driver, accounts["student"]["email"])
    driver.get(BASE_URL + "/vendor/dashboard")
    assert "Forbidden" in driver.page_source
