import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("mis_master.xlsx")
        return df
    except:
        return pd.DataFrame()

df = load_data()

st.title("📊 MIS Dashboard")

if df.empty:
    st.error("❌ File not found or empty")
    st.stop()

# =========================
# CLEAN DATA
# =========================
df.columns = df.columns.str.strip()

# Ensure correct column names
required_cols = ["Month", "Category", "Sub-Category", "Amount"]
if not all(col in df.columns for col in required_cols):
    st.error("❌ Required columns missing. Expected: Month, Category, Sub-Category, Amount")
    st.stop()

# Convert types
df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

# =========================
# FILTERS
# =========================
months = sorted(df["Month"].dropna().unique())

selected_month = st.selectbox(
    "Select Month",
    months,
    format_func=lambda x: x.strftime("%b-%y")
)

# Filter data
df_month = df[df["Month"] == selected_month]

# =========================
# KPI CALCULATIONS
# =========================
revenue = df_month[df_month["Category"] == "Revenue"]["Amount"].sum()
direct_cost = df_month[df_month["Category"] == "Direct Cost"]["Amount"].sum()
indirect_cost = df_month[df_month["Category"] == "Indirect Cost"]["Amount"].sum()

gross_margin = revenue - direct_cost
ebitda = gross_margin - indirect_cost

# =========================
# KPI DISPLAY
# =========================
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Revenue", f"₹ {revenue:,.0f}")
c2.metric("Direct Cost", f"₹ {direct_cost:,.0f}")
c3.metric("Indirect Cost", f"₹ {indirect_cost:,.0f}")
c4.metric("Gross Margin", f"₹ {gross_margin:,.0f}")
c5.metric("EBITDA", f"₹ {ebitda:,.0f}")

# =========================
# BUSINESS MIX (REVENUE)
# =========================
st.subheader("📊 Business Mix")

mix_df = df_month[df_month["Category"] == "Revenue"].copy()

# Remove negative adjustments if needed (optional)
# mix_df = mix_df[mix_df["Amount"] > 0]

mix_grouped = mix_df.groupby("Sub-Category")["Amount"].sum().reset_index()

mix_grouped = mix_grouped[mix_grouped["Amount"] > 0]

if mix_grouped.empty:
    st.info("No data available for business mix")
else:
    st.plotly_chart({
        "data": [{
            "labels": mix_grouped["Sub-Category"],
            "values": mix_grouped["Amount"],
            "type": "pie"
        }],
        "layout": {
            "title": f"Revenue Mix - {selected_month.strftime('%b-%y')}"
        }
    })

# =========================
# OPTIONAL: TABLE VIEW
# =========================
st.subheader("📋 Data Snapshot")
st.dataframe(df_month)