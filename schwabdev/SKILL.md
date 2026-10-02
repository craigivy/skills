---
name: schwabdev
description: >-
  Use this skill whenever working with the Charles Schwab API via the Python `schwabdev` library (v4.0.0+) or `schwabdev-context`.
  Triggers on requests involving Schwab API authentication, token management, fetching quotes, historical prices,
  option chains, market hours, placing/modifying/canceling equity and option orders, account balances, positions,
  real-time WebSocket streaming (Level 1 equities/options/futures, order books, account activity), and algorithmic
  trading workflows with Trader Context (backtesting strategies on 1-min candles, paper trading, live strategy deployment,
  market data recording, and interactive equity curve charting).
---

# Schwabdev Python SDK Skill

A comprehensive guide and reference for integrating and operating the [Schwabdev](https://github.com/tylerebowers/Schwabdev) Python library and [Schwabdev-Context](https://github.com/tylerebowers/Schwabdev-Context) submodule to interact with the Charles Schwab Trader API.

---

## 1. Quick Reference & Core Workflow

### Installation & Prerequisites
```bash
pip install schwabdev
# For algorithmic backtesting & live strategy deployment (Trader Context):
pip install schwabdev[context]
# For asynchronous client support (ClientAsync / StreamAsync):
pip install aiohttp
# For token database encryption:
pip install cryptography
```

> [!IMPORTANT]
> **Schwab Developer Account Prerequisites:**
> 1. Developer App status must be **"Ready for use"** on [developer.schwab.com](https://developer.schwab.com/dashboard/apps) (status "Approved - Pending" will fail).
> 2. Ensure **both** API products are added to your app: **"Accounts and Trading Production"** AND **"Market Data Production"**.
> 3. Callback URL in Developer Portal should be `https://127.0.0.1` (or specify custom port `https://127.0.0.1:7777`).
> 4. **Thinkorswim (TOS)** must be enabled on your Schwab brokerage account to allow trading and order endpoints.
> 5. Requires **Python 3.11+**. On macOS, run `Install Certificates.command` if SSL verification issues occur.

---

## 2. Client Initialization Patterns

### Standard Synchronous Client
```python
import os
import schwabdev
from dotenv import load_dotenv

load_dotenv()

client = schwabdev.Client(
    app_key=os.getenv("SCHWAB_APP_KEY"),
    app_secret=os.getenv("SCHWAB_APP_SECRET"),
    callback_url=os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1"),
    tokens_db="~/.schwabdev/tokens.db",  # Default location
    encryption=os.getenv("SCHWAB_ENCRYPTION_KEY"),  # Optional Fernet key
    timeout=10,
    open_browser_for_auth=True,
    validate_params=True
)
```

### High-Throughput Asynchronous Client
```python
import asyncio
import schwabdev

async def main():
    async with schwabdev.ClientAsync(
        app_key="YOUR_APP_KEY",
        app_secret="YOUR_APP_SECRET",
        callback_url="https://127.0.0.1",
        parsed=True  # Auto-parse JSON responses to dicts/lists
    ) as client:
        quotes = await client.quotes(["AAPL", "NVDA", "SPY"])
        print(quotes)

asyncio.run(main())
```

### Global Environment Caching
To avoid passing keys in every script on the same machine:
```python
import schwabdev

schwabdev.save_env_global(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    callback_url="https://127.0.0.1"
)
# Now client can be initialized with zero arguments:
client = schwabdev.Client()
```

---

## 3. Core Capabilities Cheatsheet

### A. Market Data & Quotes
```python
# Multiple equity quotes
quotes_resp = client.quotes(["AAPL", "MSFT", "GOOGL"])
if quotes_resp.ok:
    data = quotes_resp.json()

# Single quote
amd_quote = client.quote("AMD").json()

# Historical price bars (period: 1, 5, 10, 15, 30 min, or day/month/year)
history = client.price_history(
    symbol="AAPL",
    periodType="month",
    period=1,
    frequencyType="daily",
    frequency=1
).json()

# Option chains
chains = client.option_chains(
    symbol="SPY",
    contractType="CALL",
    strikeCount=10,
    range="ITM"
).json()

# Option expiration dates
expirations = client.option_expiration_chain("AAPL").json()

# Market hours
hours = client.market_hours(["equity", "option"]).json()
```

### B. Accounts & Positions
```python
# 1. Retrieve account hashes (required for all account-specific calls)
accounts = client.linked_accounts().json()
account_hash = accounts[0]["hashValue"]

# 2. Get account balances & open positions
account_info = client.account_details(account_hash, fields="positions").json()

# 3. View past orders
orders = client.account_orders(
    account_hash=account_hash,
    fromEnteredTime="2026-01-01T00:00:00.000Z",
    toEnteredTime="2026-02-01T00:00:00.000Z"
).json()
```

### C. Order Execution Lifecycle
```python
# 1. Define order payload
order = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "price": "150.00",
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 5,
            "instrument": {
                "symbol": "AAPL",
                "assetType": "EQUITY"
            }
        }
    ]
}

# 2. Preview order first (validation & commission/buying power impact)
preview = client.preview_order(account_hash, order)

# 3. Place order & capture Order ID from 'Location' header
resp = client.place_order(account_hash, order)
if resp.status_code == 201:
    order_id = resp.headers.get("Location", "/").split("/")[-1]
    
    # 4. Check order details
    details = client.order_details(account_hash, order_id).json()
    
    # 5. Cancel or Replace if needed
    # client.cancel_order(account_hash, order_id)
```

### D. Real-Time Streaming
```python
import time
import schwabdev

client = schwabdev.Client()
streamer = schwabdev.Stream(client)

def message_handler(msg):
    print("Received streaming update:", msg)

# Start streamer thread
streamer.start(receiver=message_handler)

# Subscribe to Level 1 Equities (Field 0 is symbol, 1=Bid, 2=Ask, 3=Last, 8=Volume)
streamer.send(streamer.level_one_equities("NVDA,AMD,TSLA", "0,1,2,3,8"))

# Subscribe to account activity notifications
streamer.send(streamer.account_activity())

time.sleep(30)
streamer.stop()
```

### E. Trader Context (Unified Backtest & Live Engine)
```python
from schwabdev import Client, Context, Costs

client = Client()
ctx = Context(client)

# Define unified strategy callable
def my_strategy(tc, events):
    for e in events:
        if e["type"] == "c":  # 1-minute candle
            sym = e["symbol"]
            closes = [c["close"] for c in tc.candles[sym]]
            if len(closes) > 50 and closes[-1] > closes[-2]:
                if tc.sellable(sym) == 0:
                    qty = int(tc.cash * 0.1 / closes[-1])
                    if qty > 0:
                        tc.order({"orderType": "MARKET", "session": "NORMAL", "duration": "DAY",
                                  "orderStrategyType": "SINGLE",
                                  "orderLegCollection": [{"instruction": "BUY", "quantity": qty,
                                                          "instrument": {"symbol": sym, "assetType": "EQUITY"}}]})

# 1. Backtest over 30 days of cached candles with interactive report & chart
run = ctx.backtest(my_strategy, ["AAPL", "NVDA"], cash=10_000, history_days=30, plot=False)
print("Return:", run.stats["net_return"], "Sharpe:", run.stats["sharpe"])

# 2. Deploy same strategy to live data (paper trading mode)
# session = ctx.deploy(my_strategy, ["AAPL", "NVDA"], cash=10_000, plot=True)
```

---

## 4. In-Depth Technical References

For exhaustive schemas, parameter types, response shapes, and best practices, consult the dedicated reference documents:

| Topic | Description | Link |
| :--- | :--- | :--- |
| **Authentication & Tokens** | OAuth flow, automatic token refresh (30 min / 7 days), headless callback handling, token DB encryption | [authentication.md](./references/authentication.md) |
| **REST API Reference** | All 20+ synchronous & asynchronous endpoints, parameters, return formats, pagination | [rest_api.md](./references/rest_api.md) |
| **Streaming Services** | All 13 streamer services (Equities, Options, Books, Charts, Screeners), field decoding map, auto market hours | [streaming.md](./references/streaming.md) |
| **Order Construction** | Market, Limit, Multi-leg Options, Vertical Spreads, Stop Loss, Trailing Stops, OCO / Contingent orders | [orders.md](./references/orders.md) |
| **Trader Context Engine** | Unified backtesting, paper trading, live broker execution, `Costs` model, candle cache, L1/L2 recording | [trader_context.md](./references/trader_context.md) |
| **Troubleshooting & FAQs** | Error code catalog (400, 401, 403, 429, 500), rate limits, TOS configuration, macOS SSL cert fix | [troubleshooting.md](./references/troubleshooting.md) |

---

## 5. Ready-to-Run Examples & Scripts

### Core API & Streaming Examples
- [basic_quotes.py](./examples/basic_quotes.py): Simple starter script for quotes and price history.
- [async_client_demo.py](./examples/async_client_demo.py): High-concurrency async client fetching multiple tickers simultaneously.
- [stream_handler_demo.py](./examples/stream_handler_demo.py): Robust stream processor with automatic field name translation.
- [order_placement.py](./examples/order_placement.py): Full lifecycle order placement, previewing, and cancellation.
- [encrypted_tokens_setup.py](./examples/encrypted_tokens_setup.py): Example setting up encrypted SQLite token storage.

### Trader Context & Strategy Examples
- [sma_backtest_demo.py](./examples/sma_backtest_demo.py): Dual moving average crossover strategy backtested over 30 days with equity stats.
- [live_strategy_demo.py](./examples/live_strategy_demo.py): Live / paper trading deployment with real-time RSI indicators and streaming charts.
- [record_market_data.py](./examples/record_market_data.py): Automated market hours recorder for Level 1, Level 2, and 1-minute candle bars.

### Utility Scripts
- [check_tokens.py](./scripts/check_tokens.py): Utility CLI script to inspect stored token expiration timestamps.
- [auth_callback_server.py](./scripts/auth_callback_server.py): Local HTTPS webserver to automatically intercept and capture OAuth redirect URLs.
