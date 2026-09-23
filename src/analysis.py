"""
analysis.py  —  Step 4
========================
Group & Summarise: produce totals, counts and averages across every
analytical dimension for the UK Retail dataset.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# 1. Scalar KPIs
# ---------------------------------------------------------------------------
def overall_kpis(df: pd.DataFrame) -> dict:
    return {
        "total_transactions"   : len(df),
        "total_sales"          : round(float(df["Sales"].sum()), 2),
        "total_units_sold"     : int(df["Quantity"].sum()),
        "unique_customers"     : int(df["Customer ID"].nunique()),
        "unique_products"      : int(df["StockCode"].nunique()),
        "unique_countries"     : int(df["Country"].nunique()),
        "avg_sales_per_txn"    : round(float(df["Sales"].mean()), 2),
        "avg_unit_price"       : round(float(df["Price"].mean()), 2),
        "avg_quantity"         : round(float(df["Quantity"].mean()), 2),
        "avg_sales_per_invoice": round(float(df.groupby("Invoice")["Sales"].sum().mean()), 2),
    }


# ---------------------------------------------------------------------------
# 2. Sales formula sample table  (Step 3 display)
# ---------------------------------------------------------------------------
def sales_formula_sample(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    cols = ["Invoice", "StockCode", "Description", "Quantity", "Price", "Sales_Calculated"]
    return (
        df[cols]
        .head(n)
        .rename(columns={
            "Sales_Calculated": "Qty × Price  (Sales)",
        })
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 3. By Country
# ---------------------------------------------------------------------------
def sales_by_country(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Country", as_index=False)
        .agg(
            Total_Sales        = ("Sales",       "sum"),
            Transactions       = ("Invoice",     "nunique"),
            Total_Units_Sold   = ("Quantity",    "sum"),
            Avg_Sales_per_Txn  = ("Sales",       "mean"),
            Unique_Customers   = ("Customer ID", "nunique"),
            Unique_Products    = ("StockCode",   "nunique"),
        )
        .round(2)
        .sort_values("Total_Sales", ascending=False)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 4. By Product (Top N by sales)
# ---------------------------------------------------------------------------
def sales_by_product(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    return (
        df.groupby(["StockCode", "Description"], as_index=False)
        .agg(
            Total_Sales      = ("Sales",    "sum"),
            Total_Units_Sold = ("Quantity", "sum"),
            Transactions     = ("Invoice",  "nunique"),
            Avg_Price        = ("Price",    "mean"),
        )
        .round(2)
        .sort_values("Total_Sales", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 5. By Customer
# ---------------------------------------------------------------------------
def sales_by_customer(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    return (
        df.groupby("Customer ID", as_index=False)
        .agg(
            Total_Sales      = ("Sales",    "sum"),
            Total_Orders     = ("Invoice",  "nunique"),
            Total_Units      = ("Quantity", "sum"),
            Avg_Order_Value  = ("Sales",    "mean"),
        )
        .round(2)
        .sort_values("Total_Sales", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 6. Monthly Trend
# ---------------------------------------------------------------------------
def monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["Year", "Month_num", "Month", "YearMonth"], as_index=False)
        .agg(
            Total_Sales       = ("Sales",    "sum"),
            Transactions      = ("Invoice",  "nunique"),
            Total_Units_Sold  = ("Quantity", "sum"),
            Avg_Sales_per_Txn = ("Sales",    "mean"),
        )
        .round(2)
        .sort_values(["Year", "Month_num"])
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 7. By Day of Week
# ---------------------------------------------------------------------------
def sales_by_day(df: pd.DataFrame) -> pd.DataFrame:
    ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result = (
        df.groupby("Day_of_week", as_index=False)
        .agg(
            Total_Sales  = ("Sales",   "sum"),
            Transactions = ("Invoice", "nunique"),
            Avg_Sales    = ("Sales",   "mean"),
        )
        .round(2)
    )
    result["Day_of_week"] = pd.Categorical(result["Day_of_week"], categories=ORDER, ordered=True)
    return result.sort_values("Day_of_week").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 8. By Hour of Day
# ---------------------------------------------------------------------------
def sales_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Hour", as_index=False)
        .agg(
            Total_Sales  = ("Sales",   "sum"),
            Transactions = ("Invoice", "nunique"),
            Avg_Sales    = ("Sales",   "mean"),
        )
        .round(2)
        .sort_values("Hour")
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 9. Country × Month pivot (heatmap source)
# ---------------------------------------------------------------------------
def country_month_pivot(df: pd.DataFrame, top_n_countries: int = 10) -> pd.DataFrame:
    top_countries = (
        df.groupby("Country")["Sales"].sum()
        .nlargest(top_n_countries).index.tolist()
    )
    sub = df[df["Country"].isin(top_countries)]
    pivot = sub.pivot_table(
        index="Country", columns="YearMonth", values="Sales", aggfunc="sum"
    ).fillna(0).round(2)
    return pivot


# ---------------------------------------------------------------------------
# 10. Full cross-tab summary
# ---------------------------------------------------------------------------
def full_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["Country", "StockCode", "Description"], as_index=False)
        .agg(
            Total_Sales      = ("Sales",    "sum"),
            Transactions     = ("Invoice",  "nunique"),
            Total_Units_Sold = ("Quantity", "sum"),
            Avg_Price        = ("Price",    "mean"),
            Avg_Sales        = ("Sales",    "mean"),
        )
        .round(2)
        .sort_values("Total_Sales", ascending=False)
        .reset_index(drop=True)
    )
