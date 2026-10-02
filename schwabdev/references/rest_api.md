# REST API Reference

The `schwabdev.Client` (synchronous) and `schwabdev.ClientAsync` (asynchronous) classes expose all Charles Schwab Trader API REST endpoints.

---

## 1. Accounts & Balances

### `linked_accounts()`
Retrieves account numbers and their corresponding encrypted hash values (`hashValue`). The hash value is required for all account-specific endpoints.

- **Returns**: `requests.Response` (or `list[dict]` in `ClientAsync(parsed=True)`)
```python
resp = client.linked_accounts()
accounts = resp.json()
# [{'accountNumber': '12345678', 'hashValue': 'A1B2C3D4E5F6...'}]
account_hash = accounts[0]["hashValue"]
```

---

### `account_details_all(fields=None)`
Retrieves balances and details for all linked accounts.

- **Parameters**:
  - `fields (str | None)`: Pass `"positions"` to include current holdings/positions in each account.
- **Example**:
```python
resp = client.account_details_all(fields="positions")
```

---

### `account_details(accountHash, fields=None)`
Retrieves balances and positions for a specific account hash.

- **Parameters**:
  - `accountHash (str)`: The encrypted account identifier from `linked_accounts()`.
  - `fields (str | None)`: Pass `"positions"` to include open positions.
- **Example**:
```python
resp = client.account_details(account_hash, fields="positions")
data = resp.json()
cash_available = data["securitiesAccount"]["currentBalances"]["cashAvailableForTrading"]
positions = data["securitiesAccount"].get("positions", [])
```

---

### `preferences()`
Retrieves user preferences for the linked Schwab profile (default account, display settings, stream configuration).

```python
prefs = client.preferences().json()
```

---

## 2. Market Data & Quotes

### `quotes(symbols, fields=None, indicative=False)`
Fetches real-time market quotes for one or more symbols.

- **Parameters**:
  - `symbols (list[str] | str)`: List of symbols `["AAPL", "TSLA"]` or comma-separated string `"AAPL,TSLA"`.
  - `fields (str | None)`: Optional subset: `"quote"`, `"fundamental"`, `"extended"`, `"reference"`, `"regular"`.
  - `indicative (bool)`: Returns indicative quotes for options/indexes.
- **Example**:
```python
quotes = client.quotes(["NVDA", "AMD", "MSFT"]).json()
nvda_last = quotes["NVDA"]["quote"]["lastPrice"]
```

---

### `quote(symbol_id, fields=None)`
Convenience method for fetching a single symbol quote.

```python
aapl_quote = client.quote("AAPL").json()
```

---

### `option_chains(symbol, ...)`
Fetches complete option chains with extensive filtering parameters.

- **Parameters**:
  - `symbol (str)`: Underlying symbol (e.g. `"SPY"`).
  - `contractType (str | None)`: `"CALL"`, `"PUT"`, or `"ALL"` (default).
  - `strikeCount (int | None)`: Number of strikes above and below current price.
  - `includeUnderlyingQuote (bool | None)`: Include underlying stock quote.
  - `strategy (str | None)`: `"SINGLE"`, `"COVERED"`, `"VERTICAL"`, `"CALENDAR"`, `"STRADDLE"`, `"STRANGLE"`, `"BUTTERFLY"`, `"CONDOR"`, `"DIAGONAL"`, `"COLLAR"`, `"ROLL"`.
  - `interval (float | None)`: Strike price interval for spread strategies.
  - `strike (float | None)`: Specific strike price.
  - `range (str | None)`: `"ITM"` (in-the-money), `"NTM"` (near-the-money), `"OTM"` (out-of-the-money), `"SAK"` (strikes above market), `"SBK"` (strikes below market), `"SNK"` (strikes near market), `"ALL"`.
  - `fromDate (datetime | str | None)`: Expiration start date (`YYYY-MM-DD`).
  - `toDate (datetime | str | None)`: Expiration end date (`YYYY-MM-DD`).
  - `volatility (float | None)`: Volatility calculation base.
  - `underlyingPrice (float | None)`: Override underlying price.
  - `interestRate (float | None)`: Override interest rate.
  - `daysToExpiration (int | None)`: Filter by days to expiration.
  - `expMonth (str | None)`: `"JAN"`, `"FEB"`, `"MAR"`, `"APR"`, `"MAY"`, `"JUN"`, `"JUL"`, `"AUG"`, `"SEP"`, `"OCT"`, `"NOV"`, `"DEC"`, or `"ALL"`.
  - `optionType (str | None)`: `"S"` (Standard), `"NS"` (Non-standard), `"ALL"`.
- **Example**:
```python
chain = client.option_chains(
    symbol="AAPL",
    contractType="CALL",
    strikeCount=5,
    range="OTM"
).json()
```

---

### `option_expiration_chain(symbol)`
Fetches list of available expiration dates for the given underlying symbol.

```python
exp_dates = client.option_expiration_chain("TSLA").json()
```

---

### `price_history(symbol, periodType=None, period=None, frequencyType=None, frequency=None, startDate=None, endDate=None, needExtendedHoursData=None, needPreviousClose=None)`
Retrieves historical OHLCV candle bars.

