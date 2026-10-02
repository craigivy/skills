# Trader Context (Backtesting & Live Strategy Engine) Reference

The `schwabdev.Context` (or `from schwabdev import Context, Costs`, installed via `pip install schwabdev[context]`) module provides a unified execution engine for developing, backtesting, paper-trading, and live-deploying algorithmic trading strategies with identical strategy code.

---

## 1. Overview & Architecture

```
                       ┌─────────────────────────────────────────┐
                       │           Unified Strategy              │
                       │          strategy(tc, events)           │
                       └────────────────────┬────────────────────┘
                                            │
                   ┌────────────────────────┼────────────────────────┐
                   ▼                        ▼                        ▼
        ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
        │  ctx.backtest(...)  │  │   ctx.deploy(...)   │  │   ctx.deploy(...)   │
        │   (Backtest Mode)   │  │ (Live Paper Trading)│  │ (Live Broker Orders)│
        └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘
                   │                        │                        │
         Cached SQLite Candles         Live Schwab Websocket    Live Schwab Websocket
          + Cost/Slippage Model        + Simulated Execution    + Real Schwab Order API
```

### Installation
```bash
pip install schwabdev[context]
# Or directly install both:
pip install schwabdev schwabdev-context
```

### Core Limitations
- **Equities Only**: Supports single-leg equity orders (whole shares only). Options and futures are not yet supported in Context.
- **Order Types**: Supports `MARKET`, `LIMIT`, and `STOP` orders with `BUY` and `SELL` instructions.
- **Candle Resolution**: 1-minute OHLCV bars.
- **Historical Level 1/2 Data**: Schwab's API does not provide historical Level 1 quotes or Level 2 order book data; backtesting against L1/L2 requires capturing them first using `ctx.record(...)`.

---

## 2. Strategy Definition

A strategy is any callable object or function matching the signature `strategy(tc, events)`.

```python
def my_strategy(tc, events):
    for e in events:
        if e["type"] != "c":  # Act only on candle events
            continue
        
        sym = e["symbol"]
        candles = tc.candles[sym]
        if len(candles) < 20:
            continue
            
        current_close = candles[-1]["close"]
        # Make trading decisions using tc
        if current_close > 150.0 and tc.sellable(sym) == 0:
            qty = int(tc.cash * 0.10 / current_close)
            if qty > 0:
                tc.order({
                    "orderType": "MARKET",
                    "session": "NORMAL",
                    "duration": "DAY",
                    "orderStrategyType": "SINGLE",
                    "orderLegCollection": [{
                        "instruction": "BUY",
                        "quantity": qty,
                        "instrument": {"symbol": sym, "assetType": "EQUITY"}
                    }]
                })
```

### Event Payload Types (`events`)

`events` is a list of market events that occurred on the current tick:

| `type` | Description | Event Dictionary Shape |
| :--- | :--- | :--- |
| `"c"` | 1-Minute Candle | `{"symbol": str, "time": int, "open": float, "high": float, "low": float, "close": float, "volume": int, "type": "c"}` |
| `"l1"` | Level-1 Quote Delta | `{"symbol": str, "time": int, "bid": float, "ask": float, "last": float, "bid_size": int, "ask_size": int, "type": "l1"}` |
| `"l2"` | Level-2 Order Book | `{"symbol": str, "time": int, "bids": list[tuple], "asks": list[tuple], "type": "l2"}` |

> [!NOTE]
> `time` is Unix milliseconds. Level-1 events deliver deltas (unchanged fields arrive as `None`). Access the fully merged latest quote via `tc.quotes[symbol]` rather than parsing deltas manually.

---

## 3. Trader Context (`tc`) Interface

Inside the strategy, `tc` provides full access to market state, portfolio state, order routing, and chart plotting:

### Reading State

| Attribute / Method | Description |
| :--- | :--- |
| `tc.candles[symbol]` | List of candle dicts up to the current tick. Latest candle is `tc.candles[symbol][-1]`. |
| `tc.quotes[symbol]` | Latest merged Level 1 quote dict (`bid`, `ask`, `last`, `bid_size`, `ask_size`). |
| `tc.books[symbol]` | Latest Level 2 order book snapshot (`bids`, `asks`). |
| `tc.positions[symbol]` | Number of shares currently held for `symbol` (float; absent if flat). |
| `tc.cash` | Spendable cash = Settled cash minus cash reserved by open BUY limit orders. |
| `tc.sellable(symbol)` | Shares available to sell = Owned shares minus shares committed to open SELL limit orders. |
| `tc.portfolio_value()` | Total portfolio valuation (settled cash + all open positions marked to latest close). |
| `tc.starting_cash` | Initial capital assigned at the start of the run. |
| `tc.orders` | Nested dict of all orders: `symbol -> order_id -> record`. |

### Actions

| Method | Description |
| :--- | :--- |
| `tc.order(order_dict)` | Submits an order dictionary (Schwab format). Returns assigned `order_id`. |
| `tc.cancel(order_id)` | Cancels a resting open order. Returns `True` if cancellation initiated. |
| `tc.plots[overlay_name]` | Appends `(timestamp_ms, value)` tuples to render visual indicators on the interactive chart. |

