# Supermarket Sales Analytics

A full end-to-end data analytics project built with **Streamlit** and **Plotly**.

## Dataset
`supermarket_data.csv` — UK Retail transactions  
Columns: `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`

## 6 Analysis Steps

| Step | Description |
|------|-------------|
| 1 | **Collect & Load** — Read CSV, inspect shape and column types |
| 2 | **Data Cleaning** — Remove missing values, duplicates, bad dates, and negative quantities |
| 3 | **Sales Formula** — Calculate `Sales = Quantity × Price` for every row |
| 4 | **Summarise** — Totals, counts, and averages by Country, Product, Customer, and Time |
| 5 | **Charts** — Bar, line, pie, and heatmap comparisons |
| 6 | **Business Decisions** — Data-driven recommendations from the results |

## Project Structure

```
mahak/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── data/
│   └── supermarket_data.csv
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # Steps 1, 2 & 3
│   └── analysis.py         # Step 4
└── .streamlit/
    └── config.toml         # Theme configuration
```

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**

## Filters
Use the **sidebar** to filter by:
- Country
- Date Range

All 6 tabs update live based on your selection.
