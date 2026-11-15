"""US4 reserve portions - Selenium black box tests (#112). Helpers are in conftest.py."""
import threading

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from conftest import (BASE_URL, counts, flash, log_in, open_reserve, pickup_code_from_flash, post_listing,
                      reservation_card, reserve, wait_for_path)


def test_us4_1_reserve_stores_reservation_decrements_and_shows_code(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, title = post_listing(driver, portions=5)

    log_in(driver, accounts["student"]["email"])
    reserve(driver, listing_id, 2)
    code = pickup_code_from_flash(driver)
    wait_for_path(driver, "/reservations")
    card = reservation_card(driver, listing_id)
    assert card.find_element(By.CLASS_NAME, "reservation-code").text == code
    assert card.find_element(By.CLASS_NAME, "reservation-portions").text == "2"
    assert card.find_element(By.CLASS_NAME, "reservation-status").text == "active"

    log_in(driver, accounts["vendor"]["email"])
    assert counts(driver, listing_id) == (2, 3, 5)


def test_us4_1_each_reservation_gets_its_own_code(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)
    codes = []
    for who in ("student", "student2"):
        log_in(driver, accounts[who]["email"])
        reserve(driver, listing_id, 1)
        codes.append(pickup_code_from_flash(driver))
    assert codes[0] != codes[1]


def test_us4_2_more_portions_than_remain_rejected(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=1)

    log_in(driver, accounts["student"]["email"])
    reserve(driver, listing_id, 2)
    assert flash(driver, "error") == "Not enough portions available."
    driver.get(BASE_URL + "/reservations")
    assert not driver.find_elements(By.CSS_SELECTOR, f'.reservation-card[data-listing-id="{listing_id}"]')

    log_in(driver, accounts["vendor"]["email"])
    assert counts(driver, listing_id) == (0, 1, 1)


def test_us4_3_second_reservation_on_same_listing_refused(driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=5)

    log_in(driver, accounts["student"]["email"])
    reserve(driver, listing_id, 1)
    pickup_code_from_flash(driver)
    reserve(driver, listing_id, 1)
    assert flash(driver, "error") == "You already have a reservation for this listing."

    log_in(driver, accounts["vendor"]["email"])
    assert counts(driver, listing_id) == (1, 4, 5)


def test_us4_4_two_students_racing_for_the_last_portion(driver, second_driver, accounts):
    log_in(driver, accounts["vendor"]["email"])
    listing_id, _ = post_listing(driver, portions=1)

    # both students have the form open with 1 portion chosen, then press Reserve together
    log_in(driver, accounts["student"]["email"])
    log_in(second_driver, accounts["student2"]["email"])
    open_reserve(driver, listing_id, 1)
    open_reserve(second_driver, listing_id, 1)
    together = threading.Barrier(2)

    def press(d):
        together.wait()
        d.find_element(By.ID, "submit").click()

    threads = [threading.Thread(target=press, args=(d,)) for d in (driver, second_driver)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    def outcome(d):
        # the reserve page has no flash, so wait until the response to the click has loaded
        WebDriverWait(d, 10).until(lambda x: x.find_elements(By.ID, "flash-success") or x.find_elements(By.ID, "flash-error"))
        return "reserved" if d.find_elements(By.ID, "flash-success") else flash(d, "error")

    outcomes = sorted(outcome(d) for d in (driver, second_driver))
    assert outcomes == ["Not enough portions available.", "reserved"]
    log_in(driver, accounts["vendor"]["email"])
    assert counts(driver, listing_id) == (1, 0, 1)
