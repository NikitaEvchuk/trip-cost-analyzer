"""Build the manual data-collection workbook (data/manual/manual_inputs.xlsx).

Usage:
    python scripts/build_manual_template.py           # refuses to overwrite existing file
    python scripts/build_manual_template.py --force   # overwrite (DESTROYS collected data)
"""
import argparse
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).resolve().parents[1] / "data" / "manual" / "manual_inputs.xlsx"
MAX_ROWS = 1000
FONT = "Arial"

HEADER_FILL = PatternFill("solid", start_color="1F3864")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")
BODY_FONT = Font(name=FONT)
INPUT_FONT = Font(name=FONT, color="0000FF")
TITLE_FONT = Font(name=FONT, bold=True, size=14)
H2_FONT = Font(name=FONT, bold=True, size=11, color="1F3864")
THIN = Side(style="thin", color="BFBFBF")

# Excel serial numbers for date validation range (2026-01-01 .. 2027-12-31)
DATE_MIN, DATE_MAX = 46023, 46752

LISTS = {
    "city": ["Warsaw", "Utrecht"],
    "currency": ["PLN", "EUR"],
    "price_type": ["regular", "happy_hour", "student", "nye"],
    "source_type": [
        "venue_website", "menu_photo_maps", "delivery_app", "ticket_platform",
        "official_tariff", "taxi_app_estimate", "in_person", "other",
    ],
    "platform": ["booking", "airbnb", "hostelworld", "other"],
    "property_type": ["entire_apartment", "hostel_dorm_bed", "hostel_private_room", "hotel_room"],
    "yes_no": ["yes", "no", "unknown"],
    "category": ["nightlife", "food", "transport", "activities"],
    "basis": ["per_day", "per_night_out", "per_trip"],
    "spending_profile": ["budget", "medium", "party"],
}

# item_code, category, item_name, standard size / definition, target samples per city
ITEMS = [
    ("beer_bar", "nightlife", "Draft beer in a bar", "Local lager; record actual volume in volume_ml (NL often 250 ml!)", 5),
    ("beer_shop", "nightlife", "Beer in supermarket", "0.5 l can of a mainstream local brand", 3),
    ("shot_bar", "nightlife", "Shot in a bar", "Standard vodka/house shot; record volume_ml (PL 40-50 ml, NL 20-35 ml)", 4),
    ("cocktail_bar", "nightlife", "Basic cocktail in a bar", "Simple mix (e.g. rum-cola, gin-tonic, aperol)", 3),
    ("club_entry_regular", "nightlife", "Club entry, regular weekend", "Entry ticket on a normal Fri/Sat", 4),
    ("club_entry_nye", "nightlife", "New Year's Eve party ticket", "31 Dec party ticket (club / event)", 4),
    ("kebab", "food", "Doner / kebab / shawarma", "Standard wrap or pita, not XXL", 5),
    ("fastfood_combo", "food", "McDonald's Big Mac meal", "Medium menu; standardised benchmark", 1),
    ("lunch_casual", "food", "Casual sit-down main dish", "Budget restaurant main course or lunch menu", 4),
    ("coffee_cappuccino", "food", "Cappuccino in a cafe", "Regular size, chain or local cafe", 4),
    ("ticket_single", "transport", "Public transport single ticket", "Shortest standard single ride in city zone", 1),
    ("ticket_24h", "transport", "Public transport 24h ticket", "City zone", 1),
    ("ticket_72h", "transport", "Public transport 72h / multi-day ticket", "City zone; note if weekend ticket", 1),
    ("taxi_night_5km", "transport", "Night taxi ride ~5 km", "Bolt/Uber estimate around 01:00-03:00, centre -> residential", 3),
    ("airport_transfer", "transport", "Airport -> city centre", "Cheapest public option (train/bus), one way", 2),
    ("ice_rink_entry", "activities", "Ice rink entry", "Seasonal / city rink, student price if any", 3),
    ("skate_rental", "activities", "Skate rental", "Per session", 3),
    ("museum_student", "activities", "Museum entry, student", "Popular museum, student ticket", 3),
]