> **Overlay Plot Naming**:
> - If `overlay_name` includes a ticker (e.g. `"SMA50 AAPL"`), it plots specifically on that ticker's panel.
> - If `overlay_name` has no ticker (e.g. `"Global_Benchmark"`), it renders on every ticker panel.

---

## 4. Backtesting Engine (`ctx.backtest`)

```python
from schwabdev import Client, Context, Costs

client = Client()  # Used to fetch candle history from Schwab on the first run
ctx = Context(client, cache_db="~/.schwabdev/candles.db")

run = ctx.backtest(
    strategy=my_strategy,
    tickers=["NVDA", "AMD", "MSFT"],
    history_days=60,
    cash=25_000,
    chart=True,          # Strategy wakes on candle events
    level1=False,        # Strategy wakes on L1 events (requires recorded data)
    level2=False,        # Strategy wakes on L2 events (requires recorded data)
    fill_delay=2,        # Market orders wait N bars before filling at bar open
    costs=Costs(pct=0.0005, half_spread=0.0001, slip=0.0001),
    report=True,         # Prints summary report in terminal
    plot=False           # Set True to open browser chart viewer
)
```

### Simulated Fills & Execution Model
- **MARKET Orders**: Fill at the open price of the candle `fill_delay` bars after placement (default: 2 bars).
- **LIMIT Orders**: Rest in the order book until a future candle's price touches or crosses the limit; fills at the limit price.
- **STOP Orders**: Trigger when a bar's price breaks the stop price; fills at the stop price or bar open if price gapped.
- **FIFO Accounting**: Closed trades are matched First-In-First-Out at the individual share level, properly handling partial fills, scaling in, and scaling out.

### Transaction Cost Model (`Costs`)
```python
costs = Costs(
    flat=0.0,                  # Fixed dollar fee per trade
    per_share=0.0,             # Dollar fee per share
    pct=0.0005,                # 0.05% of trade notional value
    half_spread=0.0001,        # Half bid-ask spread penalty
    slip=0.0001,               # Slippage factor
    sec_fee=20.60e-6,          # Regulatory SEC fee (sells only)
    taf_per_share=0.000195     # FINRA TAF fee (sells only)
)
```

### Backtest Results & Inspection
```python
# Access performance metrics dictionary
print(run.stats["net_return"])     # e.g. 0.142 (14.2%)
print(run.stats["sharpe"])         # Sharpe ratio
print(run.stats["max_drawdown"])   # Maximum peak-to-trough drawdown
print(run.stats["realized_pnl"])   # Realized dollar profit/loss
print(run.stats["fees_paid"])      # Total simulated fees paid

# Equity curve (list of (time, portfolio_value))
equity_curve = run.equity

# Display interactive chart
run.serve(port=8000)  # Non-blocking web server
# run.plot()          # Blocking chart display
```

---

## 5. Live & Paper Deployment (`ctx.deploy`)

```python
# Paper Trading Mode (Default when no account_hash is provided)
ctx_paper = Context(client)
session = ctx_paper.deploy(
    strategy=my_strategy,
    tickers=["AAPL", "TSLA"],
    cash=10_000,
    plot=True,          # Opens live streaming browser chart
    chart=True,
    record=True         # Caches incoming live stream to DB for future backtesting
)

# Live Broker Orders Mode (Real execution on Charles Schwab)
account_hash = client.linked_accounts().json()[0]["hashValue"]
ctx_live = Context(
    client=client,
    account_hash=account_hash,
    safety=True         # Protects against runaway orders (>5% away from recent OHLC)
)
live_session = ctx_live.deploy(
    strategy=my_strategy,
    tickers=["AAPL"],
    sync_positions=True # Adopts existing account positions into tc.positions
)

# To stop any active live/paper session:
# ctx_live.stop()
```

### Safety Guard Mechanism (`safety=True`)
In live or paper mode, the built-in safety check intercepts orders priced dangerously far from current market conditions:
- **BUY** orders priced > 5% above the recent candle high are rejected.
- **SELL** orders priced > 5% below the recent candle low are rejected.

---

## 6. Recording Live Market Data (`ctx.record`)

Schwab does not offer historical Level 1 quote or Level 2 book archives. Capture and store live streaming data locally for high-fidelity backtesting:

```python
from schwabdev import Client, Context

client = Client()
ctx = Context(client, cache_db="~/.schwabdev/recorded_data.db")

# Records Level 1, Level 2, and 1-minute candles automatically during market hours
streamer = ctx.record(
    tickers=["NVDA", "AMD", "SPY"],
    chart=True,
    level1=True,
    level2=True,
    verbose=True
)
```

Recorded data is persisted to SQLite and seamlessly replayed in future backtests:
```python
# Backtest replaying exact captured Level 1 quotes and order books
run = ctx.backtest(
    my_l2_strategy,
    tickers=["NVDA"],
    history_days=5,
    chart=True,
    level1=True,
    level2=True
)
```
