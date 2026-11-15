"""US7 confirm pickup - Selenium black box tests (#112). Helpers are in conftest.py."""
from selenium.webdriver.common.by import By

from conftest import (BASE_URL, confirm_pickup, end_window, flash, log_in, pickup_code_from_flash, post_listing,
                      reservation_card, reserve)


def reserve_as(d, accounts, who, listing_id, portions):
    log_in(d, accounts[who]["email"])
    reserve(d, listing_id, portions)
    return pickup_code_from_flash(d)


def test_us7_1_valid_code_marks_picked_up_and_names_the_student(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    code = reserve_as(driver, accounts, "student", listing_id, 2)

    log_in(driver, accounts["vendor"]["email"])
    confirm_pickup(driver, code.lower())  # typed in lower case, as a hurried vendor might
    assert flash(driver, "success") == f"Pickup confirmed for {accounts['student']['name']} (2 portion(s))."

    log_in(driver, accounts["student"]["email"])
    assert reservation_card(driver, listing_id).find_element(By.CLASS_NAME, "reservation-status").text == "picked up"


def test_us7_2_unknown_code_rejected(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    confirm_pickup(driver, "ZZZZZZ")
    assert flash(driver, "error") == "Invalid pickup code."


def test_us7_2_other_vendors_code_rejected(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    code = reserve_as(driver, accounts, "student", listing_id, 1)

    log_in(driver, accounts["vendor2"]["email"])
    confirm_pickup(driver, code)
    assert flash(driver, "error") == "This pickup code does not belong to one of your listings."
    log_in(driver, accounts["student"]["email"])
    assert reservation_card(driver, listing_id).find_element(By.CLASS_NAME, "reservation-status").text == "active"


def test_us7_2_used_and_cancelled_codes_rejected(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    used = reserve_as(driver, accounts, "student", listing_id, 1)
    cancelled = reserve_as(driver, accounts, "student2", listing_id, 1)
    reservation_card(driver, listing_id).find_element(By.CLASS_NAME, "cancel-reservation").click()
    flash(driver, "success")

    log_in(driver, accounts["vendor"]["email"])
    confirm_pickup(driver, used)
    flash(driver, "success")
    for code in (used, cancelled):
        confirm_pickup(driver, code)
        assert flash(driver, "error") == "This reservation has already been used or cancelled."


def test_us7_3_ended_window_shows_active_reservations_as_no_show(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    code = reserve_as(driver, accounts, "student", listing_id, 1)
    end_window(listing_id)

    # the student sees it first, before the vendor has opened any page
    assert reservation_card(driver, listing_id).find_element(By.CLASS_NAME, "reservation-status").text == "no-show"

    log_in(driver, accounts["vendor"]["email"])
    driver.get(f"{BASE_URL}/vendor/listings/{listing_id}")
    assert driver.find_element(By.CSS_SELECTOR, f'.reservation-row[data-code="{code}"] .reservation-status').text == "no-show"
    confirm_pickup(driver, code)
    assert flash(driver, "error") == "This reservation has expired and is marked as no-show."
