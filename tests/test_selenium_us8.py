"""US8 filter listings - Selenium black box tests. Helpers are in conftest.py.

Other tests and the seed data post listings too, so each check is about the four listings
posted here: which of them are shown, and that every card shown matches the filter.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from conftest import BASE_URL, log_in, new_driver, post_listing, register, wait_for

LISTINGS = {
    "vegan_gf_library": (("vegan", "gluten-free"), "Library Cafe"),
    "vegan_library": (("vegan",), "Library Cafe"),
    "vegan_gf_science": (("vegan", "gluten-free"), "Science Building"),
    "plain_union": ((), "Student Union"),
}


@pytest.fixture(scope="module")
def posted(accounts):
    """Post the four listings once as a vendor of their own; returns {key: listing id}."""
    d = new_driver()
    try:
        log_in(d, register(d, "Sel Filters", "vendor"))
        return {key: post_listing(d, tags=tags, location=loc)[0] for key, (tags, loc) in LISTINGS.items()}
    finally:
        d.quit()


def submit(d, button_id):
    before = d.find_element(By.ID, "filter-form")
    d.find_element(By.ID, button_id).click()
    WebDriverWait(d, 10).until(EC.staleness_of(before))  # wait for the filtered page
    wait_for(d, By.ID, "filter-form")


def filter_by(d, tags=(), location=""):
    d.get(BASE_URL + "/listings")
    for tag in tags:
        wait_for(d, By.ID, "filter-tag-" + tag.replace(" ", "-")).click()
    Select(d.find_element(By.ID, "filter-location")).select_by_value(location)
    submit(d, "filter-submit")


def shown(d, posted):
    """The keys of our listings on the page."""
    return {key for key, listing_id in posted.items() if d.find_elements(By.ID, f"listing-{listing_id}")}


def cards(d):
    """(tags, location) for every listing card on the page, ours or not."""
    out = []
    for card in d.find_elements(By.CLASS_NAME, "listing-card"):
        tags = {b.text for b in card.find_elements(By.CSS_SELECTOR, ".badge")}
        location = card.text.split("Pickup Location: ", 1)[1].split("\n", 1)[0]
        out.append((tags, location))
    return out


def test_us8_1_only_listings_with_all_selected_tags(driver, accounts, posted):
    log_in(driver, accounts["student"]["email"])
    filter_by(driver, tags=("vegan", "gluten-free"))
    assert shown(driver, posted) == {"vegan_gf_library", "vegan_gf_science"}
    assert all({"vegan", "gluten-free"} <= tags for tags, _ in cards(driver))


def test_us8_2_only_listings_at_the_location(driver, accounts, posted):
    log_in(driver, accounts["student"]["email"])
    filter_by(driver, location="Library Cafe")
    assert shown(driver, posted) == {"vegan_gf_library", "vegan_library"}
    assert all(location == "Library Cafe" for _, location in cards(driver))


def test_us8_2_location_and_tags_combined(driver, accounts, posted):
    log_in(driver, accounts["student"]["email"])
    filter_by(driver, tags=("vegan", "gluten-free"), location="Library Cafe")
    assert shown(driver, posted) == {"vegan_gf_library"}
    assert all({"vegan", "gluten-free"} <= tags and location == "Library Cafe" for tags, location in cards(driver))
    # the chosen filters stay selected on the results page
    assert driver.find_element(By.ID, "filter-tag-vegan").is_selected()
    assert Select(driver.find_element(By.ID, "filter-location")).first_selected_option.get_attribute("value") == "Library Cafe"


def test_us8_3_clear_filters_shows_all_again(driver, accounts, posted):
    log_in(driver, accounts["student"]["email"])
    filter_by(driver, tags=("vegan", "gluten-free"), location="Library Cafe")
    assert shown(driver, posted) == {"vegan_gf_library"}
    submit(driver, "clear-filters")
    assert shown(driver, posted) == set(LISTINGS)
    assert not driver.find_element(By.ID, "filter-tag-vegan").is_selected()
    assert Select(driver.find_element(By.ID, "filter-location")).first_selected_option.get_attribute("value") == ""


def test_us8_no_match_shows_the_empty_message(driver, accounts, posted):
    log_in(driver, accounts["student"]["email"])
    # no seed listing and no test listing is both vegan and contains nuts
    filter_by(driver, tags=("vegan", "contains nuts"))
    assert not cards(driver)
    assert "No listings are available at this time." in driver.page_source
