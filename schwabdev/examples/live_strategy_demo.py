"""
Live & Paper Trading Strategy Deployment Demo with Trader Context.
Demonstrates:
- Deploying the same strategy callable to live streaming data
- Paper trading vs live execution against a real Schwab account
- Enabling live chart viewer and database caching
- Gracefully stopping live session
"""

import os
import time
from dotenv import load_dotenv
import schwabdev

load_dotenv()

def rsi_simple_strategy(tc, events):
    """Simple momentum strategy acting on 1-minute candle events."""
    for event in events:
        if event["type"] != "c":
            continue

        sym = event["symbol"]
        candles = tc.candles.get(sym, [])
        if len(candles) < 15:
            continue

        close_prices = [c["close"] for c in candles[-15:]]
        price_diffs = [close_prices[i] - close_prices[i - 1] for i in range(1, len(close_prices))]
        gains = [d for d in price_diffs if d > 0]
        losses = [-d for d in price_diffs if d < 0]

        avg_gain = sum(gains) / 14 if gains else 0.001
        avg_loss = sum(losses) / 14 if losses else 0.001
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        tc.plots.setdefault(f"RSI {sym}", []).append((event["time"], rsi))
        last_price = close_prices[-1]

        # Oversold (< 30) -> Buy
        if rsi < 30 and tc.sellable(sym) == 0:
            qty = int((tc.cash * 0.10) / last_price)
            if qty > 0:
                print(f"[Signal] RSI Oversold ({rsi:.1f}) -> BUY {qty} shares of {sym}")
                tc.order({
                    "orderType": "MARKET",
                    "session": "NORMAL",
                    "duration": "DAY",
                    "orderStrategyType": "SINGLE",
                    "orderLegCollection": [{"instruction": "BUY", "quantity": qty, "instrument": {"symbol": sym, "assetType": "EQUITY"}}]
                })

        # Overbought (> 70) -> Exit
        elif rsi > 70 and tc.sellable(sym) > 0:
            qty = int(tc.sellable(sym))
            print(f"[Signal] RSI Overbought ({rsi:.1f}) -> SELL {qty} shares of {sym}")
            tc.order({
                "orderType": "MARKET",
                "session": "NORMAL",
                "duration": "DAY",
                "orderStrategyType": "SINGLE",
                "orderLegCollection": [{"instruction": "SELL", "quantity": qty, "instrument": {"symbol": sym, "assetType": "EQUITY"}}]
            })

def main():
    client = schwabdev.Client(
        app_key=os.getenv("SCHWAB_APP_KEY"),
        app_secret=os.getenv("SCHWAB_APP_SECRET"),
        callback_url=os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")
    )

    # 1. Choose Paper Trading or Live Execution
    # For paper trading: account_hash is None (simulated fills on live stream)
    # For real broker execution: pass account_hash from client.linked_accounts().json()
    account_hash = None

    ctx = schwabdev.Context(
        client=client,
        account_hash=account_hash,
        safety=True  # Built-in protection against aberrant order prices
    )

    tickers = ["AAPL", "NVDA"]
    print(f"Deploying Strategy on live stream for {tickers} (Paper Mode)...")

    # 2. Deploy strategy session
    session = ctx.deploy(
        strategy=rsi_simple_strategy,
        tickers=tickers,
        cash=15_000,
        plot=True,          # Opens interactive browser charts at http://localhost:8000
        chart=True,         # Trigger strategy on 1-min candles
        level1=False,       # Set True to receive Level 1 quote deltas
        record=True         # Caches streamed data into SQLite for future backtesting
    )

    print("Live session running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping strategy session...")
    finally:
        ctx.stop()
        print("Session stopped cleanly.")

if __name__ == "__main__":
    main()
