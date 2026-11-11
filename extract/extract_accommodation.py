import requests
import pandas as pd
import time
import os
import re
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    raise ValueError("RAPIDAPI_KEY not found in environment variables. Check .env file.")
RAPIDAPI_HOST = 'airbnb19.p.rapidapi.com'

headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST
}

def search_airbnb(city_query, city_name, checkin="2026-12-29", checkout="2027-01-02", adults=2):
    url = "https://airbnb19.p.rapidapi.com/api/v2/searchPropertyByLocation"

    querystring = {
        "query": city_query,
        "adults": str(adults),
        "checkin": checkin,
        "checkout": checkout,
        "currency": "EUR"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        print(f"Error API ({response.status_code}):", response.text)
        return pd.DataFrame()
    data = response.json()
    items = data.get("data",{}).get("list", [])


    results = []
    for item in items:
        price_info = item.get("structuredDisplayPrice", {}).get("primaryLine", {})
        raw_price = price_info.get("price") or price_info.get("discountedPrice") or price_info.get("originalPrice") or ""

        price_clean = None
        if raw_price:
            match = re.search(r"[\d\.]+", raw_price.replace(",", "."))
            if match:
                price_clean = float(match.group())

        raw_rating = item.get("avgRatingLocalized", "")
        rating_match = re.search(r"(\d+\.?\d*)", str(raw_rating))
        rating = float(rating_match.group()) if rating_match else None



        results.append({
            "city": city_name,
            "property_id": item.get("propertyId"),
            "title": item.get("title"),
            "subtitle": item.get("subtitle"),
            "rating": rating,
            "guests": adults,
            "checkin": checkin,
            "checkout": checkout,
            "nights": 4,
            "price_eur": price_clean,
            "price_raw": raw_price
        })
    return pd.DataFrame(results)

df_warsaw = search_airbnb("Warsaw", "Warsaw", adults=2)

time.sleep(2)

df_utrecht = search_airbnb("Utrecht", "Utrecht", adults=2)


df_accomod = pd.concat([df_warsaw, df_utrecht], ignore_index=True)
os.makedirs("data/raw", exist_ok=True)
df_accomod.to_csv("data/raw/accommodation_raw.csv", index=False, encoding="utf-8")
print(df_accomod.head())