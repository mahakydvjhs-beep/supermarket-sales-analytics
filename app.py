"""
app.py  —  Supermarket Sales Analytics  (Streamlit)
=====================================================
Run:  streamlit run app.py

Dataset: UK Retail Transactions  (supermarket_data.csv)
Columns: Invoice, StockCode, Description, Quantity, InvoiceDate,
         Price, Customer ID, Country

Steps covered:
  1. Collect & Load CSV dataset
  2. Data cleaning — missing / incorrect values
  3. Calculate Sales = Quantity × Price
  4. Group & summarise  (totals, counts, averages)
  5. Charts to compare results
  6. Business decisions from results
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_loader import load_and_clean, DATA_PATH
from analysis import (
    overall_kpis,
    sales_formula_sample,
    sales_by_country,
    sales_by_product,
    sales_by_customer,
    monthly_sales,
    sales_by_day,
    sales_by_hour,
    country_month_pivot,
    full_summary_table,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Supermarket Sales Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
body, .stApp { font-family: "Segoe UI", system-ui, sans-serif; }

.pg-title {
    font-size: 2rem; font-weight: 700; color: #0f172a;
    border-bottom: 3px solid #2563eb; padding-bottom: .4rem;
    margin-bottom: .15rem;
}
.pg-sub {
    font-size: .95rem; color: #64748b; margin-bottom: 1.4rem;
}

.step-badge {
    display: inline-block;
    background: #2563eb; color: #fff;
    font-size: .72rem; font-weight: 700;
    letter-spacing: .06em; text-transform: uppercase;
    padding: .18rem .55rem; border-radius: 999px;
    margin-right: .45rem; vertical-align: middle;
}

.sec-head {
    font-size: 1.05rem; font-weight: 600; color: #0f172a;
    border-left: 4px solid #2563eb; padding-left: .55rem;
    margin-top: 1.6rem; margin-bottom: .7rem;
}

.kpi-wrap {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 1rem 1.1rem;
    text-align: center; height: 100%;
}
.kpi-label {
    font-size: .7rem; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: .07em;
    margin-bottom: .3rem;
}
.kpi-val { font-size: 1.55rem; font-weight: 700; color: #0f172a; }
.kpi-unit { font-size: .78rem; color: #94a3b8; margin-top: .1rem; }

.box { border-radius: 7px; padding: .75rem 1rem; margin-bottom: .5rem; font-size: .9rem; }
.box-info  { background:#eff6ff; border-left:4px solid #2563eb; color:#1e3a5f; }
.box-good  { background:#f0fdf4; border-left:4px solid #16a34a; color:#14532d; }
.box-warn  { background:#fffbeb; border-left:4px solid #d97706; color:#78350f; }
.box-error { background:#fef2f2; border-left:4px solid #dc2626; color:#7f1d1d; }

.formula {
    background:#f1f5f9; border:1px solid #cbd5e1;
    border-radius:8px; padding:.8rem 1.2rem;
    font-family: "Courier New", monospace; font-size:1.05rem;
    color:#1e293b; margin: .6rem 0 1rem 0;
    text-align: center; font-weight: 600;
}

section[data-testid="stSidebar"] { background: #f8fafc; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: .88rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────
COLORS   = px.colors.qualitative.Set2
PLT_BASE = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(t=46, b=20, l=10, r=10),
    font=dict(family="Segoe UI, system-ui, sans-serif", size=12),
)


def kpi(col, label, value, unit=""):
    col.markdown(
        f'<div class="kpi-wrap">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-val">{value}</div>'
        f'<div class="kpi-unit">{unit}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def sec(text, step=None):
    badge = f'<span class="step-badge">Step {step}</span>' if step else ""
    st.markdown(f'<div class="sec-head">{badge}{text}</div>', unsafe_allow_html=True)


def box(kind, text):
    st.markdown(f'<div class="box box-{kind}">{text}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Load data (cached)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="⏳ Loading and cleaning dataset…")
def get_data():
    return load_and_clean(DATA_PATH)


df_full, rpt = get_data()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — filters
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛒 Supermarket Analytics")
    st.markdown("---")
    st.markdown("### 🔍 Filters")

    all_countries = sorted(df_full["Country"].unique())
    sel_country = st.multiselect(
        "Country",
        all_countries,
        default=all_countries[:5] if len(all_countries) > 5 else all_countries,
    )

    min_d = df_full["InvoiceDate"].min().date()
    max_d = df_full["InvoiceDate"].max().date()
    date_range = st.date_input(
        "Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d
    )

    st.markdown("---")

# Apply filters
df = df_full.copy()
if sel_country:
    df = df[df["Country"].isin(sel_country)]
if len(date_range) == 2:
    df = df[
        (df["InvoiceDate"].dt.date >= date_range[0])
        & (df["InvoiceDate"].dt.date <= date_range[1])
    ]

with st.sidebar:
    st.caption(f"**{len(df):,}** of **{len(df_full):,}** rows selected")
    st.markdown("---")
    st.markdown(
        "<small style='color:#94a3b8'>UK Retail Dataset<br>"
        f"{rpt['final_rows']:,} clean transactions<br>"
        f"{df_full['Country'].nunique()} countries</small>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="pg-title">🛒 Supermarket Sales Analytics</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="pg-sub">End-to-end data analytics pipeline · '
    'Steps 1 – 6 · Dataset: UK Retail Transactions · '
    f'{rpt["final_rows"]:,} clean rows · {df_full["Country"].nunique()} countries</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
T = st.tabs([
    "📋 Step 1 — Load Data",
    "🧹 Step 2 — Data Cleaning",
    "🧮 Step 3 — Sales Formula",
    "📊 Step 4 — Summaries",
    "📈 Step 5 — Charts",
    "💡 Step 6 — Decisions",
])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1  — Collect & Load
# ══════════════════════════════════════════════════════════════════════════════
with T[0]:
    sec("Dataset Overview", step=1)

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    kpi(r1c1, "Total Rows Loaded",  f"{rpt['original_rows']:,}")
    kpi(r1c2, "Total Columns",      f"{len(rpt['original_cols']):,}")
    kpi(r1c3, "Clean Rows",         f"{rpt['final_rows']:,}")
    kpi(r1c4, "Rows Dropped",       f"{rpt['total_dropped']:,}")

    sec("Column Names & Data Types")
    dtype_df = pd.DataFrame({
        "Column"          : df_full.columns.tolist(),
        "Data Type"       : df_full.dtypes.astype(str).tolist(),
        "Non-Null Count"  : df_full.notna().sum().tolist(),
        "Sample Value"    : [str(df_full[c].iloc[0]) if len(df_full) else "—" for c in df_full.columns],
    })
    st.dataframe(dtype_df, use_container_width=True, height=420)

    sec("First 50 Rows of Raw Dataset")
    raw_display = df_full.drop(
        columns=["Price_Original", "Sales_Calculated", "Year", "Month_num",
                 "Month", "Day_of_week", "Hour", "YearMonth"],
        errors="ignore",
    ).head(50)
    st.dataframe(raw_display, use_container_width=True, height=380)

    box("info",
        f"✅ <b>Loaded successfully</b>: <b>{rpt['original_rows']:,}</b> rows × "
        f"<b>{len(rpt['original_cols'])}</b> columns from <code>supermarket_data.csv</code>.")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2  — Data Cleaning
# ══════════════════════════════════════════════════════════════════════════════
with T[1]:
    sec("Cleaning Summary", step=2)

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi(c1, "Original Rows",      f"{rpt['original_rows']:,}")
    kpi(c2, "Missing Cells",      f"{rpt['total_missing_cells']:,}")
    kpi(c3, "Duplicates Removed", f"{rpt['duplicates_dropped']:,}")
    kpi(c4, "Rows Dropped Total", f"{rpt['total_dropped']:,}")
    kpi(c5, "Final Clean Rows",   f"{rpt['final_rows']:,}")

    # ── 2A: Missing values ───────────────────────────────────────────────────
    sec("Check 1 — Missing Values")
    if rpt["missing_before"]:
        miss_df = (
            pd.DataFrame.from_dict(rpt["missing_before"], orient="index", columns=["Missing Count"])
            .reset_index().rename(columns={"index": "Column"})
        )
        fig = px.bar(
            miss_df, x="Column", y="Missing Count",
            title="Missing Values per Column (before cleaning)",
            color="Missing Count", color_continuous_scale="Reds",
            text_auto=True,
        )
        fig.update_layout(**PLT_BASE, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        box("good", "✅ <b>No missing values</b> found in the dataset.")

    # ── 2B: Duplicates ───────────────────────────────────────────────────────
    sec("Check 2 — Duplicate Rows")
    if rpt["duplicates_dropped"] == 0:
        box("good", "✅ <b>No duplicate rows</b> detected after removing duplicates.")
    else:
        box("warn",
            f"⚠️ <b>{rpt['duplicates_dropped']:,}</b> duplicate rows removed "
            "(same Invoice + StockCode combination).")

    # ── 2C: Numeric validation ───────────────────────────────────────────────
    sec("Check 3 — Numeric Column Validation")
    if rpt["negative_found"]:
        for col, cnt in rpt["negative_found"].items():
            box("warn", f"⚠️ <b>[{col}]</b>: {cnt:,} negative/zero values detected and removed.")
    else:
        box("good", "✅ <b>No negative or zero values</b> found in Quantity or Price.")

    if rpt["bad_dates_dropped"] > 0:
        box("warn",
            f"⚠️ <b>InvoiceDate</b>: {rpt['bad_dates_dropped']:,} rows had unparseable dates — removed.")
    else:
        box("good", "✅ <b>InvoiceDate</b>: all dates are valid and properly parsed.")

    if rpt["non_numeric_dropped"] > 0:
        box("warn",
            f"⚠️ {rpt['non_numeric_dropped']:,} rows contained non-numeric values in Quantity/Price.")
    else:
        box("good", "✅ All numeric columns (Quantity, Price) contain valid numbers.")

    # ── 2D: Descriptive statistics ───────────────────────────────────────────
    sec("Check 4 — Descriptive Statistics (after cleaning)")
    num_cols = ["Quantity", "Price", "Sales"]
    st.dataframe(
        df[num_cols].describe().round(3).T.rename(columns={
            "count": "Count", "mean": "Mean", "std": "Std Dev",
            "min": "Min", "25%": "Q1", "50%": "Median", "75%": "Q3", "max": "Max",
        }),
        use_container_width=True,
    )

    box("info",
        "🔍 <b>Cleaning pipeline:</b> "
        "whitespace stripping → missing-value removal → duplicate removal → "
        "date parsing → numeric coercion → negative/zero-value filter.")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3  — Sales Formula
# ══════════════════════════════════════════════════════════════════════════════
with T[2]:
    sec("Sales Calculation", step=3)

    st.markdown(
        '<div class="formula">Sales &nbsp;=&nbsp; Quantity &nbsp;×&nbsp; Unit Price (Price)</div>',
        unsafe_allow_html=True,
    )

    f1, f2, f3 = st.columns(3)
    kpi(f1, "Rows Calculated",    f"{rpt['final_rows']:,}")
    kpi(f2, "Total Sales (£)",    f"£{df_full['Sales'].sum():,.0f}")
    kpi(f3, "Avg Sale / Row",     f"£{df_full['Sales'].mean():,.2f}")

    box("good",
        "✅ <b>Sales column created</b> by calculating Quantity × Price for every row. "
        "All values are positive and verified.")

    sec("Sample: Quantity × Price = Sales  (first 20 rows)")
    sample = sales_formula_sample(df_full)
    st.dataframe(
        sample.style.format({
            "Quantity"           : "{:.0f}",
            "Price"              : "£{:.2f}",
            "Qty × Price  (Sales)": "£{:.4f}",
        }),
        use_container_width=True,
        height=440,
    )

    sec("Sales Distribution")
    fig = px.histogram(
        df_full, x="Sales", nbins=60,
        title="Distribution of Sales (Quantity × Price)",
        labels={"Sales": "Sales (£)"},
        color_discrete_sequence=["#2563eb"],
    )
    fig.update_layout(**PLT_BASE)
    st.plotly_chart(fig, use_container_width=True)

    box("info",
        "ℹ️ The dataset records individual line items per invoice. "
        "<b>Sales = Quantity × Price</b> gives the revenue for each line. "
        "To get invoice-level totals, line-item Sales are summed per Invoice ID.")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4  — Group & Summarise
# ══════════════════════════════════════════════════════════════════════════════
with T[3]:
    kpis = overall_kpis(df)

    sec("Overall KPIs (Totals, Counts & Averages)", step=4)

    row1 = st.columns(5)
    kpi(row1[0], "Total Line Items",      f"{kpis['total_transactions']:,}")
    kpi(row1[1], "Total Sales",           f"£{kpis['total_sales']:,.0f}", "GBP")
    kpi(row1[2], "Total Units Sold",      f"{kpis['total_units_sold']:,}", "units")
    kpi(row1[3], "Unique Customers",      f"{kpis['unique_customers']:,}")
    kpi(row1[4], "Unique Products",       f"{kpis['unique_products']:,}")

    st.markdown("<br>", unsafe_allow_html=True)
    row2 = st.columns(5)
    kpi(row2[0], "Unique Countries",      f"{kpis['unique_countries']:,}")
    kpi(row2[1], "Avg Sale / Line Item",  f"£{kpis['avg_sales_per_txn']:,.2f}", "GBP")
    kpi(row2[2], "Avg Unit Price",        f"£{kpis['avg_unit_price']:,.2f}", "GBP")
    kpi(row2[3], "Avg Qty / Line",        f"{kpis['avg_quantity']:.2f}", "items")
    kpi(row2[4], "Avg Invoice Value",     f"£{kpis['avg_sales_per_invoice']:,.2f}", "GBP")

    # ── Country ──────────────────────────────────────────────────────────────
    sec("Summary by Country")
    cou = sales_by_country(df)
    st.dataframe(
        cou.style.format({
            "Total_Sales"       : "£{:,.2f}",
            "Avg_Sales_per_Txn" : "£{:,.2f}",
        }).background_gradient(subset=["Total_Sales"], cmap="Blues"),
        use_container_width=True, hide_index=True,
    )

    # ── Top Products ─────────────────────────────────────────────────────────
    sec("Top 20 Products by Sales")
    pr = sales_by_product(df)
    st.dataframe(
        pr.style.format({
            "Total_Sales" : "£{:,.2f}",
            "Avg_Price"   : "£{:,.2f}",
        }).background_gradient(subset=["Total_Sales"], cmap="Greens"),
        use_container_width=True, hide_index=True,
    )

    # ── Top Customers ─────────────────────────────────────────────────────────
    sec("Top 20 Customers by Sales")
    cu = sales_by_customer(df)
    st.dataframe(
        cu.style.format({
            "Total_Sales"     : "£{:,.2f}",
            "Avg_Order_Value" : "£{:,.2f}",
        }).background_gradient(subset=["Total_Sales"], cmap="Purples"),
        use_container_width=True, hide_index=True,
    )

    # ── Monthly ───────────────────────────────────────────────────────────────
    sec("Monthly Summary (Totals, Counts, Averages)")
    mo = monthly_sales(df)
    st.dataframe(
        mo.style.format({
            "Total_Sales"      : "£{:,.2f}",
            "Avg_Sales_per_Txn": "£{:,.2f}",
        }).background_gradient(subset=["Total_Sales"], cmap="Blues"),
        use_container_width=True, hide_index=True,
    )

    # ── Full cross-tab ────────────────────────────────────────────────────────
    with st.expander("📋 Full Cross-Tab Summary  (Country × Product)"):
        ft = full_summary_table(df)
        st.dataframe(
            ft.style.format({
                "Total_Sales" : "£{:,.2f}",
                "Avg_Price"   : "£{:,.2f}",
                "Avg_Sales"   : "£{:,.2f}",
            }).background_gradient(subset=["Total_Sales"], cmap="Blues"),
            use_container_width=True, height=420,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 5  — Charts
# ══════════════════════════════════════════════════════════════════════════════
with T[4]:
    sec("Visual Comparisons", step=5)

    cou  = sales_by_country(df)
    pr   = sales_by_product(df)
    cu   = sales_by_customer(df)
    mo   = monthly_sales(df)
    dy   = sales_by_day(df)
    hr   = sales_by_hour(df)
    pvt  = country_month_pivot(df)

    # ── Row A: Country ────────────────────────────────────────────────────────
    sec("Sales by Country")
    top10_cou = cou.head(10)
    a1, a2 = st.columns(2)
    with a1:
        fig = px.bar(
            top10_cou.sort_values("Total_Sales"),
            x="Total_Sales", y="Country", orientation="h",
            color="Total_Sales", color_continuous_scale="Blues",
            title="Top 10 Countries by Total Sales",
            text_auto=".2s",
            labels={"Total_Sales": "Total Sales (£)", "Country": ""},
        )
        fig.update_layout(**PLT_BASE, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with a2:
        fig = px.bar(
            top10_cou.sort_values("Transactions"),
            x="Transactions", y="Country", orientation="h",
            color="Transactions", color_continuous_scale="Purples",
            title="Top 10 Countries by Number of Invoices",
            text_auto=True,
            labels={"Country": ""},
        )
        fig.update_layout(**PLT_BASE, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Pie chart — country share
    top5_cou = cou.head(5)
    others   = pd.DataFrame([{
        "Country": "Others",
        "Total_Sales": cou.iloc[5:]["Total_Sales"].sum() if len(cou) > 5 else 0,
    }])
    pie_data = pd.concat([top5_cou[["Country", "Total_Sales"]], others], ignore_index=True)
    pie_data = pie_data[pie_data["Total_Sales"] > 0]

    fig = px.pie(
        pie_data, names="Country", values="Total_Sales",
        title="Sales Share by Country (Top 5 + Others)",
        color_discrete_sequence=COLORS, hole=0.42,
    )
    fig.update_layout(**PLT_BASE)
    st.plotly_chart(fig, use_container_width=True)

    # ── Row B: Products ────────────────────────────────────────────────────────
    sec("Top Products")
    b1, b2 = st.columns(2)
    with b1:
        top10_pr = pr.head(10)
        fig = px.bar(
            top10_pr.sort_values("Total_Sales"),
            x="Total_Sales", y="Description", orientation="h",
            color="Total_Sales", color_continuous_scale="Teal",
            title="Top 10 Products by Total Sales",
            text_auto=".2s",
            labels={"Total_Sales": "Total Sales (£)", "Description": ""},
        )
        fig.update_layout(**PLT_BASE, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with b2:
        top10_qty = pr.sort_values("Total_Units_Sold", ascending=False).head(10)
        fig = px.bar(
            top10_qty.sort_values("Total_Units_Sold"),
            x="Total_Units_Sold", y="Description", orientation="h",
            color="Total_Units_Sold", color_continuous_scale="Oranges",
            title="Top 10 Products by Units Sold",
            text_auto=True,
            labels={"Total_Units_Sold": "Units Sold", "Description": ""},
        )
        fig.update_layout(**PLT_BASE, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Row C: Customers ──────────────────────────────────────────────────────
    sec("Top Customers")
    top10_cu = cu.head(10)
    fig = px.bar(
        top10_cu,
        x="Customer ID", y="Total_Sales",
        color="Total_Sales", color_continuous_scale="Greens",
        title="Top 10 Customers by Total Sales",
        text_auto=".2s",
        labels={"Total_Sales": "Total Sales (£)"},
    )
    fig.update_layout(**PLT_BASE, coloraxis_showscale=False, xaxis_tickangle=-20)
    st.plotly_chart(fig, use_container_width=True)

    # ── Row D: Time Trends ────────────────────────────────────────────────────
    sec("Time Trends")

    # Monthly dual-axis chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=mo["YearMonth"], y=mo["Total_Sales"],
        name="Total Sales",
        marker_color="#2563eb",
        text=[f"£{v:,.0f}" for v in mo["Total_Sales"]],
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        x=mo["YearMonth"], y=mo["Avg_Sales_per_Txn"],
        name="Avg Sale / Line",
        mode="lines+markers",
        marker=dict(size=8, color="#f59e0b"),
        line=dict(width=2.5, color="#f59e0b"),
        yaxis="y2",
    ))
    fig.update_layout(
        **PLT_BASE,
        title="Monthly Sales vs Average Sale per Line Item",
        yaxis=dict(title="Total Sales (£)"),
        yaxis2=dict(title="Avg Sale (£)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.12),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig, use_container_width=True)

    d1, d2 = st.columns(2)
    with d1:
        fig = px.bar(
            dy, x="Day_of_week", y="Total_Sales",
            color="Total_Sales", color_continuous_scale="Blues",
            title="Total Sales by Day of Week",
            text_auto=".2s",
            labels={"Day_of_week": "Day", "Total_Sales": "Total Sales (£)"},
        )
        fig.update_layout(**PLT_BASE, coloraxis_showscale=False, xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)
    with d2:
        fig = px.line(
            hr, x="Hour", y="Total_Sales",
            markers=True,
            title="Sales by Hour of Day  (Peak Hours)",
            labels={"Total_Sales": "Total Sales (£)", "Hour": "Hour (24h)"},
            color_discrete_sequence=["#7c3aed"],
        )
        fig.update_traces(line_width=2.5, marker_size=8)
        fig.update_layout(**PLT_BASE)
        st.plotly_chart(fig, use_container_width=True)

    # ── Row E: Country × Month Heatmap ────────────────────────────────────────
    sec("Country × Month Heatmap  (Top 10 Countries)")
    if not pvt.empty:
        fig = px.imshow(
            pvt, text_auto=".2s",
            color_continuous_scale="Blues",
            title="Total Sales (£) — Country vs Month (Top 10 Countries)",
            labels={"color": "Sales (£)"},
            aspect="auto",
        )
        fig.update_layout(**PLT_BASE, margin=dict(t=56, b=20, l=150, r=10))
        st.plotly_chart(fig, use_container_width=True)

    # ── Row F: Monthly transactions & units ───────────────────────────────────
    d3, d4 = st.columns(2)
    with d3:
        fig = px.bar(
            mo, x="YearMonth", y="Total_Units_Sold",
            color="Total_Units_Sold", color_continuous_scale="Teal",
            title="Units Sold per Month",
            text_auto=True,
        )
        fig.update_layout(**PLT_BASE, coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
    with d4:
        fig = px.line(
            mo, x="YearMonth", y="Transactions",
            markers=True, color_discrete_sequence=["#16a34a"],
            title="Number of Invoices per Month",
        )
        fig.update_traces(line_width=2.5, marker_size=9)
        fig.update_layout(**PLT_BASE, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 6  — Business Decisions
# ══════════════════════════════════════════════════════════════════════════════
with T[5]:
    kpis = overall_kpis(df)
    cou  = sales_by_country(df)
    pr   = sales_by_product(df)
    cu   = sales_by_customer(df)
    hr   = sales_by_hour(df)
    mo   = monthly_sales(df)
    dy   = sales_by_day(df)

    def safe_val(frame, col, idx=0):
        return frame.iloc[idx][col] if len(frame) > idx else "N/A"

    top_country       = safe_val(cou, "Country")
    top_country_sales = safe_val(cou, "Total_Sales")
    bot_country       = safe_val(cou, "Country", min(len(cou) - 1, len(cou) - 1))
    top_product       = safe_val(pr,  "Description")
    top_product_sales = safe_val(pr,  "Total_Sales")
    top_customer      = safe_val(cu,  "Customer ID")
    top_cust_sales    = safe_val(cu,  "Total_Sales")
    peak_row          = hr.loc[hr["Total_Sales"].idxmax()] if len(hr) else None
    peak_hour_fmt     = (
        f"{int(peak_row['Hour'])}:00 – {int(peak_row['Hour']) + 1}:00"
        if peak_row is not None else "N/A"
    )
    best_month_row    = mo.loc[mo["Total_Sales"].idxmax()] if len(mo) else None
    best_month        = best_month_row["YearMonth"] if best_month_row is not None else "N/A"
    worst_month_row   = mo.loc[mo["Total_Sales"].idxmin()] if len(mo) else None
    worst_month       = worst_month_row["YearMonth"] if worst_month_row is not None else "N/A"
    top_day_row       = dy.loc[dy["Total_Sales"].idxmax()] if len(dy) else None
    top_day           = top_day_row["Day_of_week"] if top_day_row is not None else "N/A"

    sec("Data-Driven Business Recommendations", step=6)

    insights = [
        ("good", "🌍 Top Revenue Country",
         f"<b>{top_country}</b> generated <b>£{top_country_sales:,.0f}</b> in total sales — "
         f"the highest of all countries in the selection. Prioritise logistics, local partnerships, "
         f"and marketing investment in this market."),

        ("warn", "📉 Expand to Underperforming Markets",
         f"Many non-UK countries contribute a small fraction of total revenue. "
         f"Consider targeted regional campaigns, localised pricing, and dedicated account managers "
         f"to grow sales in lower-performing markets."),

        ("good", "📦 Best-Selling Product",
         f"<b>{top_product}</b> leads in revenue with <b>£{top_product_sales:,.0f}</b>. "
         f"Ensure consistent stock levels, fast re-ordering, and feature it prominently "
         f"in catalogues and promotions."),

        ("warn", "📦 Low-Performing Products",
         f"Products at the bottom of the revenue list should be reviewed for discontinuation "
         f"or repositioning. Consider bundling with bestsellers to clear slow-moving stock."),

        ("good", "👤 Top Customer Value",
         f"Customer <b>{top_customer}</b> spent <b>£{top_cust_sales:,.0f}</b> — the highest "
         f"in the selected period. Nurture top customers with exclusive loyalty rewards, "
         f"early access to new products, and dedicated account support."),

        ("info", "💡 Customer Retention",
         f"With <b>{kpis['unique_customers']:,}</b> unique customers, building a loyalty programme "
         f"and tracking repeat-purchase rates can significantly increase customer lifetime value."),

        ("good", "⏰ Peak Sales Hour",
         f"The busiest hour is <b>{peak_hour_fmt}</b>. "
         f"Maximise staffing, website/app capacity, and flash promotions during this window "
         f"to capture the highest-intent shoppers."),

        ("good", "📅 Best Month",
         f"<b>{best_month}</b> was the strongest month. "
         f"Analyse what drove that performance — seasonal demand, promotions, or catalogue updates "
         f"— and replicate those tactics in slower months."),

        ("warn", "📅 Weakest Month",
         f"<b>{worst_month}</b> had the lowest revenue. "
         f"Plan targeted campaigns (clearance sales, loyalty incentives, email campaigns) "
         f"to boost off-peak performance."),

        ("good", "📆 Best Day of Week",
         f"<b>{top_day}</b> consistently delivers the highest sales. "
         f"Schedule promotions, email blasts, and social media campaigns to land on this day."),

        ("info", "💰 Upsell & Cross-Sell",
         f"Average sale per line item is <b>£{kpis['avg_sales_per_txn']:,.2f}</b> and "
         f"average invoice value is <b>£{kpis['avg_sales_per_invoice']:,.2f}</b>. "
         f"Implement 'Frequently Bought Together' recommendations and minimum-order discounts "
         f"to push average order value above <b>£{kpis['avg_sales_per_invoice'] * 1.15:,.2f}</b> (+15%)."),

        ("info", "📊 Product Breadth",
         f"The catalogue spans <b>{kpis['unique_products']:,}</b> unique products across "
         f"<b>{kpis['unique_countries']:,}</b> countries. "
         f"Regularly audit the product mix to retire low-margin lines and introduce "
         f"high-demand seasonal items."),
    ]

    for kind, title, body in insights:
        st.markdown(
            f'<div class="box box-{kind}"><b>{title}</b><br>{body}</div>',
            unsafe_allow_html=True,
        )

    # ── Country scorecard ──────────────────────────────────────────────────────
    sec("Country Scorecard  (Normalised Multi-Metric Comparison, Top 10)")
    top10_cou_score = cou.head(10).copy()
    if len(top10_cou_score) >= 2:
        metrics = [
            ("Total_Sales",      "Total Sales",       "#2563eb"),
            ("Transactions",     "Invoices",           "#7c3aed"),
            ("Total_Units_Sold", "Units Sold",         "#16a34a"),
            ("Unique_Customers", "Unique Customers",   "#d97706"),
        ]
        fig = go.Figure()
        for col, lbl, colour in metrics:
            vals = top10_cou_score[col]
            norm = (vals - vals.min()) / (vals.max() - vals.min() + 1e-9)
            fig.add_trace(go.Bar(
                name=lbl, x=top10_cou_score["Country"], y=norm,
                marker_color=colour,
                text=top10_cou_score[col].round(1),
                textposition="inside",
            ))
        fig.update_layout(
            **PLT_BASE,
            title="Normalised Country Scorecard (0 = worst, 1 = best within selection)",
            barmode="group",
            yaxis_title="Normalised Score  (0–1)",
            legend=dict(orientation="h", y=1.12),
            xaxis_tickangle=-20,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Top 10 highest-value invoices ─────────────────────────────────────────
    sec("Top 10 Highest-Value Invoices")
    inv_totals = (
        df.groupby(["Invoice", "Country", "Customer ID"])["Sales"]
        .sum()
        .reset_index()
        .rename(columns={"Sales": "Invoice_Total"})
        .sort_values("Invoice_Total", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    inv_totals.index += 1
    st.dataframe(
        inv_totals.style
        .format({"Invoice_Total": "£{:,.2f}"})
        .background_gradient(subset=["Invoice_Total"], cmap="Blues"),
        use_container_width=True,
    )

    box("info",
        "📌 <b>How to use these insights:</b> Each recommendation is derived "
        "from the aggregated data in Step 4. Use the <b>sidebar filters</b> to drill into "
        "a specific country or date range and regenerate all insights for that segment.")


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:.78rem;color:#94a3b8'>"
    "Supermarket Sales Analytics &nbsp;·&nbsp; UK Retail Dataset &nbsp;·&nbsp; "
    "Built with Streamlit &amp; Plotly"
    "</div>",
    unsafe_allow_html=True,
)
