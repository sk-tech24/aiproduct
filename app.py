# app.py
import streamlit as st
from scraper import scrape_product_data
from ai_generator import generate_humanized_output
import os
# 🚀 Setup
os.system("playwright install")

st.set_page_config(page_title="AI Product SEO Generator", layout="wide")

st.title("🧠 AI Product SEO Generator")

product_name = st.text_input("Product Name", placeholder="e.g. Fanola No Yellow Shampoo 350 ml")
primary_keywords = st.text_input("Primary Keywords (comma-separated)", placeholder="e.g. shampoo, violet shampoo")
secondary_keywords = st.text_input("Secondary Keywords (comma-separated)", placeholder="e.g. hair care, colored hair care")

if st.button("Generate SEO Content"):
    with st.spinner("🔍 Searching and scraping Google..."):
        scraped_data = scrape_product_data(product_name, primary_keywords, secondary_keywords)
        st.success("✅ Scraping complete")

    with st.spinner("🧠 Generating AI content..."):
        seo_output = generate_humanized_output(product_name, primary_keywords, secondary_keywords, scraped_data)
        st.success("✅ Content generated!")

    st.subheader("📌 Final SEO Output")
    for key, value in seo_output.items():
        st.markdown(f"### {key}")
        st.write(value)
