"""
Market Data Recording Utility for Schwabdev Trader Context.
Demonstrates:
- Capturing Level 1 quotes, Level 2 order books, and 1-minute chart candles
- Caching streaming data into SQLite for offline backtesting
- Automatically aligning with market operating hours
"""

import os
import time
from dotenv import load_dotenv
import schwabdev

load_dotenv()

def main():
    client = schwabdev.Client(
        app_key=os.getenv("SCHWAB_APP_KEY"),
        app_secret=os.getenv("SCHWAB_APP_SECRET"),
        callback_url=os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")
    )

    db_path = "~/.schwabdev/market_history.db"
    ctx = schwabdev.Context(client, cache_db=db_path)

    tickers = ["AAPL", "NVDA", "AMD", "TSLA", "SPY", "QQQ"]
    print(f"Starting automatic market data recorder for: {tickers}")
    print(f"Data will be saved to: {db_path}")

    # Starts recording using start_auto (activates at market open 9:29 AM ET, stops at 4:00 PM ET)
    streamer = ctx.record(
        tickers=tickers,
        chart=True,     # Record 1-minute candles
        level1=True,    # Record Level 1 quote changes
        level2=True,    # Record Level 2 order book snapshots
        verbose=True
    )

    print("Recorder running. Leave this process active during market hours (Ctrl+C to stop).")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping data recording...")
    finally:
        ctx.stop()
        print("Market data recording stopped.")

if __name__ == "__main__":
    main()
