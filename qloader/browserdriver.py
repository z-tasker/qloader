from __future__ import annotations
import random
import time
import hashlib
from collections import defaultdict

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


class NoImagesInWebElementError(Exception):
    pass


def pick_best_actual_image(actual_images: List[WebElement]) -> WebElement:
    if len(actual_images) == 0:
        raise NoImagesInWebElementError()
    elif len(actual_images) == 1:
        return actual_images[0]
    else:
        scores = defaultdict(int)
        for i, actual_image in enumerate(actual_images):
            scores[i] += 1
            if "encrypted-tbn0.gstatic.com" in actual_image.get_attribute("src"):
                scores[i] -= 1
        top_scorers = list()
        for i, score in enumerate(scores):
            if score == max(scores.values()):
                top_scorers.append(i)

        return actual_images[random.choice(top_scorers)]


def fetch_google_image_urls(
    query: str,
    driver: WebDriver,
    sleep_between_interactions: float = 0.5,
    language: str = "en",
    extra_query_params: Optional[Dict[str, str]] = None,
    track_related: bool = False,
) -> List(Dict[str, str]):
    """
        Accumulate a set of image urls.
        The find_elements_by_css_selector approach for interacting with the page.
        feels a little bit brittle, it's possible these values could change.
    """

    log = get_logger("fetch_google_image_urls")
    random_sleep(sleep_between_interactions)

    def scroll_to_end(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_sleep(sleep_between_interactions)

    query_params = {
        "safe": "off",
        "tbm": "isch",
        "source": "hp",
        "q": f'+"{query}"',
        "oq": f'+"{query}"',
        "lr": f"lang_{language}",
    }

    if extra_query_params is not None:
        query_params.update(extra_query_params)

    query_params_str = "&".join([f"{key}={val}" for key, val in query_params.items()])

    # build the google query
    search_url = f"https://www.google.com/search?{query_params_str}"

    log.info(f"searching: {search_url}")

    # load the page
    driver.get(search_url)
    random_sleep(sleep_between_interactions)

    image_links = list()
    results_start = 0
    results_seen = list()
    start = time.time()
    breakpoints = 0
    while True:  # browse and download until we hit our target image count
        scroll_to_end(driver)

        # get all image thumbnail results
        thumbnail_results = driver.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        log.debug(
            f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}"
        )
        if results_start == number_results:
            breakpoints += 1
            if breakpoints >= 5:
                break

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                random_sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls
            try:
                actual_image = pick_best_actual_image(
                    driver.find_elements_by_css_selector("img.n3VNCb")
                )
            except NoImagesInWebElementError as exc:
                log.debug("skipping empty element")
                continue
            image_link = dict()
            if actual_image.get_attribute(
                "src"
            ) and "http" in actual_image.get_attribute("src"):
                image_link.update({"src": actual_image.get_attribute("src")})
                image_link.update({"alt": actual_image.get_attribute("alt")})

            else:
                continue

            if track_related:
                related_images = list()
                for related_section in driver.find_elements_by_css_selector(
                    "div.EVPn8e"
                ):
                    for related_image in related_section.find_elements_by_tag_name(
                        "img"
                    ):
                        related_images.append(
                            {
                                "src": related_image.get_attribute("src"),
                                "alt": related_image.get_attribute("alt"),
                            }
                        )
                image_link["related_images"] = related_images

            result_id = hashlib.md5(
                f"{image_link['alt']}{image_link['src']}".encode("utf-8")
            ).hexdigest()
            if result_id not in results_seen:
                yield image_link
                results_seen.append(result_id)

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
                # Show More Results
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
                log.info(f"No path for more images found")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    log.info(f"scraped for {int(time.time() - start)} seconds")
