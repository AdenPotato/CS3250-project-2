"""US10 rate a pickup - Selenium black box tests. Helpers are in conftest.py."""
from selenium.webdriver.common.by import By

from conftest import (BASE_URL, confirm_pickup, field_error_shown, flash, log_in, pickup_code_from_flash, post_listing,
                      register, reservation_card, reserve, wait_for)


def picked_up(d, accounts, who, listing_id, portions=1):
    """Reserve as `who`, then confirm the pickup as the vendor; ends signed in as `who`."""
    log_in(d, accounts[who]["email"])
    reserve(d, listing_id, portions)
    code = pickup_code_from_flash(d)
    log_in(d, accounts["vendor"]["email"])
    confirm_pickup(d, code)
    assert flash(d, "success").startswith("Pickup confirmed")  # wait, or the next log_in cuts the POST off
    log_in(d, accounts[who]["email"])


def rate(d, listing_id, stars, comment=""):
    d.get(BASE_URL + "/reservations")
    reservation_card(d, listing_id).find_element(By.CLASS_NAME, "rate-reservation").click()
    if stars:
        wait_for(d, By.ID, f"rate-stars-{stars}").click()
    if comment:
        # set the value directly; send_keys of 300 characters is slow and adds nothing
        d.execute_script("arguments[0].value = arguments[1]", d.find_element(By.ID, "rate-comment"), comment)
    d.find_element(By.ID, "rate-submit").click()


def test_us10_1_rating_is_stored_and_shown(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    picked_up(driver, accounts, "student", listing_id)

    rate(driver, listing_id, 4, "Warm and on time.")
    assert flash(driver, "success") == "Thanks! Your rating was submitted."
    card = reservation_card(driver, listing_id)
    assert card.find_element(By.CLASS_NAME, "reservation-rating").text == 'Your rating: 4/5 - "Warm and on time."'


def test_us10_1_stars_required_and_comment_capped_at_300(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    picked_up(driver, accounts, "student", listing_id)

    rate(driver, listing_id, None, "no stars picked")
    assert field_error_shown(driver, "Choose 1 to 5 stars.")
    rate(driver, listing_id, 3, "x" * 301)
    assert field_error_shown(driver, "Comment must be at most 300 characters.")
    rate(driver, listing_id, 3, "x" * 300)
    assert flash(driver, "success") == "Thanks! Your rating was submitted."


def test_us10_2_rated_once_and_only_when_picked_up(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    picked_up(driver, accounts, "student", listing_id)
    rate(driver, listing_id, 5)
    assert flash(driver, "success") == "Thanks! Your rating was submitted."
    card = reservation_card(driver, listing_id)
    assert not card.find_elements(By.CLASS_NAME, "rate-reservation")  # the Rate button is gone

    # a second rating through the URL is refused
    reservation_id = card.get_attribute("id").split("-")[1]
    driver.get(f"{BASE_URL}/reservations/{reservation_id}/rate")
    assert flash(driver, "error") == "You have already rated this pickup."

    # an active reservation has no Rate button and its URL is refused
    log_in(driver, accounts["student2"]["email"])
    reserve(driver, listing_id, 1)
    pickup_code_from_flash(driver)  # wait for the reservation, or the next page load cuts the POST off
    card = reservation_card(driver, listing_id)
    assert not card.find_elements(By.CLASS_NAME, "rate-reservation")
    driver.get(f"{BASE_URL}/reservations/{card.get_attribute('id').split('-')[1]}/rate")
    assert flash(driver, "error") == "Only picked-up reservations can be rated."


def test_us10_3_vendor_sees_average_and_comments(driver, accounts):
    # a vendor of its own, so the average covers only this test's ratings
    vendor = register(driver, "Sel Rated", "vendor")
    log_in(driver, vendor)
    listing_id, _ = post_listing(driver, portions=5)
    for who, stars, comment in (("student", 5, "Best soup."), ("student2", 2, "")):
        log_in(driver, accounts[who]["email"])
        reserve(driver, listing_id, 1)
        code = pickup_code_from_flash(driver)
        log_in(driver, vendor)
        confirm_pickup(driver, code)
        assert flash(driver, "success").startswith("Pickup confirmed")
        log_in(driver, accounts[who]["email"])
        rate(driver, listing_id, stars, comment)
        assert flash(driver, "success") == "Thanks! Your rating was submitted."

    log_in(driver, vendor)
    driver.get(BASE_URL + "/vendor/listings")
    row = wait_for(driver, By.ID, f"listing-row-{listing_id}")
    assert row.find_element(By.CLASS_NAME, "listing-rating").text == "3.5/5 (2)"
    driver.get(f"{BASE_URL}/vendor/listings/{listing_id}")
    assert wait_for(driver, By.ID, "listing-average-rating").text == "Average: 3.5/5 from 2 ratings"
    comments = [e.text for e in driver.find_elements(By.CLASS_NAME, "rating-comment")]
    assert comments == ["Best soup."]
