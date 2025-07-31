# ai_generator.py
import cohere
import os

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client("JmNhbEWy3qQIYLeTWwVqZPPVH3xzteNzgBDUqm8y")

def generate_humanized_output(product_name, primary_keywords, secondary_keywords, scraped_data):
    descriptions = "\n".join(scraped_data["descriptions"][:5])
    how_to_use = "\n".join(scraped_data["how_to_use"][:2])
    ingredients = "\n".join(scraped_data["ingredients"][:2])
    upc = scraped_data["upc"] or "Not Found"
    max_usd = max(scraped_data["prices_usd"], default="N/A")
    min_usd = min(scraped_data["prices_usd"], default="N/A")
    max_cad = max(scraped_data["prices_cad"], default="N/A")
    min_cad = min(scraped_data["prices_cad"], default="N/A")

    prompt = f"""
You are a marketing copywriter. Write SEO optimized content for:

Product: {product_name}
Primary Keywords: {primary_keywords}
Secondary Keywords: {secondary_keywords}

Extracted Description Snippets: {descriptions}
How to Use Info: {how_to_use}
Ingredients Info: {ingredients}

Your output must include the following sections in **human-like tone**, undetectable as AI:

1. Meta title: Length 50–60 characters. Primary keyword at beginning.
2. Meta description: 120–160 chars, 1–2 primary keywords
3. Short Description: 2–4 sentences using primary & secondary keywords
4. Description: 300–350 words. Talk about product benefits, target problems, usage, key features.
5. How to use: from scraped data or generic instructions
6. Ingredients: Key ingredients, with note that full list is on packaging
7. UPC: {upc}
8. Highest & Lowest Price (USD): {max_usd} / {min_usd}
9. Highest & Lowest Price (CAD): {max_cad} / {min_cad}
"""

    response = co.chat(model="command-r-plus", message=prompt)
    return {
        "Meta Title": response.text.split("\n")[1],
        "Meta Description": response.text.split("\n")[3],
        "Short Description": response.text.split("\n")[5],
        "Description": "\n".join(response.text.split("\n")[7:12]),
        "How to Use": response.text.split("\n")[13],
        "Ingredients": response.text.split("\n")[15],
        "UPC": upc,
        "Highest Price (USD)": max_usd,
        "Lowest Price (USD)": min_usd,
        "Highest Price (CAD)": max_cad,
        "Lowest Price (CAD)": min_cad
    }
