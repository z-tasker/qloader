from __future__ import annotations
import random
import time

import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

from .logger import get_logger


def get_browser_options(browser: str) -> Any:
    try:
        options = {"Firefox": FirefoxOptions(), "Chrome": ChromeOptions()}[browser]
    except KeyError:
        raise ValueError(f"Unknown browser '{browser}'")

    options.add_argument("--headless")

    if browser == "Chrome":
        options.add_argument("--no-sandbox")

    return options


def random_sleep(min_time: float) -> None:
    """
        Fuzz wait times between [min_time, min_time*2]
    """
    time.sleep(min_time + min_time * random.random())


def fetch_google_image_urls(
    query: str,
    driver: WebDriver,
    sleep_between_interactions: float = 0.5,
    desired_count: int = 100,
    language: str = "en",
) -> Set(str):
    """
        Accumulate a set of google image urls until desired_count is reached
        The find_elements_by_css_selector approach for interacting with the page feels a little bit brittle, it's possible these values could change.
    """

    log = get_logger("fetch_google_image_urls")
    random_sleep(sleep_between_interactions)

    def scroll_to_end(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_sleep(sleep_between_interactions)

    # build the google query
    search_url = f"https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={query}&oq={query}&gs_l=img&lr=lang_{language}"

    # load the page
    driver.get(search_url)
    random_sleep(sleep_between_interactions)

    image_links = set()
    results_start = 0
    start = time.time()
    while True:  # browse and download until we hit our target image count
        scroll_to_end(driver)

        # get all image thumbnail results
        thumbnail_results = driver.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        log.debug(
            f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}"
        )

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                random_sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls
            actual_images = driver.find_elements_by_css_selector("img.n3VNCb")
            for actual_image in actual_images:
                if actual_image.get_attribute(
                    "src"
                ) and "http" in actual_image.get_attribute("src"):
                    image_links.add(actual_image.get_attribute("src"))
                    if len(image_links) >= desired_count:
                        # We're done
                        return image_links

        else:
            log.debug(f"Found: {len(image_links)} image links, looking for more ...")
            random_sleep(sleep_between_interactions * 2)

            scroll_to_end(driver)

            # look for the More Results or Load More Anyway button, preferring the latter as it is conditional
            try:
                see_more_anyway_button = driver.find_element_by_css_selector(".r0zKGf")
            except selenium.common.exceptions.NoSuchElementException:
                see_more_anyway_button = None

            try:
                load_more_button = driver.find_element_by_css_selector(".mye4qd")
            except selenium.common.exceptions.NoSuchElementException:
                load_more_button = None

            if see_more_anyway_button:
                # prefer the see more anyway button
                try:
                    driver.execute_script("document.querySelector('.r0zKGf').click();")
                    log.debug("clicked See More Anyway")
                    random_sleep(sleep_between_interactions)
                except selenium.common.exceptions.NoSuchElementException:
                    pass
            elif load_more_button:
                driver.execute_script("document.querySelector('.mye4qd').click();")
                log.debug("clicked More Results")
                random_sleep(sleep_between_interactions * 10)
            else:
                log.debug(driver.page_source)
                log.debug(
                    f"{image_count}/{desired_count} images gathered, but no 'load_more_button' found, returning what we have so far"
                )
                return image_links

        # move the result startpoint further down
        results_start = len(thumbnail_results)
    log.info(f"image links gathered by scraper in {int(time.time() - start)} seconds")
