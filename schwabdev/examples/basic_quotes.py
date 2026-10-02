"""
Basic Quotes & Market Data Example for Schwabdev.
Demonstrates:
- Client initialization with environment variables
- Fetching single and multiple stock quotes
- Fetching historical candlestick price bars
- Fetching option chains
"""

import os
import datetime
from dotenv import load_dotenv
import schwabdev

# Load credentials from .env file
load_dotenv()

APP_KEY = os.getenv("SCHWAB_APP_KEY")
APP_SECRET = os.getenv("SCHWAB_APP_SECRET")
CALLBACK_URL = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

if not APP_KEY or not APP_SECRET:
    print("Please configure SCHWAB_APP_KEY and SCHWAB_APP_SECRET in your environment or .env file.")
    exit(1)

# Initialize client
client = schwabdev.Client(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    callback_url=CALLBACK_URL,
    timeout=10
)

# 1. Fetch quotes for multiple tickers
print("--- Fetching Quotes ---")
symbols = ["AAPL", "NVDA", "MSFT"]
resp = client.quotes(symbols)

if resp.ok:
    data = resp.json()
    for symbol in symbols:
        quote_data = data.get(symbol, {}).get("quote", {})
        last_price = quote_data.get("lastPrice")
        net_change = quote_data.get("netChange")
        pct_change = quote_data.get("netPercentChange")
        print(f"{symbol:5s} | Last: ${last_price:<8.2f} | Change: {net_change:+6.2f} ({pct_change:+5.2f}%)")
else:
    print(f"Failed to fetch quotes: {resp.status_code} - {resp.text}")

# 2. Fetch price history (Daily bars for past month)
print("\n--- Price History (SPY - 5 Day 5-Min Candles) ---")
history_resp = client.price_history(
    symbol="SPY",
    periodType="day",
    period=5,
    frequencyType="minute",
    frequency=5,
    needExtendedHoursData=False
)

if history_resp.ok:
    candles = history_resp.json().get("candles", [])
    print(f"Total candles retrieved: {len(candles)}")
    if candles:
        latest = candles[-1]
        dt = datetime.datetime.fromtimestamp(latest["datetime"] / 1000, tz=datetime.timezone.utc)
        print(f"Latest Candle ({dt} UTC): Open=${latest['open']}, High=${latest['high']}, Low=${latest['low']}, Close=${latest['close']}, Volume={latest['volume']}")

# 3. Fetch Option Expiration Dates
print("\n--- Option Expirations (AAPL) ---")
exp_resp = client.option_expiration_chain("AAPL")
if exp_resp.ok:
    expirations = exp_resp.json().get("expirationList", [])
    print("Available expirations:", [e.get("expirationDate") for e in expirations[:5]])
