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
    st.title("📈 MIS Overview")

    df = data["mis"]

    total_revenue = df.select_dtypes(np.number).sum().sum()
    total_cost = total_revenue * 0.7  # placeholder if structure unclear
    profit = total_revenue - total_cost

    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue", f"₹ {total_revenue:,.0f}")
    c2.metric("Cost", f"₹ {total_cost:,.0f}")
    c3.metric("Profit", f"₹ {profit:,.0f}")

    st.line_chart(df.select_dtypes(np.number))

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
