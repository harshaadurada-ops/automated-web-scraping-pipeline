
import logging
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Project folders
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"

START_URL = "https://books.toscrape.com/"
REQUEST_DELAY = 1

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# Configure retries and HTTP headers
def create_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "EducationalWebScraper/1.0"
    })

    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True
    )

    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


# Download a webpage
def fetch_page(session, url):
    response = session.get(url, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


# Extract book information
def parse_books(soup, page_url):
    books = []

    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        price = card.select_one(".price_color")
        availability = card.select_one(".availability")
        rating_element = card.select_one(".star-rating")

        if not link or not price:
            continue

        title = link.get("title") or link.get_text(strip=True)
        price_text = price.get_text(strip=True)

        try:
            price_value = float(
                "".join(
                    char for char in price_text
                    if char.isdigit() or char == "."
                )
            )
        except ValueError:
            logging.warning("Skipping invalid price: %s", title)
            continue

        rating_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }

        rating = None
        if rating_element:
            for class_name in rating_element.get("class", []):
                if class_name in rating_map:
                    rating = rating_map[class_name]
                    break

        books.append({
            "title": title.strip(),
            "price_gbp": price_value,
            "rating": rating,
            "availability": (
                availability.get_text(" ", strip=True)
                if availability else "Unknown"
            ),
            "product_url": urljoin(page_url, link.get("href", "")),
            "source_page": page_url
        })

    return books


# Scrape every catalogue page
def scrape_catalogue():
    all_books = []
    visited_urls = set()
    current_url = START_URL

    with create_session() as session:
        while current_url:
            if current_url in visited_urls:
                break

            visited_urls.add(current_url)
            logging.info("Scraping %s", current_url)

            soup = fetch_page(session, current_url)
            books = parse_books(soup, current_url)

            if not books:
                raise RuntimeError(
                    f"No books found on {current_url}"
                )

            all_books.extend(books)
            logging.info("Books collected: %d", len(all_books))

            next_link = soup.select_one("li.next a")

            if next_link and next_link.get("href"):
                current_url = urljoin(
                    current_url,
                    next_link["href"]
                )
                time.sleep(REQUEST_DELAY)
            else:
                current_url = None

    return all_books


# Clean and validate data
def transform_data(records):
    df = pd.DataFrame(records)

    df["title"] = df["title"].astype("string").str.strip()
    df["price_gbp"] = pd.to_numeric(
        df["price_gbp"], errors="coerce"
    )
    df["rating"] = pd.to_numeric(
        df["rating"], errors="coerce"
    )

    df = df.dropna(subset=["title", "price_gbp"])
    df = df[df["title"] != ""]
    df = df[df["price_gbp"] >= 0]
    df = df.drop_duplicates(subset=["product_url"])

    if df.empty:
        raise RuntimeError("No valid records after cleaning")

    return df.reset_index(drop=True)


# Export CSV and JSON
def save_data(df):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        DATA_DIR / "books.csv",
        index=False,
        encoding="utf-8-sig"
    )

    df.to_json(
        DATA_DIR / "books.json",
        orient="records",
        indent=2,
        force_ascii=False
    )

    logging.info("CSV and JSON files created")


# Generate a statistics report
def generate_report(df):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = f"""
AUTOMATED WEB SCRAPING PIPELINE
================================

Source: {START_URL}
Total books: {len(df)}

PRICE ANALYSIS (GBP)
Average price: £{df['price_gbp'].mean():.2f}
Median price: £{df['price_gbp'].median():.2f}
Minimum price: £{df['price_gbp'].min():.2f}
Maximum price: £{df['price_gbp'].max():.2f}

RATING ANALYSIS
Average rating: {df['rating'].mean():.2f}
Rating distribution:
{df['rating'].value_counts().sort_index().to_string()}

DATA QUALITY
Missing titles: {df['title'].isna().sum()}
Missing prices: {df['price_gbp'].isna().sum()}
Duplicate URLs: {df['product_url'].duplicated().sum()}
"""

    report_path = REPORT_DIR / "summary_report.txt"
    report_path.write_text(report.strip() + "\n", encoding="utf-8")

    print(report)
    logging.info("Summary report created")


# Run the entire ETL pipeline
def main():
    logging.info("Starting pipeline")

    records = scrape_catalogue()
    logging.info("Raw records collected: %d", len(records))

    df = transform_data(records)
    save_data(df)
    generate_report(df)

    logging.info("Pipeline completed successfully")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError, ValueError) as error:
        logging.error("Pipeline failed: %s", error)
        raise SystemExit(1)
