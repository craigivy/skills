"""
Simple Moving Average (SMA) Crossover Backtest Demo with Trader Context.
Demonstrates:
- Defining a unified algorithmic strategy: strategy(tc, events)
- Managing portfolio cash and sellable shares
- Adding indicator overlay plots to tc.plots
- Running a 60-day historical backtest on multiple tickers
- Inspecting performance statistics and equity curves
"""

import os
from dotenv import load_dotenv
import schwabdev

load_dotenv()

# Define standard Schwab market order helper
def market_order(symbol: str, instruction: str, quantity: int) -> dict:
    return {
        "orderType": "MARKET",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": instruction,
                "quantity": quantity,
                "instrument": {
                    "symbol": symbol,
                    "assetType": "EQUITY"
                }
            }
        ]
    }

class SMACrossoverStrategy:
    """
    Dual Moving Average Crossover Strategy.
    Fast SMA crossing above Slow SMA generates BUY signal.
    Fast SMA crossing below Slow SMA generates SELL signal.
    """
    def __init__(self, fast_window: int = 50, slow_window: int = 200, position_size_pct: float = 0.15):
        self.fast = fast_window
        self.slow = slow_window
        self.size_pct = position_size_pct

    def __call__(self, tc, events):
        for event in events:
            if event["type"] != "c":  # React to 1-minute candle bars
                continue

            sym = event["symbol"]
            candles = tc.candles.get(sym, [])
            if len(candles) <= self.slow:
                continue

            closes = [c["close"] for c in candles]
            curr_len = len(closes)

            # Compute moving averages
            fast_now = sum(closes[curr_len - self.fast:curr_len]) / self.fast
            slow_now = sum(closes[curr_len - self.slow:curr_len]) / self.slow

            fast_prev = sum(closes[curr_len - self.fast - 1:curr_len - 1]) / self.fast
            slow_prev = sum(closes[curr_len - self.slow - 1:curr_len - 1]) / self.slow

            # Add overlays to visual chart viewer
            tc.plots.setdefault(f"SMA{self.fast} {sym}", []).append((event["time"], fast_now))
            tc.plots.setdefault(f"SMA{self.slow} {sym}", []).append((event["time"], slow_now))

            current_price = closes[-1]

            # Signal 1: Golden Cross -> Buy position slice
            if fast_prev <= slow_prev and fast_now > slow_now:
                shares_to_buy = int((tc.cash * self.size_pct) / current_price)
                if shares_to_buy > 0:
                    tc.order(market_order(sym, "BUY", shares_to_buy))

            # Signal 2: Death Cross -> Exit all held shares
            elif fast_prev >= slow_prev and fast_now < slow_now:
                shares_to_sell = int(tc.sellable(sym))
                if shares_to_sell > 0:
                    tc.order(market_order(sym, "SELL", shares_to_sell))

def main():
    # Initialize client (uses ~/.schwabdev/env.json if available, or .env)
    client = schwabdev.Client(
        app_key=os.getenv("SCHWAB_APP_KEY"),
        app_secret=os.getenv("SCHWAB_APP_SECRET"),
        callback_url=os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")
    )

    ctx = schwabdev.Context(client, cache_db="~/.schwabdev/candles.db")
    tickers = ["AAPL", "NVDA", "AMD", "MSFT"]

    print(f"Starting SMA Crossover Backtest on: {tickers}...")
    strategy = SMACrossoverStrategy(fast_window=20, slow_window=50, position_size_pct=0.20)

    # Run 30-day backtest
    run = ctx.backtest(
        strategy=strategy,
        tickers=tickers,
        cash=20_000,
        history_days=30,
        chart=True,
        fill_delay=2,
        report=True,
        plot=False  # Set to True to open live browser chart viewer
    )

    print("\n--- Key Performance Metrics ---")
    print(f"Net Return:       {run.stats.get('net_return', 0.0) * 100:.2f}%")
    print(f"Realized P&L:     ${run.stats.get('realized_pnl', 0.0):,.2f}")
    print(f"Max Drawdown:     {run.stats.get('max_drawdown', 0.0) * 100:.2f}%")
    print(f"Total Fees Paid:  ${run.stats.get('fees_paid', 0.0):.2f}")

if __name__ == "__main__":
    main()
