import os
import json
import time
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from tda.auth import easy_client
from tda.client import Client
from textblob import TextBlob
from bs4 import BeautifulSoup
import requests

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN_PATH = os.getenv("TOKEN_PATH", "token.json")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

# Auth setup
client = easy_client(
    api_key=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    token_path=TOKEN_PATH,
)

# App title
st.set_page_config(page_title="SPY Trading Bot", layout="wide")
st.title("📈 SPY Trading Bot Dashboard")

# File paths
STATE_FILE = "bot_state.json"
LOG_FILE = "trade_log.json"

# Load state
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"position": None, "entry_price": 0.0}

# Save state
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Log trades
def log_trade(action, price):
    trade = {
        "action": action,
        "price": price,
        "timestamp": datetime.now().isoformat()
    }
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            trades = json.load(f)
    else:
        trades = []
    trades.append(trade)
    with open(LOG_FILE, "w") as f:
        json.dump(trades, f, indent=4)

# Sentiment analysis
def fetch_news_sentiment(symbol="SPY"):
    url = f"https://finance.yahoo.com/quote/{symbol}?p={symbol}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    headlines = [a.get_text() for a in soup.select("h3")]
    scores = [TextBlob(headline).sentiment.polarity for headline in headlines]
    avg_sentiment = np.mean(scores) if scores else 0
    return avg_sentiment

# Strategy signal
def generate_signal():
    df = client.get_price_history("SPY",
        period_type=Client.PriceHistory.PeriodType.DAY,
        period=Client.PriceHistory.Period.ONE_DAY,
        frequency_type=Client.PriceHistory.FrequencyType.MINUTE,
        frequency=Client.PriceHistory.Frequency.EVERY_MINUTE).json()["candles"]

    prices = pd.DataFrame(df)
    if prices.empty:
        return "HOLD", 0.0

    prices["sma20"] = prices["close"].rolling(window=20).mean()
    prices["sma50"] = prices["close"].rolling(window=50).mean()

    latest = prices.iloc[-1]
    if latest["sma20"] > latest["sma50"]:
        return "BUY", latest["close"]
    elif latest["sma20"] < latest["sma50"]:
        return "SELL", latest["close"]
    return "HOLD", latest["close"]

# Execute trade manually
def execute_signal(action, price):
    state = load_state()
    if action == "BUY" and state["position"] is None:
        st.success(f"Bought SPY at ${price:.2f}")
        state["position"] = "CALL"
        state["entry_price"] = price
        log_trade("BUY", price)
    elif action == "SELL" and state["position"] == "CALL":
        st.warning(f"Sold SPY at ${price:.2f}")
        state["position"] = None
        log_trade("SELL", price)
    else:
        st.info("No action taken.")
    save_state(state)

# Display PnL
def display_pnl():
    state = load_state()
    if state["position"] == "CALL":
        quote = client.get_quote("SPY").json()
        current_price = quote["SPY"]["lastPrice"]
        pnl = current_price - state["entry_price"]
        st.metric("Current PnL", f"${pnl:.2f}")
    else:
        st.write("No active position.")

# Streamlit layout
col1, col2 = st.columns(2)

with col1:
    sentiment = fetch_news_sentiment()
    st.metric("📊 Market Sentiment (Yahoo)", f"{sentiment:.2f}")

    signal, price = generate_signal()
    st.metric("Signal", signal)
    st.metric("Price", f"${price:.2f}")

    if st.button("▶️ Execute Trade"):
        execute_signal(signal, price)

with col2:
    display_pnl()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            trades = json.load(f)
            df = pd.DataFrame(trades)
            st.dataframe(df[::-1])

