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
    return pd.read_excel(path)

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
# MIS OVERVIEW
# =========================
if page == "MIS Overview":

    st.title("📊 MIS Overview")

    df = data["mis"].copy()
    df.columns = df.columns.map(str)

    # Identify month columns
    month_cols = [col for col in df.columns if "20" in str(col)]
    month_cols = [str(col) for col in month_cols]

    # Dropdowns
    view_type = st.selectbox("Select View", ["Monthly", "YTD"])
    selected_month = st.selectbox("Select Month", month_cols)

    # =========================
    # KPI FUNCTION
    # =========================
    def get_exact_row(keyword):
        col = df.iloc[:, 0].astype(str).str.strip().str.lower()
        match = df[col.str.contains(keyword, case=False, na=False)]

        if not match.empty:
            row = match.iloc[0][month_cols]
            row = row.astype(str).str.replace(",", "").str.strip()
            return pd.to_numeric(row, errors="coerce").fillna(0)

        return pd.Series([0] * len(month_cols), index=month_cols)

    revenue_series = get_exact_row("total revenue")
    direct_cost_series = get_exact_row("total direct")
    indirect_cost_series = get_exact_row("total indirect")

    # =========================
    # CALCULATIONS
    # =========================
    if view_type == "Monthly":
        revenue = revenue_series[selected_month]
        direct_cost = direct_cost_series[selected_month]
        indirect_cost = indirect_cost_series[selected_month]
    else:
        revenue = revenue_series.sum()
        direct_cost = direct_cost_series.sum()
        indirect_cost = indirect_cost_series.sum()

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

    # Find REVENUE section safely
    revenue_rows = col[col.str.contains("revenue", case=False, na=False)]

    if not revenue_rows.empty:
        start_idx = revenue_rows.index[0]
    else:
        st.error("❌ 'REVENUE' section not found")
        st.stop()

    # Find DIRECT EXPENSES safely
    direct_rows = col[col.str.contains("direct expenses", case=False, na=False)]

    if not direct_rows.empty:
        end_idx = direct_rows.index[0]
    else:
        st.error("❌ 'DIRECT EXPENSES' section not found")
        st.stop()
    mix_df = df.iloc[start_idx + 1:end_idx].copy()

    mix_df = mix_df[~mix_df.iloc[:, 0].str.contains("less|total", case=False, na=False)]

    # Clean numeric values
    mix_df[selected_month] = (
        mix_df[selected_month]
        .astype(str)
        .str.replace(",", "")
        .str.strip()
    )

    mix_df[selected_month] = pd.to_numeric(mix_df[selected_month], errors="coerce")

    mix_data = mix_df[[df.columns[0], selected_month]].dropna()
    mix_data.columns = ["Business", "Value"]

    mix_data = mix_data[mix_data["Value"] > 0]

    # Plot
    st.plotly_chart({
        "data": [{
            "labels": mix_data["Business"],
            "values": mix_data["Value"],
            "type": "pie"
        }],
        "layout": {"title": f"Revenue Mix - {selected_month}"}
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
