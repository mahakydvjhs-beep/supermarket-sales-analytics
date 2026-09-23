"""
data_loader.py  —  Steps 1, 2 & 3
===================================
Step 1  Collect & Load  : Read CSV, inspect shape & column names.
Step 2  Data Cleaning   : Missing values, duplicates, type coercion,
                          negative numerics, bad dates.
Step 3  Sales Formula   : Calculate  Sales = Quantity × Price
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "supermarket_data.csv")

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
NUMERIC_COLS  = ["Quantity", "Price"]
POSITIVE_COLS = ["Quantity", "Price"]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def load_and_clean(path: str = DATA_PATH):
    """
    Load, clean and enrich the CSV.

    Returns
    -------
    df     : pd.DataFrame   Clean, enriched dataset.
    report : dict           Cleaning report consumed by the Streamlit UI.
    """

    # ── STEP 1 : COLLECT & LOAD ─────────────────────────────────────────────
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df.columns = df.columns.str.strip()

    original_rows = len(df)
    original_cols = list(df.columns)

    # ── STEP 2 : DATA CLEANING ──────────────────────────────────────────────

    # 2-A  Strip leading/trailing whitespace from every string cell
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # 2-B  Capture missing values BEFORE any row is dropped
    missing_series = df.isnull().sum()
    missing_before = missing_series[missing_series > 0].to_dict()
    total_missing  = int(missing_series.sum())

    # 2-C  Drop rows that contain ANY missing value
    n_before             = len(df)
    df.dropna(inplace=True)
    missing_rows_dropped = n_before - len(df)

    # 2-D  Remove exact-duplicate Invoice+StockCode combinations (keep first)
    n_before           = len(df)
    df.drop_duplicates(subset=["Invoice", "StockCode"], keep="first", inplace=True)
    duplicates_dropped = n_before - len(df)

    # 2-E  Parse InvoiceDate; drop rows with unparseable dates
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="%d/%m/%y %H:%M", errors="coerce")
    n_before             = len(df)
    df.dropna(subset=["InvoiceDate"], inplace=True)
    bad_dates_dropped    = n_before - len(df)

    # 2-F  Cast numeric columns; drop rows with non-numeric values
    n_before = len(df)
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=NUMERIC_COLS, inplace=True)
    non_numeric_dropped = n_before - len(df)

    # 2-G  Remove rows with negative/zero values in columns that must be positive
    negative_found = {}
    for col in POSITIVE_COLS:
        n_neg = int((df[col] <= 0).sum())
        if n_neg:
            negative_found[col] = n_neg
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)].copy()

    # ── STEP 3 : CALCULATE  Sales = Quantity × Price ─────────────────────────
    df["Price_Original"]   = df["Price"].round(4)
    df["Sales_Calculated"] = (df["Quantity"] * df["Price"]).round(4)
    df["Sales"]            = df["Sales_Calculated"]

    # ── DERIVED COLUMNS for time analysis ────────────────────────────────────
    df["Year"]        = df["InvoiceDate"].dt.year
    df["Month_num"]   = df["InvoiceDate"].dt.month
    df["Month"]       = df["InvoiceDate"].dt.month_name()
    df["Day_of_week"] = df["InvoiceDate"].dt.day_name()
    df["Hour"]        = df["InvoiceDate"].dt.hour
    df["YearMonth"]   = df["InvoiceDate"].dt.to_period("M").astype(str)

    # Normalise Customer ID
    df["Customer ID"] = df["Customer ID"].astype(str).str.strip()

    df.reset_index(drop=True, inplace=True)

    # ── CLEANING REPORT ───────────────────────────────────────────────────────
    report = {
        # Step 1
        "original_rows"       : original_rows,
        "original_cols"       : original_cols,
        # Step 2 – missing
        "missing_before"      : missing_before,
        "total_missing_cells" : total_missing,
        "missing_rows_dropped": missing_rows_dropped,
        # Step 2 – duplicates
        "duplicates_dropped"  : duplicates_dropped,
        # Step 2 – type errors
        "bad_dates_dropped"   : bad_dates_dropped,
        "non_numeric_dropped" : non_numeric_dropped,
        # Step 2 – value errors
        "negative_found"      : negative_found,
        # Step 3
        "final_rows"          : len(df),
        "total_dropped"       : original_rows - len(df),
    }

    return df, report
