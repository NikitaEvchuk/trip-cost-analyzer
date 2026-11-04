# Agent.md — System Specification & Developer Guidelines
# Project: Student Holiday Trip Cost Analyzer (Warsaw vs. Utrecht)

## 1. Project Overview & Vision
Проект представляет собой сквозной пайплайн аналитики данных для персонального использования. Система решает прикладную задачу: обоснованный выбор города для новогодней поездки компании студентов/молодежи на основе комплексного финансового анализа.

Анализируются не только расходы на жилье (Booking / Airbnb), но и структура ежедневных трат:
- Ночная жизнь и бары (цена пинты пива, шотов, вход в клубы).
- Стритфуд и базовый общепит (дёнер/шаурма, комбо-обед, кофе).
- Городской транспорт (суточный/многодневный проездной, такси ночью).
- Культурные и развлекательные локации (катки, музеи со студенческой скидкой).

---

## 2. End-to-End Architecture & Data Flow

```
Open sources / Excel  ->  Python (pandas) extract  ->  BigQuery `raw`  ->  dbt (staging -> intermediate -> marts)  ->  Power BI
```

| Layer | Tool | Responsibility |
|---|---|---|
| Manual input | Excel (`data/manual/*.xlsx`) | Prices not available in open data (beer, kebab, coffee, club entry, transport tickets, accommodation offers). Every row MUST have `source_url` and `collected_at`. |
| Extract | Python 3.11, pandas, requests | Pull open APIs, light cleaning, write to `data/raw/` and load to BigQuery via `pandas-gbq`. |
| Raw | BigQuery dataset `raw` (Sandbox) | Data as-is + `_loaded_at` column. No business logic. |
| Transform | dbt Core + `dbt-bigquery` (fallback: `dbt-duckdb`) | Cleaning, currency conversion to EUR, unit costs per component, data tests. |
| Serve | Power BI Desktop | What-if parameters, DAX for per-person math, scenario comparison. |

### 2.1 Data Sources (open only, no scraping of sites that forbid it)
| Domain | Source | Notes |
|---|---|---|
| Accommodation | Manual Excel (offers from Booking/Airbnb collected by hand for the trip dates) | Inside Airbnb has NO Utrecht/Warsaw. Amsterdam/Rotterdam/The Hague may be used only as an NL benchmark. |
| POIs (bars, clubs, fast food, cafes, ice rinks, museums) | OpenStreetMap Overpass API | Send a descriptive `User-Agent`; respect rate limits; cache results. |
| Daily prices | Manual Excel `manual_prices.xlsx` | min / typical / max per item per city. |
| Price level sanity check | Eurostat API `prc_ppp_ind` | Country level (PL vs NL). |
| Transport tariffs | Official ZTM Warszawa / U-OV & NS tariffs -> Excel | Static. |
| FX rates | Frankfurter (ECB) + NBP API | ECB has no UAH -> use NBP table A for UAH. Default currency: EUR. |
| Weather (optional) | Open-Meteo Historical API | Late-December climate. |
| Travel to city | Not modelled by default; optional manual Excel row | — |

### 2.2 Parameters (changeable in Power BI, defaults in `trip_config` seed)
- Group size (default 5, range 1–12)
- Check-in / check-out dates -> number of nights (default 29.12 -> 02.01)
- Display currency (default EUR)
- Spending profile: `budget` / `medium` / `party`
- Accommodation type: entire apartment / hostel
- Nights out count

### 2.3 Cost Model (per person)
```
total = accommodation_per_night * nights / group_size
      + days * (food + transport)
      + nights_out * nightlife_basket
      + activities
      + nye_premium
```
dbt computes **unit costs** per component; Power BI (DAX) does group-size / nights math so parameters stay interactive.

---

## 3. Repository Layout
```
extract/      Python extract & load scripts
data/manual/  Excel inputs (versioned)
data/raw/     Downloaded files (git-ignored)
dbt_trip/     dbt project (models/staging|intermediate|marts, seeds, tests)
notebooks/    EDA
powerbi/      .pbix report
```

---

## 4. Developer Guidelines
- Portfolio project: code, comments, README and commit messages in **English**.
- No secrets in git: use `.env` (see `.env.example`); GCP key files are git-ignored.
- Only open/sanctioned data sources; never scrape Booking, Airbnb or Google Maps.
- Every manual price row needs a source and a collection date.
- dbt naming: `stg_<source>__<entity>`, `int_<desc>`, `dim_*`, `fct_*`, `mart_*`.
- Every mart model has at least `not_null` + `unique` tests on its key.
- Prices stored in local currency in raw; converted to EUR in `int_prices_in_eur`.