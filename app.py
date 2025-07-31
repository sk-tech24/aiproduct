# 📦 Streamlit Product Info Scraper App (SEO-Optimized + Humanized)

import streamlit as st
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import os
import cohere
import re
import aiohttp
import requests
from datasets import Dataset, load_dataset, concatenate_datasets
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# 🚀 Setup
os.system("playwright install")

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)
HF_DATASET_NAME = "Jay-Rajput/product_desc"

# 🔍 Google Search
async def search_product_links(query, max_links=5):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"https://www.google.com/search?q={query}")
        await page.wait_for_timeout(2000)
        elements = await page.query_selector_all("a")
        links = []
        for e in elements:
            href = await e.get_attribute("href")
            if href and href.startswith("/url?q="):
                clean_link = href.split("/url?q=")[1].split("&")[0]
                if ("google" not in clean_link and not clean_link.startswith("#") and
                    not any(domain in clean_link for domain in ["youtube.com", "facebook.com", "instagram.com"])):
                    links.append(clean_link)
            if len(links) >= max_links:
                break
        await browser.close()
        return links

# 🕷️ Scraper
async def extract_product_info(session, url):
    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as response:
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            title = soup.title.text.strip() if soup.title else ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            short_desc = meta_desc['content'] if meta_desc else ""
            paragraphs = soup.find_all("p")
            body_text = " ".join([p.text.strip() for p in paragraphs[:15] if len(p.text.strip()) > 30])

            keywords = ["price", "buy", "add to cart", "mrp", "product", "brand", "description"]
            combined_text = f"{title.lower()} {short_desc.lower()} {body_text.lower()}"
            keyword_matches = sum(1 for word in keywords if word in combined_text)

            if keyword_matches < 2 or len(body_text) < 100:
                return {"url": url, "error": "Page doesn't appear to be a product page."}

            return {
                "url": url,
                "title": title,
                "short_desc": short_desc,
                "long_desc": body_text
            }
    except Exception as e:
        return {"url": url, "error": str(e)}

# 🧠 Generate SEO-Friendly Description
async def generate_aggregated_description(product_name, descriptions):
    combined_texts = "\n\n".join([f"Source {i+1}: {desc}" for i, desc in enumerate(descriptions)])
    prompt = f"""
    Use the dependency grammar linguistic framework rather than phrase structure grammar to craft a product description. The idea is that the closer together each pair of words you're connecting is, the easier the copy will be to comprehend. Here is the topic and additional details: 
    Based on the following descriptions for "{product_name}", generate one product description.

    Strictly follow this format:

    ### Short Description:
    [A concise overview in 2-3 sentences]

    ### Description:
    [Combine all key features and conclusion into this section. Avoid adding any headers inside.]

    ### How to Use:
    [Step-by-step usage instructions]

    Guidelines:
    - Do NOT use any extra headers like 'Key Features' or 'Conclusion'
    - Use markdown formatting exactly as shown
    - Avoid repetition

    Descriptions from sources:
    {combined_texts}
    """
    try:
        response = co.chat(model="command-r-plus-08-2024", message=prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def build_humanizer_prompt(ai_description):
    return f"""
    
    Rewrite the following product description so it looks and feels truly written by a human copywriter, while keeping the exact format:

### Short Description:
[ ... 2–3 lines summary ...]

### Description:
[ ... key features and details, single block ... ]

### How to Use:
[ ... step-by-step usage instructions ... ]

Your rewrite must:
1. Preserve all headings and their order.
2. Use varied sentence lengths and rhythm: mix short punchy lines with longer ones.
3. Avoid cliché marketing phrases (“Get ready for...”, “This isn’t your average…”, etc.).
4. Inject subtle, natural imperfections: mild colloquialisms (“a bit”, “kind of”), contractions (“you’ll”, “it’s”), and even occasional minor typos or slight grammatical quirks.
5. Include a rhetorical question or two (e.g., “Want fuller hair?”, “Need something easy?”) — humans often use them casually.
6. Use grounded, specific detail — not vague superlatives.
7. Avoid repeating keywords or terms in close proximity.
8. Add tiny personal touches or relatable imagery — but don’t turn it into a story or blog post.
9. Don’t over‑optimize for SEO; write for humans, not machines.
10. Maintain clarity and professionalism — readable, easy to skim.

Here’s the original description:

[PASTE AI‑GENERATED PRODUCT DESCRIPTION HERE]

    {ai_description}
    """

# 🤖 Humanize AI Output
def humanize_text_with_gemini(text):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt_text = build_humanizer_prompt(text)
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"[ERROR]: {str(e)}"
    
# 💾 Save to HF Dataset
def save_to_huggingface_dataset(product_name, description):
    new_data = Dataset.from_dict({
        "product_name": [product_name],
        "description": [description]
    })
    try:
        existing = load_dataset(HF_DATASET_NAME, split="train")
        combined = concatenate_datasets([existing, new_data])
    except:
        combined = new_data

    combined.push_to_hub(HF_DATASET_NAME, split="train", private=False)

# 🚀 Streamlit UI
st.set_page_config(page_title="ProductSense", page_icon="🛍️", layout="wide")
st.title("🛍️ ProductSense: AI-Powered Product Descriptions")
st.markdown("Enter a product name to scrape the web and generate a description.")

if "submitted" not in st.session_state:
    st.session_state.submitted = False

with st.form("product_form"):
    product_name = st.text_input("Enter product name (e.g., Sebastian Volupt Shampoo 250ml):")
    submitted = st.form_submit_button("Generate Description")

if submitted and product_name:
    st.session_state.submitted = True
    st.session_state.product_name = product_name
elif submitted and not product_name:
    st.warning("Please enter a product name.")
    st.session_state.submitted = False

if st.session_state.submitted and product_name:
    async def run():
        with st.spinner("Searching and scraping..."):
            urls = await search_product_links(product_name, max_links=10)
            print(urls)
            descriptions = []
            metadata = []
            async with aiohttp.ClientSession() as session:
                scrape_tasks = [extract_product_info(session, url) for url in urls]
                scraped_data = await asyncio.gather(*scrape_tasks)
                for raw in scraped_data:
                    if 'error' not in raw:
                        descriptions.append(raw['long_desc'])
                        metadata.append(raw)
                    else:
                        metadata.append(raw)

            ai_summary = await generate_aggregated_description(product_name, descriptions)
            human_like_summary = humanize_text_with_gemini(ai_summary)
            save_to_huggingface_dataset(product_name, human_like_summary)
            return human_like_summary, metadata

    summary, sources = asyncio.run(run())
    st.subheader("📝 Final Product Description")
    st.write(summary)
    st.session_state.submitted = False
