"""
Sales Dashboard — Single Screen Streamlit App
Run with: streamlit run streamlit_app.py

If you have your own sales CSV, upload it via the sidebar uploader.
Expected columns (flexible — the app will try to auto-detect):
    date, region, product, category, salesperson, units, revenue
If no file is uploaded, the app generates realistic sample data so
the dashboard works out of the box.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# PAGE CONFIG (must be the first Streamlit call)
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# SAMPLE DATA GENERATOR (used when no file is uploaded)
# ----------------------------------------------------------------------
@st.cache_data
def generate_sample_data(n_rows: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    regions = ["North", "South", "East", "West", "Central"]
    categories = ["Electronics", "Apparel", "Home & Garden", "Sports", "Beauty"]
    products = {
        "Electronics": ["Headphones", "Smartwatch", "Speaker", "Tablet"],
        "Apparel": ["T-Shirt", "Jacket", "Sneakers", "Jeans"],
        "Home & Garden": ["Lamp", "Cushion", "Planter", "Rug"],
        "Sports": ["Yoga Mat", "Dumbbells", "Running Shoes", "Bike Helmet"],
        "Beauty": ["Moisturizer", "Perfume", "Lipstick", "Shampoo"],
    }
    salespeople = ["Aisha", "Bilal", "Chen", "Diego", "Elena", "Farhan", "Grace", "Hassan"]

    start_date = datetime.today() - timedelta(days=365)
    dates = [start_date + timedelta(days=int(d)) for d in rng.integers(0, 365, n_rows)]
    region_choice = rng.choice(regions, n_rows)
    category_choice = rng.choice(categories, n_rows)
    product_choice = [rng.choice(products[c]) for c in category_choice]
    salesperson_choice = rng.choice(salespeople, n_rows)
    units = rng.integers(1, 25, n_rows)
    unit_price = rng.uniform(8, 400, n_rows).round(2)
    revenue = (units * unit_price).round(2)

    df = pd.DataFrame({
        "date": dates,
        "region": region_choice,
        "category": category_choice,
        "product": product_choice,
        "salesperson": salesperson_choice,
        "units": units,
        "unit_price": unit_price,
        "revenue": revenue,
    })
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data
def load_uploaded_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


# ----------------------------------------------------------------------
# SIDEBAR — DATA SOURCE + FILTERS
# ----------------------------------------------------------------------
st.sidebar.title("📊 Sales Dashboard")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("Upload sales CSV (optional)", type=["csv"])

if uploaded_file is not None:
    df = load_uploaded_data(uploaded_file)
    st.sidebar.success(f"Loaded {len(df):,} rows from your file.")
else:
    df = generate_sample_data()
    st.sidebar.info("No file uploaded — showing sample data.")

st.sidebar.markdown("### Filters")

# Date filter
if "date" in df.columns and df["date"].notna().any():
    min_date, max_date = df["date"].min(), df["date"].max()
    date_range = st.sidebar.date_input(
        "Date range", value=(min_date.date(), max_date.date()),
        min_value=min_date.date(), max_value=max_date.date()
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        df = df[(df["date"] >= pd.Timestamp(date_range[0])) &
                (df["date"] <= pd.Timestamp(date_range[1]))]

# Categorical filters (only shown if column exists)
def multiselect_filter(col_name, label):
    global df
    if col_name in df.columns:
        options = sorted(df[col_name].dropna().unique().tolist())
        selected = st.sidebar.multiselect(label, options, default=options)
        df = df[df[col_name].isin(selected)]

multiselect_filter("region", "Region")
multiselect_filter("category", "Category")
multiselect_filter("salesperson", "Salesperson")

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit • Plotly")

# ----------------------------------------------------------------------
# MAIN — HEADER + KPIs
# ----------------------------------------------------------------------
st.title("📊 Sales Performance Dashboard")

if df.empty:
    st.warning("No data matches the current filters. Adjust filters in the sidebar.")
    st.stop()

total_revenue = df["revenue"].sum() if "revenue" in df.columns else 0
total_units = df["units"].sum() if "units" in df.columns else 0
avg_order_value = (total_revenue / len(df)) if len(df) else 0
n_orders = len(df)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"${total_revenue:,.0f}")
k2.metric("Units Sold", f"{total_units:,.0f}")
k3.metric("Orders", f"{n_orders:,}")
k4.metric("Avg Order Value", f"${avg_order_value:,.2f}")

st.markdown("---")

# ----------------------------------------------------------------------
# CHART ROW 1 — Revenue trend + Revenue by category
# ----------------------------------------------------------------------
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Revenue Trend")
    if "date" in df.columns:
        trend = df.groupby(df["date"].dt.to_period("W")).agg(revenue=("revenue", "sum")).reset_index()
        trend["date"] = trend["date"].dt.start_time
        fig_trend = px.line(trend, x="date", y="revenue", markers=True)
        fig_trend.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No date column found for trend chart.")

with c2:
    st.subheader("Revenue by Category")
    if "category" in df.columns:
        cat_rev = df.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
        fig_cat = px.pie(cat_rev, names="category", values="revenue", hole=0.45)
        fig_cat.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("No category column found.")

# ----------------------------------------------------------------------
# CHART ROW 2 — Region performance + Top products/salespeople
# ----------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("Revenue by Region")
    if "region" in df.columns:
        reg_rev = df.groupby("region")["revenue"].sum().reset_index().sort_values("revenue", ascending=True)
        fig_reg = px.bar(reg_rev, x="revenue", y="region", orientation="h")
        fig_reg.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(fig_reg, use_container_width=True)
    else:
        st.info("No region column found.")

with c4:
    st.subheader("Top Salespeople")
    if "salesperson" in df.columns:
        top_sales = df.groupby("salesperson")["revenue"].sum().reset_index().sort_values("revenue", ascending=False).head(8)
        fig_sales = px.bar(top_sales, x="salesperson", y="revenue")
        fig_sales.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(fig_sales, use_container_width=True)
    else:
        st.info("No salesperson column found.")

# ----------------------------------------------------------------------
# DATA TABLE (expandable, keeps the screen single-view by default)
# ----------------------------------------------------------------------
with st.expander("🔍 View raw data"):
    st.dataframe(df, use_container_width=True, height=300)
