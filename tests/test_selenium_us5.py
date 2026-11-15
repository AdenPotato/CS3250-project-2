"""US5 manage listings - Selenium black box tests (#112). Helpers are in conftest.py."""
from selenium.webdriver.common.by import By

from conftest import (BASE_URL, counts, end_window, field_error_shown, flash, is_not_found, listing_row, log_in,
                      pickup_code_from_flash, post_listing, reservation_card, reserve, wait_for)


def status(d, listing_id):
    return listing_row(d, listing_id).find_element(By.CLASS_NAME, "listing-status").text


def test_us5_1_my_listings_shows_status_and_counts(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    active, _ = post_listing(driver, portions=6)
    ended, _ = post_listing(driver, portions=4)
    cancelled, _ = post_listing(driver, portions=3)
    log_in(driver, accounts["student"]["email"])
    reserve(driver, active, 2)
    pickup_code_from_flash(driver)

    log_in(driver, accounts["vendor"]["email"])
    listing_row(driver, cancelled).find_element(By.ID, f"cancel-listing-{cancelled}").click()
    end_window(ended)
    assert status(driver, active) == "active"
    assert counts(driver, active) == (2, 4, 6)
    assert status(driver, ended) == "ended"
    assert status(driver, cancelled) == "cancelled"


def test_us5_2_edit_without_reservations_saves_and_validates(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, title = post_listing(driver, portions=5)
    listing_row(driver, listing_id).find_element(By.ID, f"edit-listing-{listing_id}").click()

    # same rule as US2.2: the end must come after the start
    start = wait_for(driver, By.ID, "window_start").get_attribute("value")
    driver.execute_script("arguments[0].value = arguments[1]", driver.find_element(By.ID, "window_end"), start)
    driver.find_element(By.ID, "submit").click()
    assert field_error_shown(driver, "Pickup window end must be after the start time.")
    assert counts(driver, listing_id) == (0, 5, 5)

    driver.get(f"{BASE_URL}/vendor/listings/{listing_id}/edit")
    new_title = title + " edited"
    wait_for(driver, By.ID, "title").clear()
    driver.find_element(By.ID, "title").send_keys(new_title)
    driver.find_element(By.ID, "portions").clear()
    driver.find_element(By.ID, "portions").send_keys("8")
    driver.find_element(By.ID, "submit").click()
    assert flash(driver, "success") == "Listing updated."
    assert listing_row(driver, listing_id).find_element(By.TAG_NAME, "a").text == new_title
    assert counts(driver, listing_id) == (0, 8, 8)


def test_us5_3_portions_cannot_go_below_reserved(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    log_in(driver, accounts["student"]["email"])
    reserve(driver, listing_id, 2)
    pickup_code_from_flash(driver)

    log_in(driver, accounts["vendor"]["email"])
    for portions, saved in (("1", False), ("2", True)):
        driver.get(f"{BASE_URL}/vendor/listings/{listing_id}/edit")
        wait_for(driver, By.ID, "portions").clear()
        driver.find_element(By.ID, "portions").send_keys(portions)
        driver.find_element(By.ID, "submit").click()
        if saved:
            assert flash(driver, "success") == "Listing updated."
        else:
            assert field_error_shown(driver, "2 portions are already reserved, so portions cannot be set below 2.")
    assert counts(driver, listing_id) == (2, 0, 2)


def test_us5_4_cancel_hides_listing_and_cancels_its_reservations(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, title = post_listing(driver, portions=5)
    log_in(driver, accounts["student"]["email"])
    reserve(driver, listing_id, 1)
    pickup_code_from_flash(driver)

    log_in(driver, accounts["vendor"]["email"])
    listing_row(driver, listing_id).find_element(By.ID, f"cancel-listing-{listing_id}").click()
    assert flash(driver, "success") == "Listing cancelled. Active reservations cancelled."

    log_in(driver, accounts["student2"]["email"])
    driver.get(BASE_URL + "/listings")
    assert title not in driver.page_source
    driver.get(f"{BASE_URL}/listings/{listing_id}/reserve")
    assert is_not_found(driver)

    log_in(driver, accounts["student"]["email"])
    assert reservation_card(driver, listing_id).find_element(By.CLASS_NAME, "reservation-status").text == "cancelled"


def test_us5_5_detail_lists_reservers_and_other_vendors_are_blocked(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    for who, portions in (("student", 2), ("student2", 1)):
        log_in(driver, accounts[who]["email"])
        reserve(driver, listing_id, portions)
        pickup_code_from_flash(driver)

    log_in(driver, accounts["vendor"]["email"])
    driver.get(f"{BASE_URL}/vendor/listings/{listing_id}")
    rows = {
        r.find_element(By.CLASS_NAME, "reservation-student").text: r.find_element(By.CLASS_NAME, "reservation-portions").text
        for r in driver.find_elements(By.CLASS_NAME, "reservation-row")
    }
    assert rows == {accounts["student"]["name"]: "2", accounts["student2"]["name"]: "1"}

    log_in(driver, accounts["vendor2"]["email"])
    for path in (f"/vendor/listings/{listing_id}", f"/vendor/listings/{listing_id}/edit"):
        driver.get(BASE_URL + path)
        assert is_not_found(driver), path
    driver.get(BASE_URL + "/vendor/listings")
    assert not driver.find_elements(By.ID, f"listing-row-{listing_id}")