PRICE_COLS = [
    ("city", 12, "Dropdown: Warsaw / Utrecht"),
    ("item_code", 20, "Dropdown: code from 'items' sheet. Read its definition before collecting!"),
    ("venue_name", 28, "Bar / shop / cafe / operator name"),
    ("district", 16, "Neighbourhood (e.g. Srodmiescie, Binnenstad). Optional but useful."),
    ("price_local", 12, "Price as shown, in local currency. Number only, no symbol."),
    ("currency", 10, "Dropdown: PLN for Warsaw, EUR for Utrecht"),
    ("volume_ml", 11, "Drinks only: actual serving size in ml (250, 330, 500, 40...)"),
    ("price_type", 13, "regular / happy_hour / student / nye"),
    ("source_type", 18, "Where the price came from (dropdown)"),
    ("source_url", 40, "Link to menu / page / photo. Required unless in_person."),
    ("price_date", 13, "Date the price is valid for / menu date if known (YYYY-MM-DD). Optional."),
    ("collected_at", 13, "Date YOU recorded the row (YYYY-MM-DD). Required."),
    ("collected_by", 13, "Your name / initials"),
    ("notes", 40, "Anything unusual: 'price from 2025 menu', 'delivery app +20%', etc."),
]

ACC_COLS = [
    ("city", 12, "Dropdown: Warsaw / Utrecht"),
    ("platform", 13, "booking / airbnb / hostelworld / other"),
    ("property_type", 20, "entire_apartment / hostel_dorm_bed / hostel_private_room / hotel_room"),
    ("listing_name", 30, "Name as shown on the platform"),
    ("district", 16, "Neighbourhood"),
    ("distance_center_km", 12, "Distance to city centre as shown on platform"),
    ("guests_searched", 12, "Number of guests entered in the search filter"),
    ("max_guests", 11, "Maximum guests the listing allows"),
    ("bedrooms", 10, "Number of bedrooms"),
    ("beds", 8, "Number of beds (sofa bed counts)"),
    ("check_in", 12, "YYYY-MM-DD"),
    ("check_out", 12, "YYYY-MM-DD"),
    ("total_price_local", 14, "FINAL total for the whole stay incl. cleaning & service fees. For dorms: price per ONE bed for whole stay."),
    ("currency", 10, "PLN / EUR"),
    ("taxes_fees_included", 12, "Does total include city tax and all fees? yes / no / unknown"),
    ("rating", 8, "Rating as shown (Booking 0-10, Airbnb 0-5)"),
    ("reviews_count", 10, "Number of reviews"),
    ("free_cancellation", 12, "yes / no"),
    ("search_rank", 10, "Position in the sorted result list (1, 2, 3...) - proves no cherry-picking"),
    ("listing_url", 40, "Link to listing"),
    ("collected_at", 13, "Date YOU recorded the row (YYYY-MM-DD)"),
    ("collected_by", 13, "Your name / initials"),
    ("notes", 40, "e.g. 'min stay 5 nights', 'party not allowed', 'far from metro'"),
]

CONFIG = [
    ("group_size", 5, "Default number of people (changeable in Power BI)"),
    ("check_in", "2026-12-29", "Default check-in date"),
    ("check_out", "2027-01-02", "Default check-out date"),
    ("default_currency", "EUR", "Reporting currency"),
    ("spending_profile", "medium", "budget / medium / party"),
    ("accommodation_type", "entire_apartment", "Default accommodation type"),
    ("nights_out", 3, "Nights going out (bars/clubs) incl. NYE"),
    ("nye_in_trip", "yes", "Does the trip include 31 December?"),
]

# profile, item_code, quantity, basis  (assumptions - edit freely)
PROFILES = []
_base = {
    "beer_bar": ("per_night_out", 2, 4, 6),
    "shot_bar": ("per_night_out", 1, 2, 4),
    "cocktail_bar": ("per_night_out", 0, 1, 2),
    "beer_shop": ("per_night_out", 2, 3, 4),
    "club_entry_regular": ("per_night_out", 0, 0.5, 1),
    "club_entry_nye": ("per_trip", 0, 1, 1),
    "kebab": ("per_day", 1, 1, 1),
    "lunch_casual": ("per_day", 0, 0.5, 1),
    "fastfood_combo": ("per_day", 0.5, 0.5, 0.5),
    "coffee_cappuccino": ("per_day", 1, 1, 2),
    "ticket_24h": ("per_day", 1, 1, 1),
    "taxi_night_5km": ("per_night_out", 0, 0.2, 0.25),
    "airport_transfer": ("per_trip", 2, 2, 2),
    "ice_rink_entry": ("per_trip", 1, 1, 1),
    "skate_rental": ("per_trip", 1, 1, 1),
    "museum_student": ("per_trip", 1, 1, 0),
}
for _code, (_basis, b, m, p) in _base.items():
    for _prof, _q in (("budget", b), ("medium", m), ("party", p)):
        PROFILES.append((_prof, _code, _q, _basis))


