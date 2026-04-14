from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

STAR_MAP = {
    "One": 1.0,
    "Two": 2.0,
    "Three": 3.0,
    "Four": 4.0,
    "Five": 5.0,
}


def _build_driver(headless: bool) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def _extract_rating(driver: webdriver.Chrome) -> float | None:
    try:
        rating_classes = driver.find_element(By.CSS_SELECTOR, "p.star-rating").get_attribute(
            "class"
        )
    except NoSuchElementException:
        return None

    for cls_name in rating_classes.split():
        if cls_name in STAR_MAP:
            return STAR_MAP[cls_name]
    return None


def _extract_description(driver: webdriver.Chrome) -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, "#product_description ~ p").text.strip()
    except NoSuchElementException:
        return ""


def scrape_books(
    base_url: str = "https://books.toscrape.com",
    max_books: int | None = None,
    headless: bool = True,
) -> list[dict[str, Any]]:
    """
    Scrape books.toscrape.com and return a list of dictionaries with:
    title, price, rating, description, url.
    """
    driver = _build_driver(headless=headless)
    wait = WebDriverWait(driver, 10)
    scraped: list[dict[str, Any]] = []

    page_url = base_url.rstrip("/") + "/"

    try:
        while page_url:
            driver.get(page_url)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.product_pod")))
            except TimeoutException:
                break

            next_page_url = None
            try:
                next_href = driver.find_element(By.CSS_SELECTOR, "li.next a").get_attribute("href")
                next_page_url = urljoin(driver.current_url, next_href)
            except NoSuchElementException:
                pass

            product_cards = driver.find_elements(By.CSS_SELECTOR, "article.product_pod h3 a")
            detail_urls = [urljoin(driver.current_url, card.get_attribute("href")) for card in product_cards]

            for detail_url in detail_urls:
                driver.get(detail_url)
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product_main h1")))
                except TimeoutException:
                    continue

                title = driver.find_element(By.CSS_SELECTOR, "div.product_main h1").text.strip()
                price = driver.find_element(By.CSS_SELECTOR, "p.price_color").text.strip()
                rating = _extract_rating(driver)
                description = _extract_description(driver)

                scraped.append(
                    {
                        "title": title,
                        "price": price,
                        "rating": rating,
                        "description": description,
                        "url": driver.current_url,
                    }
                )

                if max_books is not None and len(scraped) >= max_books:
                    return scraped

            page_url = next_page_url
    finally:
        driver.quit()

    return scraped
