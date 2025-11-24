import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("📈 Live Stock Market Tracker")


# ----------------------------------------------------
# THEME TOGGLE
# ----------------------------------------------------
theme = st.radio("Theme", ["Light", "Dark"], index=1, horizontal=True)

if theme == "Dark":
    page_bg = "#0E1117"
    text_color = "#FFFFFF"
    widget_bg = "#1E1E1E"
else:
    page_bg = "#FFFFFF"
    text_color = "#000000"
    widget_bg = "#F1F1F1"

# Global Styling
theme_css = f"""
<style>
    .stApp {{
        background-color: {page_bg};
        color: {text_color} !important;
    }}

    .stSelectbox div[data-baseweb="select"], input, textarea {{
        background-color: {widget_bg} !important;
        color: {text_color} !important;
        border-radius: 6px;
    }}

    label, p, span, h1, h2, h3, h4 {{
        color: {text_color} !important;
    }}

    .stCheckbox label {{
        color: {text_color} !important;
    }}

    .stMetric-value, .stMetric-label {{
        color: {text_color} !important;
    }}

    .stButton>button {{
        background-color: {widget_bg};
        color: {text_color} !important;
        border-radius: 6px;
        border: 1px solid gray;
    }}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)


# ----------------------------------------------------
# STOCK LIST
# ----------------------------------------------------
stocks = {
    "Apple (AAPL)": "AAPL",
    "Tesla (TSLA)": "TSLA",
    "Google (GOOGL)": "GOOGL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "Reliance (RELIANCE.NS)": "RELIANCE.NS",
    "TCS (TCS.NS)": "TCS.NS",
    "Infosys (INFY.NS)": "INFY.NS",
}

stock_name = st.selectbox("Select Stock:", list(stocks.keys()))
symbol = stocks[stock_name]

period = st.selectbox("Chart Range:", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y", "max"])
refresh_rate = st.slider("Auto Refresh (seconds):", 5, 120, 15)
show_sma = st.checkbox("Show SMA (20)", True)
show_ema = st.checkbox("Show EMA (20)", True)


# ----------------------------------------------------
# DATA FETCHING
# ----------------------------------------------------
@st.cache_data(ttl=60)
def get_stock(symbol, period):
    return yf.Ticker(symbol).history(period=period)

df = get_stock(symbol, period)
ticker = yf.Ticker(symbol)


# ----------------------------------------------------
# DISPLAY PRICE
# ----------------------------------------------------
if not df.empty:
    price = round(df["Close"].iloc[-1], 2)

    currency = ticker.info.get("currency", "USD")
    symbols = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    currency_symbol = symbols.get(currency, "")

    formatted_price = f"{currency_symbol}{price:,}" if currency_symbol else f"{price:,} {currency}"

    col1, col2 = st.columns(2)
    col1.metric(f"{symbol} Price", formatted_price)
    col2.write(f"🏦 Company: **{ticker.info.get('longName', 'Unknown')}**")
    col2.write(f"💱 Currency: **{currency}**")


# ----------------------------------------------------
# MOVING AVERAGES
# ----------------------------------------------------
if show_sma:
    df["SMA"] = df["Close"].rolling(20).mean()

if show_ema:
    df["EMA"] = df["Close"].ewm(span=20, adjust=False).mean()


# ----------------------------------------------------
# CHART
# ----------------------------------------------------
if not df.empty:
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price"
    ))

    if show_sma:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA"], name="SMA", mode="lines"))

    if show_ema:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA"], name="EMA", mode="lines"))

    fig.update_layout(
        title=f"{symbol} Stock Chart",
        xaxis_rangeslider_visible=True,
        template="plotly_dark" if theme == "Dark" else "plotly",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------
# PRICE ALERTS SYSTEM
# ----------------------------------------------------
st.subheader("🔔 Price Alerts")

if "alerts" not in st.session_state:
    st.session_state.alerts = {}

alert_input = st.number_input("Alert when price goes above:", value=float(price), step=1.0)

if st.button("Add Alert"):
    st.session_state.alerts[symbol] = alert_input
    st.success(f"Alert added: {symbol} → {alert_input}")

# Check & Trigger alerts
if symbol in st.session_state.alerts:
    alert_price = st.session_state.alerts[symbol]
    if price >= alert_price:
        st.warning(f"🚨 ALERT: {symbol} has crossed {alert_price}! Current: {formatted_price}")
        del st.session_state.alerts[symbol]


# ----------------------------------------------------
# AUTO REFRESH
# ----------------------------------------------------
st.write(f"⏳ Refreshing in {refresh_rate} seconds…")
time.sleep(refresh_rate)
st.experimental_rerun()