- **Parameters**:
  - `symbol (str)`: Ticker symbol.
  - `periodType (str | None)`: `"day"`, `"month"`, `"year"`, `"ytd"`.
  - `period (int | None)`: Number of periods. Valid pairings with `periodType`:
    - `day`: `1, 2, 3, 4, 5, 10`
    - `month`: `1, 2, 3, 6`
    - `year`: `1, 2, 3, 5, 10, 15, 20`
    - `ytd`: `1`
  - `frequencyType (str | None)`: `"minute"`, `"daily"`, `"weekly"`, `"monthly"`.
  - `frequency (int | None)`:
    - If `minute`: `1, 5, 10, 15, 30`
    - If `daily`: `1`
    - If `weekly`: `1`
    - If `monthly`: `1`
  - `startDate (datetime | str | int | None)`: Epoch ms or datetime object.
  - `endDate (datetime | str | int | None)`: Epoch ms or datetime object.
  - `needExtendedHoursData (bool | None)`: `True` to include pre/post market.
  - `needPreviousClose (bool | None)`: `True` to include previous close price.
- **Example**:
```python
import datetime

# 5-minute candles for the last 5 days
history = client.price_history(
    symbol="SPY",
    periodType="day",
    period=5,
    frequencyType="minute",
    frequency=5,
    needExtendedHoursData=True
).json()
candles = history["candles"]  # [{'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ..., 'datetime': ...}]
```

---

### `movers(symbol, sort=None, frequency=None)`
Fetches top market movers for an index.

- **Parameters**:
  - `symbol (str)`: Index symbol (`"$DJI"`, `"$COMPX"`, `"$SPX"`).
  - `sort (str | None)`: `"VOLUME"`, `"TRADES"`, `"PERCENT_CHANGE_UP"`, `"PERCENT_CHANGE_DOWN"`.
  - `frequency (int | None)`: Frequency in minutes (0, 1, 5, 10, 30, 60).
- **Example**:
```python
spx_gainers = client.movers("$SPX", sort="PERCENT_CHANGE_UP").json()
```

---

### `market_hours(symbols, date=None)` / `market_hour(market_id, date=None)`
Retrieves market operating hours and trading session schedules.

- **Parameters**:
  - `symbols / market_id`: `"equity"`, `"option"`, `"bond"`, `"forex"`, `"future"`.
  - `date (datetime | date | str | None)`: Target date (`YYYY-MM-DD`). Defaults to current day.
- **Example**:
```python
hours = client.market_hour("equity").json()
is_open = hours["equity"]["EQ"]["isOpen"]
```

---

### `instruments(symbols, projection)` / `instrument_cusip(cusip_id)`
Search for financial instruments by symbol or query string, or look up by CUSIP.

- **Parameters**:
  - `symbols (str)`: Search query or symbol.
  - `projection (str)`: `"symbol-search"`, `"symbol-regex"`, `"desc-search"`, `"desc-regex"`, `"search"`, `"fundamental"`.
- **Example**:
```python
fundamentals = client.instruments("AAPL", projection="fundamental").json()
cusip_data = client.instrument_cusip("037833100").json()
```

---

## 3. Orders & Transactions

| Method | Description |
| :--- | :--- |
| `preview_order(accountHash, orderObject)` | Simulates order placement without executing. Returns estimated cost and validation status. |
| `place_order(accountHash, order)` | Submits an order. Order ID is returned in `response.headers["Location"]`. |
| `order_details(accountHash, orderId)` | Retrieves live status, fills, and details for an order ID. |
| `cancel_order(accountHash, orderId)` | Cancels a working or pending order. |
| `replace_order(accountHash, orderId, order)` | Replaces an existing order with modified parameters (price, quantity). |
| `account_orders(accountHash, fromEnteredTime, toEnteredTime, maxResults=None, status=None)` | Lists orders for a specific account in a date range. |
| `account_orders_all(fromEnteredTime, toEnteredTime, maxResults=None, status=None)` | Lists up to 3000 orders across all linked accounts. |
| `transactions(accountHash, startDate, endDate, types=None, symbol=None)` | Lists transactions (trades, transfers, dividends) for an account. |
| `transaction_details(accountHash, transactionId)` | Retrieves specific transaction line-item details. |

---

## 4. Asynchronous Client (`ClientAsync`)

`ClientAsync` matches all methods of `Client` but executes using `aiohttp` and returns awaitable coroutines.

```python
import asyncio
import schwabdev

async def fetch_parallel_quotes():
    async with schwabdev.ClientAsync(parsed=True) as client:
        # Concurrent API calls with asyncio.gather
        quotes_task = client.quotes(["AAPL", "NVDA"])
        history_task = client.price_history("SPY", periodType="day", period=1, frequencyType="minute", frequency=1)
        
        quotes, history = await asyncio.gather(quotes_task, history_task)
        print("Quotes:", quotes)
        print("Recent Candles:", len(history["candles"]))

asyncio.run(fetch_parallel_quotes())
```
