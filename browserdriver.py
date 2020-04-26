from __future__ import annotations
import random
import time
from selenium import webdriver


def random_sleep(min_time: int) -> None:
    """
        Fuzz wait times between [min_time, min_time*2]
    """
    time.sleep(min_time + min_time * random.random())


def fetch_google_image_urls(
    query: str,
    driver: WebDriver,
    sleep_between_interactions: int = 1,
    desired_count: int = 100,
) -> Set(str):
    """
        yield google image urls until desired_count is reached
        The find_elements_by_css_selector approach for interacting with the page feels a little bit brittle, it's possible these values could change.
    """

    random_sleep(sleep_between_interactions)

    def scroll_to_end(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_sleep(sleep_between_interactions)

    # build the google query
    search_url = f"https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={query}&oq={query}&gs_l=img"

    # load the page
    driver.get(search_url)
    random_sleep(sleep_between_interactions)

    image_links = set()
    results_start = 0
    while True:  # browse and download until we hit our target image count
        scroll_to_end(driver)

        # get all image thumbnail results
        thumbnail_results = driver.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        print(
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
            print(f"Found: {len(image_links)} image links, looking for more ...")
            random_sleep(sleep_between_interactions * 2)
            load_more_button = driver.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                driver.execute_script("document.querySelector('.mye4qd').click();")
                random_sleep(sleep_between_interactions)
            else:
                print(driver.page_source)
                print(
                    f"{image_count}/{desired_count} images gathered, but no 'load_more_button' found, returning what we have so far"
                )
                return image_links

        # move the result startpoint further down
        results_start = len(thumbnail_results)
