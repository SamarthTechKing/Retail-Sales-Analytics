from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "retail_sales_clean.csv"

st.set_page_config(
    page_title="Retail Intelligence | Sales Performance",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#14213D"
BLUE = "#2563EB"
TEAL = "#0F9D8A"
AMBER = "#F59E0B"
RED = "#DC5353"
MUTED = "#64748B"
PALETTE = ["#2563EB", "#0F9D8A", "#F59E0B", "#8B5CF6", "#E76F51", "#64748B"]


# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    .stApp { background: #F5F7FB; }
    [data-testid="stHeader"] { background: rgba(245,247,251,0.92); }
    [data-testid="stSidebar"] {
        background: #101D35;
        border-right: 1px solid #20314F;
    }
    [data-testid="stSidebar"] * { color: #E7EDF7 !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #1A2A46;
        border-color: #354968;
    }
    [data-testid="stSidebar"] .stDateInput input {
        background: #1A2A46;
        color: #FFFFFF;
        border-color: #354968;
    }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: #14213D; }
    h1 { letter-spacing: -1.3px; font-weight: 800 !important; }
    h2 { letter-spacing: -0.5px; font-weight: 750 !important; }
    .hero {
        background: linear-gradient(115deg, #14213D 0%, #1E3A63 62%, #176B70 100%);
        padding: 27px 32px;
        border-radius: 18px;
        color: white;
        margin: 0 0 24px 0;
        box-shadow: 0 12px 30px rgba(20,33,61,.13);
    }
    .hero-kicker {
        color: #A9D8D4; text-transform: uppercase; letter-spacing: 2px;
        font-size: 11px; font-weight: 700; margin-bottom: 8px;
    }
    .hero-title {
        color: #FFFFFF; font-family: 'Manrope', sans-serif;
        font-size: 29px; font-weight: 800; line-height: 1.2;
    }
    .hero-subtitle { color: #D7E2F0; margin-top: 8px; font-size: 14px; }
    .section-label {
        color: #64748B; text-transform: uppercase; letter-spacing: 1.4px;
        font-size: 11px; font-weight: 700; margin: 7px 0 12px 0;
    }
    .metric-card {
        background: #FFFFFF; border: 1px solid #E7ECF3;
        border-radius: 15px; padding: 17px 18px 15px 18px;
        box-shadow: 0 4px 14px rgba(20,33,61,.045); min-height: 112px;
    }
    .metric-label { color: #64748B; font-size: 12px; font-weight: 600; }
    .metric-value {
        color: #14213D; font-family: 'Manrope', sans-serif;
        font-size: 25px; font-weight: 800; margin-top: 7px;
        white-space: nowrap;
    }
    .metric-note { color: #94A3B8; font-size: 11px; margin-top: 3px; }
    .panel {
        background: #FFFFFF; border: 1px solid #E7ECF3;
        border-radius: 16px; padding: 16px 18px 10px 18px;
        box-shadow: 0 4px 14px rgba(20,33,61,.035);
    }
    .small-note { color: #64748B; font-size: 12px; }
    div[data-testid="stPlotlyChart"] {
        background: #FFFFFF; border: 1px solid #E7ECF3;
        border-radius: 15px; padding: 7px;
        box-shadow: 0 4px 14px rgba(20,33,61,.035);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #E7ECF3; border-radius: 12px; overflow: hidden;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #E9EEF6; border-radius: 9px 9px 0 0;
        padding: 10px 17px; color: #334155; font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background: #FFFFFF !important; color: #1D4ED8 !important; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Data loading and validation
# ---------------------------------------------------------------------
@st.cache_data(show_spinner="Loading retail sales data...")
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    required = {
        "order_date", "country", "category", "sales_channel", "net_sales",
        "quantity", "returned", "order_id", "product", "customer_id",
        "customer_rating",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError("The dataset is missing required columns: " + ", ".join(missing))

    data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")
    data["net_sales"] = pd.to_numeric(data["net_sales"], errors="coerce").fillna(0)
    data["quantity"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0)
    data["customer_rating"] = pd.to_numeric(data["customer_rating"], errors="coerce")
    data["returned"] = data["returned"].astype(str).str.strip().str.title()
    data = data.dropna(subset=["order_date"]).copy()

    for col in ["country", "category", "sales_channel", "product", "customer_id"]:
        data[col] = data[col].fillna("Unknown").astype(str)

    data["month"] = data["order_date"].dt.to_period("M").dt.to_timestamp()
    data["returned_flag"] = data["returned"].eq("Yes").astype(int)
    return data


if not DATA_PATH.exists():
    st.error(
        f"Dataset not found: `{DATA_PATH.name}`. "
        "Place `retail_sales_clean.csv` in the same folder as `app.py`."
    )
    st.stop()

try:
    df = load_data(str(DATA_PATH))
except Exception as exc:
    st.error(f"Unable to load the dataset: {exc}")
    st.stop()

if df.empty:
    st.warning("The dataset contains no usable rows.")
    st.stop()


# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("## RETAIL INTELLIGENCE")
    st.caption("BUSINESS PERFORMANCE SUITE")
    st.markdown("---")
    st.markdown("### Refine your analysis")
    st.caption("Selections update every KPI and visual.")

    countries = sorted(df["country"].unique().tolist())
    categories = sorted(df["category"].unique().tolist())
    channels = sorted(df["sales_channel"].unique().tolist())

    chosen_countries = st.multiselect("🌎 Countries", countries, default=countries)
    chosen_categories = st.multiselect("▦ Product categories", categories, default=categories)
    chosen_channels = st.multiselect("⇄ Sales channels", channels, default=channels)

    min_date = df["order_date"].min().date()
    max_date = df["order_date"].max().date()
    chosen_dates = st.date_input(
        "▣ Order date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("---")
    if st.button("↺ Reset all filters", use_container_width=True):
        st.rerun()
    st.caption(f"Dataset coverage: {min_date:%d %b %Y} – {max_date:%d %b %Y}")
    st.caption(f"{len(df):,} source records")


filtered = df[
    df["country"].isin(chosen_countries)
    & df["category"].isin(chosen_categories)
    & df["sales_channel"].isin(chosen_channels)
].copy()

if isinstance(chosen_dates, (tuple, list)) and len(chosen_dates) == 2:
    start = pd.Timestamp(chosen_dates[0])
    end = pd.Timestamp(chosen_dates[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    filtered = filtered[filtered["order_date"].between(start, end)]

if filtered.empty:
    st.warning("No records match the selected filters. Adjust the filters in the sidebar.")
    st.stop()


# ---------------------------------------------------------------------
# Reusable chart formatting
# ---------------------------------------------------------------------
def polish(fig, height=330):
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=28, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="DM Sans, sans-serif", color="#475569", size=11),
        title=dict(font=dict(family="Manrope, sans-serif", size=15, color=NAVY)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor=NAVY, font_size=12, font_family="DM Sans"),
        xaxis=dict(showgrid=False, linecolor="#E8EDF4", tickfont=dict(color=MUTED)),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", zeroline=False, tickfont=dict(color=MUTED)),
    )
    return fig


def money(value):
    return f"${value:,.0f}"


# ---------------------------------------------------------------------
# Header and KPI cards
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">Business intelligence • Retail sector</div>
      <div class="hero-title">Retail Sales Performance</div>
      <div class="hero-subtitle">
        A unified view of revenue, demand, customer activity and product performance.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

revenue = filtered["net_sales"].sum()
orders = filtered["order_id"].nunique()
units = filtered["quantity"].sum()
aov = revenue / orders if orders else 0
return_rate = filtered["returned_flag"].mean() * 100 if len(filtered) else 0
customers = filtered["customer_id"].nunique()

st.markdown('<div class="section-label">Performance snapshot</div>', unsafe_allow_html=True)
kpis = [
    ("NET REVENUE", money(revenue), "Across selected records"),
    ("ORDERS", f"{orders:,.0f}", "Unique transactions"),
    ("UNITS SOLD", f"{units:,.0f}", "Total quantity"),
    ("AVERAGE ORDER VALUE", money(aov), "Revenue per order"),
    ("RETURN RATE", f"{return_rate:.1f}%", "Share of returned records"),
]
cols = st.columns(5)
for col, (label, value, note) in zip(cols, kpis):
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div>'
            f'<div class="metric-note">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
tab_overview, tab_products, tab_customers, tab_data = st.tabs(
    ["  Overview  ", "  Products & Channels  ", "  Customer & Returns  ", "  Data Explorer  "]
)


# ---------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------
with tab_overview:
    st.markdown("### Revenue overview")
    st.caption("Track sales momentum and understand where revenue is generated.")

    monthly = (
        filtered.groupby("month", as_index=False)
        .agg(revenue=("net_sales", "sum"), orders=("order_id", "nunique"))
        .sort_values("month")
    )
    c1, c2 = st.columns([1.65, 1])
    with c1:
        fig = px.area(
            monthly, x="month", y="revenue",
            title="Monthly revenue trend",
            color_discrete_sequence=[BLUE],
        )
        fig.update_traces(line=dict(width=3), fillcolor="rgba(37,99,235,0.12)")
        fig.update_yaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
        fig.update_xaxes(title="")
        st.plotly_chart(polish(fig, 360), use_container_width=True)
    with c2:
        country = (
            filtered.groupby("country", as_index=False)["net_sales"]
            .sum().sort_values("net_sales", ascending=True)
        )
        fig = px.bar(
            country, x="net_sales", y="country", orientation="h",
            title="Revenue by country", text="net_sales",
            color="net_sales", color_continuous_scale=["#BFD7F7", BLUE],
        )
        fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
        fig.update_xaxes(title="", showticklabels=False, showgrid=False)
        fig.update_yaxes(title="")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(polish(fig, 360), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        category = (
            filtered.groupby("category", as_index=False)["net_sales"]
            .sum().sort_values("net_sales", ascending=False)
        )
        fig = px.pie(
            category, names="category", values="net_sales",
            title="Revenue mix by category", hole=0.62,
            color_discrete_sequence=PALETTE,
        )
        fig.update_traces(textposition="outside", textinfo="percent+label", hole=0.62)
        st.plotly_chart(polish(fig, 340), use_container_width=True)
    with c4:
        channel = (
            filtered.groupby("sales_channel", as_index=False)
            .agg(revenue=("net_sales", "sum"), orders=("order_id", "nunique"))
            .sort_values("revenue", ascending=False)
        )
        fig = px.bar(
            channel, x="sales_channel", y="revenue", title="Sales by channel",
            color="sales_channel", color_discrete_sequence=PALETTE,
            hover_data={"orders": True, "revenue": ":,.2f"},
        )
        fig.update_layout(showlegend=False)
        fig.update_xaxes(title="", tickangle=-12)
        fig.update_yaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
        st.plotly_chart(polish(fig, 340), use_container_width=True)


# ---------------------------------------------------------------------
# Products and channels
# ---------------------------------------------------------------------
with tab_products:
    st.markdown("### Product & channel performance")
    st.caption("Identify leading products and compare the contribution of each sales channel.")

    products = (
        filtered.groupby("product", as_index=False)
        .agg(revenue=("net_sales", "sum"), units=("quantity", "sum"),
             orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .head(12)
    )
    left, right = st.columns([1.3, 1])
    with left:
        fig = px.bar(
            products.sort_values("revenue"), x="revenue", y="product",
            orientation="h", title="Top 12 products by revenue",
            color="revenue", color_continuous_scale=["#BFD7F7", BLUE],
            hover_data={"units": True, "orders": True},
        )
        fig.update_xaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
        fig.update_yaxes(title="")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(polish(fig, 480), use_container_width=True)
    with right:
        fig = px.scatter(
            products, x="units", y="revenue", size="orders", color="product",
            title="Product volume vs revenue", hover_name="product",
            color_discrete_sequence=PALETTE, size_max=35,
        )
        fig.update_xaxes(title="Units sold")
        fig.update_yaxes(title="Revenue ($)", tickprefix="$")
        fig.update_layout(showlegend=False)
        st.plotly_chart(polish(fig, 480), use_container_width=True)

    st.markdown("#### Product performance table")
    display_products = products.copy()
    display_products["revenue"] = display_products["revenue"].map(lambda x: f"${x:,.2f}")
    st.dataframe(display_products, use_container_width=True, hide_index=True)

    channel_detail = (
        filtered.groupby("sales_channel", as_index=False)
        .agg(orders=("order_id", "nunique"), revenue=("net_sales", "sum"),
             units=("quantity", "sum"), avg_order_value=("net_sales", "mean"))
        .sort_values("revenue", ascending=False)
    )
    st.markdown("#### Channel contribution")
    channel_detail["revenue_share"] = channel_detail["revenue"] / revenue * 100 if revenue else 0
    channel_detail["revenue"] = channel_detail["revenue"].map(lambda x: f"${x:,.2f}")
    channel_detail["avg_order_value"] = channel_detail["avg_order_value"].map(lambda x: f"${x:,.2f}")
    channel_detail["revenue_share"] = channel_detail["revenue_share"].map(lambda x: f"{x:.1f}%")
    st.dataframe(channel_detail, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Customers and returns
# ---------------------------------------------------------------------
with tab_customers:
    st.markdown("### Customer experience & returns")
    st.caption("Explore customer ratings, high-value customers and product return patterns.")

    customer_summary = (
        filtered.groupby("customer_id", as_index=False)
        .agg(orders=("order_id", "nunique"), revenue=("net_sales", "sum"),
             avg_rating=("customer_rating", "mean"))
        .sort_values("revenue", ascending=False)
    )
    cat_returns = (
        filtered.groupby("category", as_index=False)
        .agg(return_rate=("returned_flag", "mean"), records=("order_id", "count"))
    )
    cat_returns["return_rate"] *= 100

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            customer_summary.head(10).sort_values("revenue"),
            x="revenue", y="customer_id", orientation="h",
            title="Top 10 customers by revenue",
            color="revenue", color_continuous_scale=["#B7E4D8", TEAL],
            hover_data={"orders": True, "avg_rating": ":.2f"},
        )
        fig.update_xaxes(title="Revenue ($)", tickprefix="$", tickformat=",.0f")
        fig.update_yaxes(title="Customer ID")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(polish(fig, 390), use_container_width=True)
    with right:
        ratings = (
            filtered["customer_rating"].dropna().value_counts()
            .rename_axis("rating").reset_index(name="records").sort_values("rating")
        )
        fig = px.bar(
            ratings, x="rating", y="records", title="Customer rating distribution",
            color="records", color_continuous_scale=["#FDE7B2", AMBER],
            text="records",
        )
        fig.update_traces(textposition="outside")
        fig.update_xaxes(title="Rating")
        fig.update_yaxes(title="Number of records")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(polish(fig, 390), use_container_width=True)

    fig = px.bar(
        cat_returns.sort_values("return_rate", ascending=True),
        x="return_rate", y="category", orientation="h",
        title="Return rate by product category",
        color="return_rate", color_continuous_scale=["#F9D6D6", RED],
        hover_data={"records": True},
    )
    fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
    fig.update_xaxes(title="Return rate (%)", ticksuffix="%", range=[0, max(5, cat_returns["return_rate"].max() * 1.2)])
    fig.update_yaxes(title="")
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(polish(fig, 330), use_container_width=True)

    st.markdown("#### High-value customer detail")
    st.dataframe(customer_summary.head(15), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Data explorer
# ---------------------------------------------------------------------
with tab_data:
    st.markdown("### Filtered data explorer")
    st.caption("Review the records behind the dashboard and export the current selection.")

    summary_cols = st.columns(3)
    summary_cols[0].metric("Filtered records", f"{len(filtered):,}")
    summary_cols[1].metric("Unique customers", f"{customers:,}")
    summary_cols[2].metric("Average customer rating",
                           f"{filtered['customer_rating'].mean():.2f}" if filtered["customer_rating"].notna().any() else "N/A")

    st.dataframe(
        filtered.sort_values("order_date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered records (CSV)",
        data=csv_bytes,
        file_name="retail_sales_filtered.csv",
        mime="text/csv",
        use_container_width=False,
    )

st.markdown("---")
st.markdown(
    '<div class="small-note">Retail Intelligence Dashboard • Interactive analysis based on the selected dataset. '
    'All metrics respond to the sidebar filters.</div>',
    unsafe_allow_html=True,
)
