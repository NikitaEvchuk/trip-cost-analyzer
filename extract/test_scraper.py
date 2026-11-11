import pandas as pd
import requests
from bs4 import BeautifulSoup
import os


pd.set_option("display.expand_frame_repr", False)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", 1000)

TARGET_KEYWORDS = [
    "Domestic Beer",
    "Imported Beer",
    "Wine",
    "Meal at",
    "Cappuccino",
    "One-way Ticket",
    "Taxi 1km",
    "Taxi Start"
]

def scrape_city(city_name):
    url = f"https://www.numbeo.com/cost-of-living/in/{city_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", class_="data_wide_table")

    collected_data = []
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                item_name = cells[0].text.strip()
                price = cells[1].text.strip()
                for keyword in TARGET_KEYWORDS:
                    if keyword.lower() in item_name.lower():
                        collected_data.append({
                            "city": city_name ,
                            "category_keyword": keyword,
                            "item_name": item_name,
                            "price": price
                        })
                        break
    return pd.DataFrame(collected_data)

df_warsaw = scrape_city("Warsaw")
df_utrecht = scrape_city("Utrecht")

df_combined = pd.concat([df_warsaw, df_utrecht], ignore_index=True)

df_combined["price_clean"] = (
    df_combined["price"]
    .str.replace(",", ".", regex=False)
    .str.extract(r"(\d+\.?\d*)")[0]
    .astype(float)
)
df_combined["currency"] = df_combined["city"].apply(lambda c: "PLN" if c =="Warsaw" else "EUR")

fx_url = "https://api.frankfurter.app/latest?from=EUR&to=PLN"
fx_data = requests.get(fx_url).json()

eur_to_pln = fx_data["rates"]["PLN"]

def convert_to_eur(row, rate):
    if row["currency"] == "EUR":
        return row["price_clean"]
    elif row["currency"] == "PLN":
        return round(row["price_clean"] / rate, 2)
    return row["price_clean"]

df_combined["price_eur"] = df_combined.apply(convert_to_eur, rate = eur_to_pln, axis= 1)

print(df_combined[["city", "item_name", "price", "price_clean", "currency", "price_eur"]])

os.makedirs("data/raw", exist_ok=True)
df_combined.to_csv("data/raw/numbeo_prices.csv", index=False, encoding= "utf-8")





