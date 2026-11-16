"""US6 view and cancel my reservations - Selenium black box tests (#112). Helpers are in conftest.py."""
from selenium.webdriver.common.by import By

from conftest import (confirm_pickup, counts, end_window, flash, log_in, pickup_code_from_flash, post_listing,
                      reservation_card, reserve)


def test_us6_1_my_reservations_shows_every_detail(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, title = post_listing(driver, portions=5, location="Library Cafe")
    log_in(driver, accounts["student"]["email"])
    reserve(driver, listing_id, 2)
    code = pickup_code_from_flash(driver)

    card = reservation_card(driver, listing_id)
    text = card.text
    assert card.find_element(By.CLASS_NAME, "card-title").text == title
    assert f"Vendor: {accounts['vendor']['name']}" in text
    assert "Pickup Location: Library Cafe" in text
    assert "Pickup Window:" in text
    assert card.find_element(By.CLASS_NAME, "reservation-portions").text == "2"
    assert card.find_element(By.CLASS_NAME, "reservation-code").text == code
    assert card.find_element(By.CLASS_NAME, "reservation-status").text == "active"


def test_us6_2_cancel_active_reservation_returns_portions(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    log_in(driver, accounts["student"]["email"])
    reserve(driver, listing_id, 2)
    pickup_code_from_flash(driver)

    reservation_card(driver, listing_id).find_element(By.CLASS_NAME, "cancel-reservation").click()
    assert flash(driver, "success") == "Reservation cancelled. Portions returned."
    assert reservation_card(driver, listing_id).find_element(By.CLASS_NAME, "reservation-status").text == "cancelled"

    log_in(driver, accounts["vendor"]["email"])
    assert counts(driver, listing_id) == (0, 5, 5)


def test_us6_3_no_cancel_option_unless_active(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    picked_up, _ = post_listing(driver, portions=5)
    cancelled, _ = post_listing(driver, portions=5)
    no_show, _ = post_listing(driver, portions=5)

    log_in(driver, accounts["student"]["email"])
    codes = {}
    for listing_id in (picked_up, cancelled, no_show):
        reserve(driver, listing_id, 1)
        codes[listing_id] = pickup_code_from_flash(driver)
    reservation_card(driver, cancelled).find_element(By.CLASS_NAME, "cancel-reservation").click()
    flash(driver, "success")

    log_in(driver, accounts["vendor"]["email"])
    confirm_pickup(driver, codes[picked_up])
    flash(driver, "success")
    end_window(no_show)

    log_in(driver, accounts["student"]["email"])
    for listing_id, expected in ((picked_up, "picked up"), (cancelled, "cancelled"), (no_show, "no-show")):
        card = reservation_card(driver, listing_id)
        assert card.find_element(By.CLASS_NAME, "reservation-status").text == expected
        assert not card.find_elements(By.CLASS_NAME, "cancel-reservation"), expected
