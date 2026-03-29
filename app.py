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
def load_file(path, sheet=None):
    try:
        return pd.read_excel(path, sheet_name=sheet)
    except:
        return pd.DataFrame()

data = {
    "mis": load_file(FILES["mis"], sheet="MIS_DATA"),
    "invoices": load_file(FILES["invoices"]),
    "recv_curr": load_file(FILES["recv_curr"]),
    "recv_roll": load_file(FILES["recv_roll"]),
    "cod": load_file(FILES["cod"]),
    "cn_client": load_file(FILES["cn_client"]),
    "cn_courier": load_file(FILES["cn_courier"]),
    "payables": load_file(FILES["payables"])
}

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
# MIS OVERVIEW (FINAL CLEAN VERSION)
# =========================
if page == "MIS Overview":

    st.title("📊 MIS Overview")

    df = data["mis"].copy()

    if df.empty:
        st.error("❌ MIS_DATA sheet not found or empty")
        st.stop()

    # =========================
    # DATA CLEANING
    # =========================
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

    df["Category"] = df["Category"].astype(str).str.strip()
    df["Subcategory"] = df["Subcategory"].astype(str).str.strip()

    df["Month"] = df["Date"].dt.strftime("%b-%y")

    # =========================
    # FILTERS
    # =========================
    months = sorted(df["Month"].dropna().unique())

    view_type = st.selectbox("Select View", ["Monthly", "YTD"])

    selected_month = st.selectbox("Select Month", months)

    if view_type == "Monthly":
        df_filtered = df[df["Month"] == selected_month]
    else:
        df_filtered = df[df["Month"] <= selected_month]

    # =========================
    # CALCULATIONS
    # =========================
    revenue = df_filtered[df_filtered["Category"] == "Revenue"]["Amount"].sum()
    direct_cost = df_filtered[df_filtered["Category"] == "Direct Cost"]["Amount"].sum()
    indirect_cost = df_filtered[df_filtered["Category"] == "Indirect Cost"]["Amount"].sum()

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

    mix_df = df_filtered[df_filtered["Category"] == "Revenue"]

    if mix_df.empty:
        st.info("No revenue data available")
    else:
        st.plotly_chart({
            "data": [{
                "labels": mix_df["Subcategory"],
                "values": mix_df["Amount"],
                "type": "pie"
            }],
            "layout": {
                "title": f"Revenue Mix - {selected_month}"
            }
        })

    # =========================
    # MONTHLY TREND (BONUS)
    # =========================
    st.subheader("📈 Revenue Trend")

    trend_df = df.groupby("Month")["Amount"].sum().reset_index()

    st.line_chart(trend_df.set_index("Month"))

# =========================
# INVOICES
# =========================
elif page == "Invoices":

    st.title("🧾 Invoices")
    df = data["invoices"]

    st.dataframe(df)

    if "Invoice Amount" in df.columns:
        st.bar_chart(df.groupby("Client Name")["Invoice Amount"].sum())

# =========================
# RECEIVABLES
# =========================
elif page == "Receivables":

    st.title("💰 Receivables")
    df = data["recv_curr"]

    st.dataframe(df)

    if "Outstanding" in df.columns:
        st.metric("Total Outstanding", f"₹ {df['Outstanding'].sum():,.0f}")

# =========================
# COD
# =========================
elif page == "COD":

    st.title("📦 COD Dashboard")
    df = data["cod"]

    st.dataframe(df)

    numeric_cols = df.select_dtypes(include=np.number)

    if not numeric_cols.empty:
        st.bar_chart(numeric_cols)

# =========================
# CREDIT NOTES COURIER
# =========================
elif page == "Credit Notes - Courier":

    st.title("📉 Courier Credit Notes")
    st.dataframe(data["cn_courier"])

# =========================
# CREDIT NOTES CLIENT
# =========================
elif page == "Credit Notes - Client":

    st.title("📉 Client Credit Notes")
    st.dataframe(data["cn_client"])

# =========================
# PAYABLES
# =========================
elif page == "Payables":

    st.title("📤 Payables")
    df = data["payables"]

    st.dataframe(df)

    if "Outstanding" in df.columns:
        st.metric("Total Outstanding", f"₹ {df['Outstanding'].sum():,.0f}")
