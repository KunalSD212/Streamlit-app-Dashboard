import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")

# =========================
# AUTO REFRESH (IMPORTANT)
# =========================

# =========================
# FILE PATHS (LOCAL / CLOUD)
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
    return pd.read_excel(path)

data = {k: load_file(v) for k, v in FILES.items()}

# =========================
# CLEANING FUNCTIONS
# =========================
def clean_monthly_matrix(df, id_col="Particulars"):
    df = df.copy()
    df = df.dropna(how="all")
    df.columns = df.iloc[1]
    df = df[2:]
    df = df.melt(id_vars=[id_col], var_name="Month", value_name="Amount")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df

# Apply cleaning where needed
try:
    recv_roll = clean_monthly_matrix(data["recv_roll"])
    cn_client = clean_monthly_matrix(data["cn_client"])
    cn_courier = clean_monthly_matrix(data["cn_courier"])
except:
    recv_roll = data["recv_roll"]
    cn_client = data["cn_client"]
    cn_courier = data["cn_courier"]

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
# KPI FUNCTION
# =========================
def kpi(label, value):
    st.metric(label, f"₹ {value:,.0f}")

# =========================
# MIS OVERVIEW
# =========================
if page == "MIS Overview":

    st.title("📊 MIS Overview")

    df = data["mis"].copy()

    # Identify month columns
    month_cols = [col for col in df.columns if "-" in str(col)]

    # Dropdown: Monthly / YTD
    view_type = st.selectbox("Select View", ["Monthly", "YTD"])

    # Select month
    selected_month = st.selectbox("Select Month", month_cols)

    # -------------------------
    # Extract Key Rows
    # -------------------------
    def get_value(label):
        row = df[df.iloc[:,0].astype(str).str.contains(label, case=False, na=False)]
        if not row.empty:
            return row.iloc[0][month_cols]
        return pd.Series([0]*len(month_cols), index=month_cols)

    revenue_series = get_value("Total Revenue")
    direct_cost_series = get_value("Total Direct Expenses")
    indirect_cost_series = get_value("Total Indirect Expenses")

    # -------------------------
    # Monthly vs YTD Logic
    # -------------------------
    if view_type == "Monthly":
        revenue = revenue_series[selected_month]
        direct_cost = direct_cost_series[selected_month]
        indirect_cost = indirect_cost_series[selected_month]
    else:
        revenue = revenue_series.sum()
        direct_cost = direct_cost_series.sum()
        indirect_cost = indirect_cost_series.sum()

    # Calculations
    gross_margin = revenue - direct_cost
    ebitda = gross_margin - indirect_cost

    # -------------------------
    # KPI CARDS
    # -------------------------
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Revenue", f"₹ {revenue:,.0f}")
    c2.metric("Direct Cost", f"₹ {direct_cost:,.0f}")
    c3.metric("Indirect Cost", f"₹ {indirect_cost:,.0f}")
    c4.metric("Gross Margin", f"₹ {gross_margin:,.0f}")
    c5.metric("EBITDA", f"₹ {ebitda:,.0f}")

    # -------------------------
    # PIE CHART
    # -------------------------
    st.subheader("📊 Business Mix")

    exclude_keywords = ["total", "cost", "margin", "ebitda"]

    mix_df = df[~df.iloc[:,0].astype(str).str.lower().str.contains("|".join(exclude_keywords))]

    mix_data = mix_df[[df.columns[0], selected_month]].dropna()
    mix_data.columns = ["Business", "Value"]
    mix_data = mix_data[mix_data["Value"] > 0]

    st.plotly_chart({
        "data": [{
            "labels": mix_data["Business"],
            "values": mix_data["Value"],
            "type": "pie"
        }],
        "layout": {"title": f"Business Mix - {selected_month}"}
    })
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

    st.bar_chart(df.select_dtypes(np.number))

# =========================
# CREDIT NOTES COURIER
# =========================
elif page == "Credit Notes - Courier":
    st.title("📉 Courier Credit Notes")

    st.dataframe(cn_courier)

# =========================
# CREDIT NOTES CLIENT
# =========================
elif page == "Credit Notes - Client":
    st.title("📉 Client Credit Notes")

    st.dataframe(cn_client)

# =========================
# PAYABLES
# =========================
elif page == "Payables":
    st.title("📤 Payables")

    df = data["payables"]

    st.dataframe(df)

    if "Outstanding" in df.columns:
        st.metric("Total Outstanding", f"₹ {df['Outstanding'].sum():,.0f}")
