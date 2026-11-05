"""Validate data/manual/manual_inputs.xlsx.

Checks required fields, valid values, data types, and logic.
Run:
    python scripts/validate_manual_inputs.py
"""
import sys
from pathlib import Path
import pandas as pd

FILE_PATH = Path(__file__).resolve().parents[1] / "data" / "manual" / "manual_inputs.xlsx"

def validate():
    if not FILE_PATH.exists():
        print(f"[ERROR] File not found: {FILE_PATH}")
        sys.exit(1)

    xl = pd.ExcelFile(FILE_PATH)
    errors = []
    warnings = []

    # Check accommodation
    if "accommodation" in xl.sheet_names:
        df_acc = pd.read_excel(xl, "accommodation")
        print(f"Checking 'accommodation' ({len(df_acc)} rows)...")
        for idx, row in df_acc.iterrows():
            r_num = idx + 2
            # Required checks
            for col in ["city", "platform", "property_type", "total_price_local", "currency", "check_in", "check_out"]:
                if pd.isna(row.get(col)):
                    errors.append(f"accommodation row {r_num}: missing required field '{col}'")

            # Numeric checks
            if pd.notna(row.get("total_price_local")):
                try:
                    val = float(row["total_price_local"])
                    if val <= 0:
                        errors.append(f"accommodation row {r_num}: total_price_local must be > 0 (got {val})")
                except ValueError:
                    errors.append(f"accommodation row {r_num}: total_price_local is not a number")

            # Currency check
            curr = str(row.get("currency", "")).strip().upper()
            city = str(row.get("city", "")).strip()
            if curr not in ["EUR", "PLN", "USD"]:
                errors.append(f"accommodation row {r_num}: unexpected currency '{curr}'")

            # Warnings
            if pd.isna(row.get("listing_url")):
                warnings.append(f"accommodation row {r_num}: missing listing_url")
            if pd.isna(row.get("rating")):
                warnings.append(f"accommodation row {r_num}: missing rating")

    # Check prices
    if "prices" in xl.sheet_names:
        df_pr = pd.read_excel(xl, "prices")
        print(f"Checking 'prices' ({len(df_pr)} rows)...")
        for idx, row in df_pr.iterrows():
            r_num = idx + 2
            for col in ["city", "item_code", "price_local", "currency", "collected_at"]:
                if pd.isna(row.get(col)):
                    errors.append(f"prices row {r_num}: missing required field '{col}'")
            if pd.notna(row.get("price_local")):
                try:
                    val = float(row["price_local"])
                    if val <= 0:
                        errors.append(f"prices row {r_num}: price_local must be > 0 (got {val})")
                except ValueError:
                    errors.append(f"prices row {r_num}: price_local is not a number")

    print("\n--- Validation Summary ---")
    if errors:
        print(f"Found {len(errors)} ERROR(S):")
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("✅ No critical errors found!")

    if warnings:
        print(f"\nFound {len(warnings)} WARNING(S):")
        for w in warnings:
            print(f"  ⚠️  {w}")
    else:
        print("✅ No warnings.")

    return len(errors) == 0

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
