import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ========== App Title ==========
st.set_page_config(page_title="ADR Trade Decision System", layout="centered")
st.title("📊 ADR-Based Trading System (US100 CFD)")

# ========== User Input ==========
input_date = st.date_input("📅 Select the date you want to trade", datetime.today())

# ========== Data Loading Function ==========
@st.cache_data(ttl=3600)
def load_data(ticker: str, start: str, end: str):
    return yf.download(ticker, start=start, end=end, interval="1d")

# ========== Fetch Data ==========
ticker = "^NDX"  # NASDAQ 100 Index (proxy for US100 CFD)
start_date = "2000-01-01"
end_date = input_date + timedelta(days=1)

with st.spinner("🔄 Fetching historical market data..."):
    data = load_data(ticker, start=start_date, end=end_date)

# ========== Validate Data ==========
if data.empty or len(data) < 20:
    st.warning("⚠️ Not enough data available. Please try a different date.")
else:
    data['ADR'] = (data['High'] - data['Low']).rolling(window=14).mean()

    # Get last 6 days before input date
    recent = data[data.index < pd.to_datetime(input_date)].tail(6).copy()

    if len(recent) < 6:
        st.warning("⚠️ Not enough previous days for ADR analysis.")
    else:
        # Reverse the order to Day 1 to Day 6
        recent = recent.iloc[::-1].reset_index()
        if 'Date' not in recent.columns:
            recent = recent.rename(columns={'index': 'Date'})

        try:
            # Scalar values
            high = float(recent.loc[0, 'High'])
            low = float(recent.loc[0, 'Low'])
            adr_3_series = recent.loc[1:3, 'ADR']
            adr_3 = float(adr_3_series.mean()) if not adr_3_series.isnull().any() else None
            day1_range = high - low

            # Format output
            day1_range_fmt = f"{day1_range:.2f}" if pd.notnull(day1_range) else "N/A"
            adr_3_fmt = f"{adr_3:.2f}" if adr_3 is not None else "N/A"

            st.subheader("📈 Yesterday’s Range vs 3-Day ADR")
            st.markdown(f"- **Yesterday’s Range (Day 1)**: `{day1_range_fmt}`")
            st.markdown(f"- **3-Day ADR (Day 2–4)**: `{adr_3_fmt}`")

            if adr_3 is None or pd.isnull(day1_range):
                st.warning("⚠️ ADR or range is missing. Please try another date.")
            elif day1_range > adr_3:
                st.error("❌ No Trade Today: Yesterday's range broke the 3-day ADR.")

                st.subheader("📊 5-Day ADR Table (Day 2–6)")
                table = recent.loc[1:5, ['Date', 'High', 'Low', 'ADR']].copy()
                table['High'] = table['High'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                table['Low'] = table['Low'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                table['ADR'] = table['ADR'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                st.dataframe(table.rename(columns={"Date": "Day"}))
            else:
                st.success("✅ Trade Allowed Today: Yesterday's range did NOT break the 3-day ADR.")

        except Exception as e:
            st.error("🚨 Unexpected error occurred during calculation.")
            st.code(str(e))