def style_header(ws, cols):
    for i, (name, width, note) in enumerate(cols, start=1):
        c = ws.cell(row=1, column=i, value=name)
        c.font, c.fill = HEADER_FONT, HEADER_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(bottom=THIN)
        c.comment = Comment(note, "template")
        ws.column_dimensions[c.column_letter].width = width
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(cols)).column_letter}1"


def col_letter(cols, name):
    from openpyxl.utils import get_column_letter
    return get_column_letter([c[0] for c in cols].index(name) + 1)


def add_list_dv(ws, cols, name, source):
    dv = DataValidation(type="list", formula1=source, allow_blank=True, showErrorMessage=True,
                        errorTitle="Invalid value", error="Pick a value from the dropdown list.")
    L = col_letter(cols, name)
    dv.add(f"{L}2:{L}{MAX_ROWS}")
    ws.add_data_validation(dv)


def add_number_dv(ws, cols, name, kind="decimal", minimum=0):
    dv = DataValidation(type=kind, operator="greaterThanOrEqual", formula1=str(minimum), allow_blank=True,
                        showErrorMessage=True, errorTitle="Invalid number", error=f"Enter a number >= {minimum}.")
    L = col_letter(cols, name)
    dv.add(f"{L}2:{L}{MAX_ROWS}")
    ws.add_data_validation(dv)


def add_date_dv(ws, cols, name):
    dv = DataValidation(type="date", operator="between", formula1=str(DATE_MIN), formula2=str(DATE_MAX),
                        allow_blank=True, showErrorMessage=True, errorTitle="Invalid date",
                        error="Enter a date as YYYY-MM-DD (2026-2027).")
    L = col_letter(cols, name)
    dv.add(f"{L}2:{L}{MAX_ROWS}")
    ws.add_data_validation(dv)
    for r in range(2, MAX_ROWS + 1):
        ws[f"{L}{r}"].number_format = "yyyy-mm-dd"


def list_ref(key):
    keys = list(LISTS)
    from openpyxl.utils import get_column_letter
    L = get_column_letter(keys.index(key) + 1)
    return f"=lists!${L}$2:${L}${len(LISTS[key]) + 1}"


