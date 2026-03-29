import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# =========================
# FILE PATHS
# =========================
FILES = {
    "mis": "mis_master.xlsx",
    "invoices": "invoices.xlsx",
    "recv_curr": "receivables_current.xlsx",
    "recv_roll": "receivables_rolling_period.xlsx",
    "cod": "cod_outstanding_summary.xlsx",
    "cn_client": "credit_notes_client.xlsx",
    "cn_courier": "credit_notes_courier.xlsx",
    "payables": "payables.xlsx"
}

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=60)
def load_file(path):
    try:
        return pd.read_excel(path)
    except:
        return pd.DataFrame()

data = {k: load_file(v) for k, v in FILES.items()}

# =========================
# SIDEBAR
# =========================
st.sidebar.title("📊 Management Dashboard")

page = st.sidebar.radio("Navigation", [
    "MIS Overview",
    "Invoices",
    "Receivables",
    "COD",
    "Credit Notes - Courier",
    "Credit Notes - Client",
    "Payables"
])

# =========================
# HELPER FUNCTIONS
# =========================

def clean_number(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    ).fillna(0)


def find_row(df, keyword):
    col = df.iloc[:, 0].astype(str).str.strip().str.lower()
    match = df[col.str.contains(keyword, case=False, na=False)]
    if not match.empty:
        return match.iloc[0]
    return None


def get_month_columns(df):
    cols = []
    for col in df.columns:
        try:
            dt = pd.to_datetime(col, errors="coerce")
            if pd.notna(dt):
                cols.append(col)
        except:
            pass
    return cols


# =========================
# MIS OVERVIEW
# =========================
if page == "MIS Overview":

    st.title("📊 MIS Overview")

    df = data["mis"].copy()

    if df.empty:
        st.error("MIS file not found or empty")
        st.stop()

    df.columns = df.columns.map(str)

    # Get month columns
    month_cols = get_month_columns(df)

    if len(month_cols) == 0:
        st.warning("⚠️ No valid month columns found")
        st.stop()

    # Dropdowns
    view_type = st.selectbox("Select View", ["Monthly", "YTD"])

    selected_month = st.selectbox(
        "Select Month",
        month_cols,
        format_func=lambda x: pd.to_datetime(x).strftime("%b-%y")
    )

    # =========================
    # KPI CALCULATION
    # =========================

    revenue_row = find_row(df, "total revenue")
    direct_row = find_row(df, "total direct")
    indirect_row = find_row(df, "total indirect")

    if revenue_row is None:
        st.warning("⚠️ Total Revenue not found")
        revenue_series = pd.Series(0, index=month_cols)
    else:
        revenue_series = clean_number(revenue_row[month_cols])

    if direct_row is None:
        direct_series = pd.Series(0, index=month_cols)
    else:
        direct_series = clean_number(direct_row[month_cols])

    if indirect_row is None:
        indirect_series = pd.Series(0, index=month_cols)
    else:
        indirect_series = clean_number(indirect_row[month_cols])

    # Calculations
    if view_type == "Monthly":
        revenue = revenue_series.get(selected_month, 0)
        direct_cost = direct_series.get(selected_month, 0)
        indirect_cost = indirect_series.get(selected_month, 0)
    else:
        revenue = revenue_series.sum()
        direct_cost = direct_series.sum()
        indirect_cost = indirect_series.sum()

    gross_margin = revenue - direct_cost
    ebitda = gross_margin - indirect_cost

    # =========================
    # KPI CARDS
    # =========================
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Revenue", f"₹ {revenue:,.0f}")
    c2.metric("Direct Cost", f"₹ {direct_cost:,.0f}")
    c3.metric("Indirect Cost", f"₹ {indirect_cost:,.0f}")
    c4.metric("Gross Margin", f"₹ {gross_margin:,.0f}")
    c5.metric("EBITDA", f"₹ {ebitda:,.0f}")

    # =========================
    # BUSINESS MIX
    # =========================
    st.subheader("📊 Business Mix")

    col = df.iloc[:, 0].astype(str).str.strip().str.lower()

    revenue_idx = col[col.str.contains("revenue", na=False)]
    direct_idx = col[col.str.contains("direct expenses", na=False)]

    if revenue_idx.empty or direct_idx.empty:
        st.warning("⚠️ Cannot detect revenue section for mix chart")
    else:
        start = revenue_idx.index[0]
        end = direct_idx.index[0]

        mix_df = df.iloc[start+1:end].copy()

        mix_df = mix_df[
            ~mix_df.iloc[:, 0].astype(str).str.contains("total|less", case=False, na=False)
        ]

        mix_df[selected_month] = clean_number(mix_df[selected_month])

        mix_data = mix_df[[df.columns[0], selected_month]].dropna()
        mix_data.columns = ["Business", "Value"]
        mix_data = mix_data[mix_data["Value"] > 0]

        if mix_data.empty:
            st.info("No data for Business Mix")
        else:
            st.plotly_chart({
                "data": [{
                    "labels": mix_data["Business"],
                    "values": mix_data["Value"],
                    "type": "pie"
                }],
                "layout": {
                    "title": f"Revenue Mix - {pd.to_datetime(selected_month).strftime('%b-%y')}"
                }
            })


# =========================
# OTHER SECTIONS
# =========================
elif page == "Invoices":
    st.title("🧾 Invoices")
    df = data["invoices"]
    st.dataframe(df)


elif page == "Receivables":
    st.title("💰 Receivables")
    df = data["recv_curr"]
    st.dataframe(df)


elif page == "COD":
    st.title("📦 COD")
    df = data["cod"]
    st.dataframe(df)


elif page == "Credit Notes - Courier":
    st.title("📉 Courier Credit Notes")
    st.dataframe(data["cn_courier"])


elif page == "Credit Notes - Client":
    st.title("📉 Client Credit Notes")
    st.dataframe(data["cn_client"])


elif page == "Payables":
    st.title("📤 Payables")
    st.dataframe(data["payables"])
