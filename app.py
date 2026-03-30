import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# =========================
# LOAD MIS FILE
# =========================
@st.cache_data(ttl=60)
def load_mis():
    try:
        df = pd.read_excel("mis_master.xlsx")
        return df
    except:
        return pd.DataFrame()

df = load_mis()

st.title("📊 MIS Dashboard")

# =========================
# VALIDATION
# =========================
if df.empty:
    st.error("❌ MIS file not found or empty")
    st.stop()

# Clean column names
df.columns = df.columns.map(str).str.strip()

# =========================
# IDENTIFY MONTH COLUMNS
# =========================
month_cols = [col for col in df.columns if "-" in col]

if len(month_cols) == 0:
    st.error("❌ No month columns detected")
    st.write("Columns found:", df.columns.tolist())
    st.stop()

# =========================
# SELECT MONTH
# =========================
selected_month = st.selectbox("Select Month", month_cols)

# =========================
# CLEAN NUMBERS
# =========================
def clean_series(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    ).fillna(0)

# =========================
# FIND ROW FUNCTION
# =========================
def find_row(keyword):
    col = df.iloc[:, 0].astype(str).str.strip().str.lower()
    match = df[col.str.contains(keyword, case=False, na=False)]
    if not match.empty:
        return match.iloc[0]
    return None

# =========================
# KPI CALCULATIONS
# =========================
revenue_row = find_row("total revenue")
direct_row = find_row("direct")
indirect_row = find_row("indirect")

revenue = clean_series(revenue_row[month_cols])[selected_month] if revenue_row is not None else 0
direct_cost = clean_series(direct_row[month_cols])[selected_month] if direct_row is not None else 0
indirect_cost = clean_series(indirect_row[month_cols])[selected_month] if indirect_row is not None else 0

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
direct_idx = col[col.str.contains("direct", na=False)]

if revenue_idx.empty or direct_idx.empty:
    st.warning("⚠️ Could not detect revenue section")
else:
    start = revenue_idx.index[0]
    end = direct_idx.index[0]

    mix_df = df.iloc[start+1:end].copy()

    # Remove totals and adjustments
    mix_df = mix_df[
        ~mix_df.iloc[:, 0].astype(str).str.contains("total|less", case=False, na=False)
    ]

    # Clean numbers
    mix_df[selected_month] = clean_series(mix_df[selected_month])

    mix_data = mix_df[[df.columns[0], selected_month]].dropna()
    mix_data.columns = ["Business", "Value"]

    mix_data = mix_data[mix_data["Value"] > 0]

    if mix_data.empty:
        st.info("No data for mix")
    else:
        st.plotly_chart({
            "data": [{
                "labels": mix_data["Business"],
                "values": mix_data["Value"],
                "type": "pie"
            }],
            "layout": {
                "title": f"Revenue Mix - {selected_month}"
            }
        })