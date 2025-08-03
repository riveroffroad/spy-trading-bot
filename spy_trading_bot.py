import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import datetime as dt

# ======================
# Load Token
# ======================
def load_token():
    token_path = 'token.json'
    if not os.path.exists(token_path):
        st.warning("Token file 'token.json' not found.")
        return None
    with open(token_path, 'r') as f:
        return json.load(f)

# ======================
# Technical Indicators
# ======================
def calculate_indicators(df):
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['RSI'] = compute_rsi(df['Close'])
    df['UpperBB'], df['LowerBB'] = compute_bollinger_bands(df['Close'])
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_bollinger_bands(series, window=20, num_std=2):
    rolling_mean = series.rolling(window).mean()
    rolling_std = series.rolling(window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, lower_band

# ======================
# Streamlit UI
# ======================
st.set_page_config(page_title="SPY Trading Bot", layout="wide")
st.title("📈 SPY Trading Bot Dashboard")

# Load token (for future use)
token = load_token()

# Simulate SPY data (replace with API or file in future)
@st.cache_data
def get_sample_data():
    dates = pd.date_range(end=dt.datetime.today(), periods=60)
    prices = np.cumsum(np.random.randn(60)) + 4