def build():
    wb = Workbook()

    # README
    ws = wb.active
    ws.title = "README"
    ws.column_dimensions["A"].width = 120
    lines = [
        ("Manual data collection - Warsaw vs Utrecht", TITLE_FONT),
        ("", None),
        ("Sheets", H2_FONT),
        ("prices         - one row = one observed price of one item in one venue (fill this)", None),
        ("accommodation  - one row = one listing offer for the trip dates (fill this)", None),
        ("items          - catalogue of what to collect + definitions + target number of samples (read)", None),
        ("trip_config    - default trip parameters (edit values in blue if needed)", None),
        ("spending_profiles - how many of each item a person consumes per profile (assumptions, edit in blue)", None),
        ("lists          - dropdown values (do not edit unless adding a new option)", None),
        ("", None),
        ("Rules", H2_FONT),
        ("1. One observation per row. Never put two prices in one cell, never merge cells, never add subtotal rows.", None),
        ("2. Use the dropdowns. Free-text variants ('warsaw', 'Warszawa') break the pipeline.", None),
        ("3. Prices: number only, in local currency, exactly as shown (no conversion). PLN for Warsaw, EUR for Utrecht.", None),
        ("4. Every row needs source_url (or source_type = in_person) and collected_at.", None),
        ("5. Drinks: always fill volume_ml - Dutch beers are often 250 ml, Polish 500 ml.", None),
        ("6. Accommodation: total_price_local = FINAL price for the whole stay incl. all fees. Note search_rank.", None),
        ("7. Do not delete 'odd' prices - keep them and explain in notes. Outliers are handled in the pipeline.", None),
        ("8. Do not add or rename columns. If something is missing, write it in notes.", None),
        ("", None),
        ("Example rows (do NOT copy into data sheets)", H2_FONT),
        ("prices:  Warsaw | beer_bar | Pub XYZ | Srodmiescie | 18 | PLN | 500 | regular | venue_website | https://... | | 2026-11-05 | NK | ", None),
        ("prices:  Utrecht | beer_bar | Cafe ABC | Binnenstad | 3.9 | EUR | 250 | regular | menu_photo_maps | https://maps... | | 2026-11-05 | NK | menu photo from Oct 2026", None),
        ("accommodation: Utrecht | airbnb | entire_apartment | Cozy loft | Lombok | 1.8 | 6 | 6 | 2 | 4 | 2026-12-29 | 2027-01-02 | 1240 | EUR | yes | 4.85 | 112 | no | 3 | https://... | 2026-11-05 | NK |", None),
    ]
    for i, (text, font) in enumerate(lines, start=1):
        c = ws.cell(row=i, column=1, value=text)
        c.font = font or BODY_FONT

    # prices
    ws = wb.create_sheet("prices")
    style_header(ws, PRICE_COLS)
    add_list_dv(ws, PRICE_COLS, "city", list_ref("city"))
    add_list_dv(ws, PRICE_COLS, "item_code", f"=items!$A$2:$A${len(ITEMS) + 1}")
    add_list_dv(ws, PRICE_COLS, "currency", list_ref("currency"))
    add_list_dv(ws, PRICE_COLS, "price_type", list_ref("price_type"))
    add_list_dv(ws, PRICE_COLS, "source_type", list_ref("source_type"))
    add_number_dv(ws, PRICE_COLS, "price_local")
    add_number_dv(ws, PRICE_COLS, "volume_ml", "whole", 1)
    add_date_dv(ws, PRICE_COLS, "price_date")
    add_date_dv(ws, PRICE_COLS, "collected_at")

    # accommodation
    ws = wb.create_sheet("accommodation")
    style_header(ws, ACC_COLS)
    add_list_dv(ws, ACC_COLS, "city", list_ref("city"))
    add_list_dv(ws, ACC_COLS, "platform", list_ref("platform"))
    add_list_dv(ws, ACC_COLS, "property_type", list_ref("property_type"))
    add_list_dv(ws, ACC_COLS, "currency", list_ref("currency"))
    add_list_dv(ws, ACC_COLS, "taxes_fees_included", list_ref("yes_no"))
    add_list_dv(ws, ACC_COLS, "free_cancellation", list_ref("yes_no"))
    for n in ("distance_center_km", "total_price_local", "rating"):
        add_number_dv(ws, ACC_COLS, n)
    for n in ("guests_searched", "max_guests", "bedrooms", "beds", "reviews_count", "search_rank"):
        add_number_dv(ws, ACC_COLS, n, "whole", 0)
    for n in ("check_in", "check_out", "collected_at"):
        add_date_dv(ws, ACC_COLS, n)

    # items
    ws = wb.create_sheet("items")
    item_cols = [("item_code", 20, ""), ("category", 12, ""), ("item_name", 34, ""),
                 ("definition", 70, ""), ("target_samples_per_city", 14, "")]
    style_header(ws, item_cols)
    for row in ITEMS:
        ws.append(row)

    # trip_config
    ws = wb.create_sheet("trip_config")
    style_header(ws, [("parameter", 22, ""), ("value", 18, "Edit values in blue"), ("description", 60, "")])
    for p, v, d in CONFIG:
        ws.append([p, v, d])
        ws.cell(row=ws.max_row, column=2).font = INPUT_FONT

    # spending_profiles
    ws = wb.create_sheet("spending_profiles")
    prof_cols = [("spending_profile", 16, ""), ("item_code", 20, ""),
                 ("quantity", 10, "Units per basis period. Edit freely (blue = assumption)."), ("basis", 14, "")]
    style_header(ws, prof_cols)
    for row in PROFILES:
        ws.append(row)
        ws.cell(row=ws.max_row, column=3).font = INPUT_FONT
    add_list_dv(ws, prof_cols, "spending_profile", list_ref("spending_profile"))
    add_list_dv(ws, prof_cols, "item_code", f"=items!$A$2:$A${len(ITEMS) + 1}")
    add_list_dv(ws, prof_cols, "basis", list_ref("basis"))

    # lists
    ws = wb.create_sheet("lists")
    style_header(ws, [(k, 18, "") for k in LISTS])
    for j, vals in enumerate(LISTS.values(), start=1):
        for i, v in enumerate(vals, start=2):
            ws.cell(row=i, column=j, value=v)

    for sheet in wb.worksheets:
        for row in sheet.iter_rows(min_row=2):
            for c in row:
                if c.font is None or c.font.name != FONT:
                    c.font = Font(name=FONT, color=c.font.color if c.font else None)
    for name in ("prices", "accommodation"):
        wb[name].sheet_properties.tabColor = "70AD47"

    wb.active = 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if OUT.exists() and not args.force:
        sys.exit(f"{OUT} already exists. Use --force to overwrite (collected data will be lost).")
    build()
    print(f"Created {OUT}")
