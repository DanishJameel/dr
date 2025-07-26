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
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data(ticker: str, start: str, end: str):
    return yf.download(ticker, start=start, end=end, interval="1d")

# ========== Fetch Data ==========
ticker = "^NDX"  # NASDAQ 100 Index (used as proxy for US100)
start_date = "2000-01-01"
end_date = input_date + timedelta(days=1)

with st.spinner("🔄 Fetching historical market data..."):
    data = load_data(ticker, start=start_date, end=end_date)

# ========== Data Validation ==========
if data.empty or len(data) < 20:
    st.warning("⚠️ Not enough data available. Please try a different date.")
else:
    # ========== Compute ADR ==========
    data['ADR'] = (data['High'] - data['Low']).rolling(window=14).mean()

    # Select 6 most recent days before the input date
    recent = data[data.index < pd.Timestamp(input_date)].tail(6)
    recent = recent[::-1].reset_index()  # Day 1 (yesterday) to Day 6

    if len(recent) < 6:
        st.warning("⚠️ Not enough previous days for ADR analysis.")
    else:
        # Day 1: yesterday
        day1_range = recent.loc[0, 'High'] - recent.loc[0, 'Low']

        # ADR of Day2 to Day4 (3-day ADR)
        adr_3 = recent.loc[1:3, 'ADR'].mean()

        st.subheader("📈 Yesterday’s Range vs 3-Day ADR")
        st.markdown(f"- **Yesterday’s Range (Day 1)**: `{day1_range:.2f}`")
        st.markdown(f"- **3-Day ADR (Day 2–4)**: `{adr_3:.2f}`")

        if day1_range > adr_3:
            st.error("❌ No Trade Today: Yesterday's range broke the 3-day ADR.")
            
            # Show detailed 5-day ADR table (Day2 to Day6)
            st.subheader("📊 5-Day ADR Table (Day 2–6)")
            st.dataframe(
                recent.loc[1:5][['Date', 'High', 'Low', 'ADR']]
                .rename(columns={"Date": "Day", "High": "High", "Low": "Low", "ADR": "ADR"})
                .style.format({"High": "{:.2f}", "Low": "{:.2f}", "ADR": "{:.2f}"})
            )
        else:
            st.success("✅ Trade Allowed Today: Yesterday's range did NOT break the 3-day ADR.")
