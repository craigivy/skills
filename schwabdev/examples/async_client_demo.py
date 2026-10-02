"""
Asynchronous High-Throughput Client Demo for Schwabdev.
Demonstrates:
- ClientAsync context manager usage
- Auto-parsing JSON responses (parsed=True)
- Concurrent parallel API queries with asyncio.gather
"""

import asyncio
import os
from dotenv import load_dotenv
import schwabdev

load_dotenv()

APP_KEY = os.getenv("SCHWAB_APP_KEY")
APP_SECRET = os.getenv("SCHWAB_APP_SECRET")
CALLBACK_URL = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

async def fetch_stock_snapshot(client: schwabdev.ClientAsync, symbol: str):
    """Fetches quote, fundamentals, and recent price history concurrently."""
    quote_task = client.quote(symbol)
    fund_task = client.instruments(symbol, projection="fundamental")
    history_task = client.price_history(symbol, periodType="day", period=1, frequencyType="minute", frequency=5)

    quote_res, fund_res, hist_res = await asyncio.gather(quote_task, fund_task, history_task)
    return {
        "symbol": symbol,
        "quote": quote_res,
        "fundamentals": fund_res,
        "candles": hist_res.get("candles", []) if isinstance(hist_res, dict) else []
    }

async def main():
    if not APP_KEY or not APP_SECRET:
        print("Please set SCHWAB_APP_KEY and SCHWAB_APP_SECRET.")
        return

    # Use async context manager with parsed=True
    async with schwabdev.ClientAsync(
        app_key=APP_KEY,
        app_secret=APP_SECRET,
        callback_url=CALLBACK_URL,
        parsed=True
    ) as client:
        tickers = ["AAPL", "MSFT", "NVDA", "AMZN", "META"]
        print(f"Fetching snapshots concurrently for: {tickers}")

        tasks = [fetch_stock_snapshot(client, sym) for sym in tickers]
        results = await asyncio.gather(*tasks)

        for res in results:
            sym = res["symbol"]
            quote_dict = res["quote"].get(sym, {}).get("quote", {})
            last_price = quote_dict.get("lastPrice", "N/A")
            num_candles = len(res["candles"])
            print(f"[{sym}] Last Price: ${last_price} | 5-min candles today: {num_candles}")

if __name__ == "__main__":
    asyncio.run(main())
