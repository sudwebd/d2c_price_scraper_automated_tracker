import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import time
import logging
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)

SCROLL_PAUSE_TIME = 5
PAGE_LOAD_TIMEOUT = 10

def _scroll_to_load_content(driver):
    """
    Scrolls the webpage to load all dynamic content.
    """
    height_js = "return document.body.scrollHeight"
    scroll_js = "window.scrollTo(0, document.body.scrollHeight);"
    current_height = driver.execute_script(height_js)
    while True:
        driver.execute_script(scroll_js)
        time.sleep(SCROLL_PAUSE_TIME)
        driver.execute_script("window.scrollBy(0, -300);")
        driver.execute_script(scroll_js)
        new_height = driver.execute_script(height_js)
        if new_height == current_height:
            break
        current_height = new_height
    logging.info("Page loaded successfully")

def _process_sneakers(driver):
    """
    Processes the sneaker elements on the webpage and extracts relevant information.
    """
    sneakers = []
    try:
        _scroll_to_load_content(driver)
        sneaker_elements = driver.find_elements(By.CSS_SELECTOR, "div.pro-list div.animate-card:not(.flex-column) div.productCard")
        logging.info(f"Found {len(sneaker_elements)} sneakers")
        for element in sneaker_elements:
            sneaker_element = element.find_element(By.CSS_SELECTOR, "a > div:not(.imgBlock)")
            current_price = re.sub(r'[^\d.]', '', sneaker_element.find_element(By.CSS_SELECTOR, "span.offer.fsemibold").text)
            sneaker = {
                "name": sneaker_element.find_element(By.CSS_SELECTOR, "div:nth-of-type(1) h5").text,
                "category": sneaker_element.find_element(By.CSS_SELECTOR, "div.listprice.ecltext span").text,
                "current_price": current_price,
                "original_price": current_price,
                "in_stock": "No" if len(element.find_elements(By.CSS_SELECTOR, "a > div.imgBlock > div.souled-out-image-blur")) > 0 else "Yes"
            }
            sneakers.append(sneaker)
            try:
                original_price = re.sub(r'[^\d.]', '', sneaker_element.find_element(By.CSS_SELECTOR, "span.product-price").text)
                sneakers[-1]["original_price"] = original_price
            except NoSuchElementException:
                pass
        logging.info("Scraped sneakers data:\n%s", json.dumps(sneakers, indent=2))
    except NoSuchElementException as e:
        logging.error(f"Element not found: {e}")
    except WebDriverException as e:
        logging.error(f"WebDriver error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return sneakers

def _initialize_driver():
    """
    Initializes the Chrome driver with the specified options.
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver

def process_page(url):
    """
    Loads the webpage and processes the sneaker data.
    """
    try:
        driver = _initialize_driver()
        driver.get(url)
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return _process_sneakers(driver)
    except TimeoutException as e:
        logging.error(f"Page load timeout: {e}")
    except WebDriverException as e:
        logging.error(f"WebDriver error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()
    return []