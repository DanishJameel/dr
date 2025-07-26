import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
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

    # Filter for days before the selected date, take last 6, reverse order
    mask = data.index < pd.to_datetime(input_date)
    recent = data[mask].tail(6).copy()
    recent = recent.iloc[::-1].reset_index()  # Day 1 (yesterday) to Day 6

    # Ensure correct column names after reset_index
    if 'Date' not in recent.columns:
        recent = recent.rename(columns={'index': 'Date'})

    if len(recent) < 6:
        st.warning("⚠️ Not enough previous days for ADR analysis.")
        st.info("Check if the selected date is a weekend, holiday, or too close to the start date.")
    else:
        # Access Day 1 values safely
        try:
            high = float(recent.loc[0, 'High'])
            low = float(recent.loc[0, 'Low'])
            adr_3 = recent.loc[1:3, 'ADR'].mean()

            # Compute Range
            day1_range = high - low

            # Formatted Display
            st.subheader("📈 Yesterday’s Range vs 3-Day ADR")
            st.markdown(f"- **Yesterday’s Range (Day 1)**: `{day1_range:.2f}`")
            st.markdown(f"- **3-Day ADR (Day 2–4)**: `{adr_3:.2f}`")

            # Logic Decision
            if day1_range > adr_3:
                st.error("❌ No Trade Today: Yesterday's range broke the 3-day ADR.")

                # Detailed ADR table (Day 2–6)
                st.subheader("📊 5-Day ADR Table (Day 2–6)")
                table = recent.loc[1:5, ['Date', 'High', 'Low', 'ADR']].copy()
                table['High'] = table['High'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                table['Low'] = table['Low'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                table['ADR'] = table['ADR'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                st.dataframe(table.rename(columns={"Date": "Day"}))

            else:
                st.success("✅ Trade Allowed Today: Yesterday's range did NOT break the 3-day ADR.")

        except Exception as e:
            st.warning("⚠️ Data for required range or ADR is missing or invalid.")
            st.error(f"Details: {e}")
