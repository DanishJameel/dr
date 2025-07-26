import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ========== App Title ==========
st.title("📊 ADR Trading Decision System (US100)")

# ========== User Input ==========
input_date = st.date_input("📅 Date you want to trade on:", datetime.today())

# ========== Download Data ==========
ticker = "^NDX"  # NASDAQ 100 Index
data = yf.download(ticker, start=input_date - timedelta(days=20), end=input_date + timedelta(days=1))

if len(data) < 10:
    st.warning("⚠️ Not enough data. Please select a later date.")
else:
    # ========== Compute ADR ==========
    data['ADR'] = (data['High'] - data['Low']).rolling(window=14).mean()

    # Filter up to the day BEFORE the input date
    recent = data[data.index < pd.Timestamp(input_date)].tail(6)  # Day 1 to Day 6
    recent = recent[::-1].reset_index(drop=True)

    if len(recent) < 6:
        st.warning("⚠️ Not enough historical days for 5-day ADR check.")
    else:
        # Day 1: yesterday
        day1_range = recent.loc[0, 'High'] - recent.loc[0, 'Low']

        # 3-day ADR: from Day2 to Day4
        adr_3 = recent.loc[1:3, 'ADR'].mean()

        st.subheader("📈 Yesterday's Range vs 3-Day ADR")
        st.write(f"**Yesterday's Range (Day 1)**: {day1_range:.2f}")
        st.write(f"**3-Day ADR (Day2–Day4)**: {adr_3:.2f}")

        if day1_range > adr_3:
            st.error("❌ No Trade Today: Yesterday's range broke the 3-day ADR.")
            
            # Show 5-day ADR info
            st.subheader("📊 5-Day ADR Table (Day2–Day6)")
            st.dataframe(recent.loc[1:5][['Date', 'High', 'Low', 'ADR']])
        else:
            st.success("✅ Trade Allowed Today: Yesterday's range did NOT break the 3-day ADR.")
