from selenium import webdriver
import time
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from pathlib import Path


def main():
    path = str(Path(__file__).parent.joinpath("cookies-consent.html").resolve())
    print(path)

    driver = webdriver.Firefox()

    try:
        file_name = "file://" + path
        driver.get(file_name)
        button = driver.find_element(By.XPATH, "//button[@jsname = 'b3VHJd']")
        button.click()
        time.sleep(5)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
