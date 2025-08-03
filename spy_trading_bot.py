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
    df['EMA26'] = df['Close'].ewm(span=26, adjus
