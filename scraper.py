# scraper.py
import asyncio
from playwright.sync_api import sync_playwright
from utils import clean_html
import re

def scrape_product_data(product_name, primary_keywords, secondary_keywords):
    query = f"{product_name} {' '.join(primary_keywords.split(','))} {' '.join(secondary_keywords.split(','))}"
    urls = []
    data = {
        "descriptions": [],
        "ingredients": [],
        "how_to_use": [],
        "upc": None,
        "prices_usd": [],
        "prices_cad": [],
    }

    def extract_prices(text):
        usd = re.findall(r'\$\d+(?:\.\d{2})?', text)
        cad = re.findall(r'CAD\s*\$\d+(?:\.\d{2})?', text)
        return usd, cad

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.google.com/search?q={query}")

        links = page.locator("a:visible")
        for i in range(min(10, links.count())):
            href = links.nth(i).get_attribute("href")
            if href and href.startswith("http") and "google.com" not in href:
                urls.append(href)

        for url in urls:
            try:
                page.goto(url, timeout=10000)
                content = page.content()
                cleaned = clean_html(content)
                data["descriptions"].append(cleaned)
                if "ingredients" in cleaned.lower():
                    data["ingredients"].append(cleaned)
                if "how to use" in cleaned.lower():
                    data["how_to_use"].append(cleaned)
                if "upc" in cleaned.lower() and not data["upc"]:
                    match = re.search(r'UPC[:\s]*([0-9]{8,14})', cleaned)
                    if match:
                        data["upc"] = match.group(1)

                usd, cad = extract_prices(cleaned)
                data["prices_usd"].extend(usd)
                data["prices_cad"].extend(cad)
            except Exception as e:
                print("Error scraping", url, e)
                continue
        browser.close()

    return data
