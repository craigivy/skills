# WebSocket Streamer Reference

The `schwabdev.Stream` (synchronous thread-based) and `schwabdev.StreamAsync` (native asyncio) classes provide real-time streaming market data over WebSockets directly from Schwab's streamer server.

---

## 1. Streamer Lifecycle & Options

### Starting the Streamer
```python
import schwabdev

client = schwabdev.Client()
streamer = schwabdev.Stream(client)

def my_handler(message: str):
    # message is a JSON-formatted string received from the websocket
    print("Update received:", message)

# Start background streamer thread
streamer.start(receiver=my_handler, daemon=True, ping_interval=20)
```

- **`receiver (callable)`**: The callback function invoked whenever a message arrives.
- **`daemon (bool)`**: If `True`, the streaming thread terminates when the main Python program exits. If `False`, the streamer keeps the process alive.
- **`ping_interval (int)`**: Keep-alive ping interval in seconds (default: 20s).
- **Auto-timeout**: If no subscription requests are sent within ~30 seconds of starting, Schwab closes the WebSocket connection.

### Market Hours Auto-Streaming (`start_auto`)
Automatically starts the stream when the market opens (09:29 AM ET) and stops it at market close (04:00 PM ET):

```python
import datetime
import zoneinfo

streamer.start_auto(
    receiver=my_handler,
    start_time=datetime.time(9, 29, 0),
    stop_time=datetime.time(16, 0, 0),
    on_days=(0, 1, 2, 3, 4),  # Monday - Friday
    now_timezone=zoneinfo.ZoneInfo("America/New_York")
)
```

### Stopping the Streamer
```python
# stop(clear_subscriptions=True)
streamer.stop(clear_subscriptions=True)
```
- If `clear_subscriptions=False`, previously active subscriptions are preserved and will automatically resubscribe the next time `start()` is invoked.

---

## 2. Subscription Commands

When sending streaming requests, you specify a `command`:

| Command | Behavior |
| :--- | :--- |
| `"ADD"` (Default) | Adds the specified symbols to the existing active subscription list for that service. |
| `"SUBS"` | Replaces all existing subscriptions for that service with the new list of symbols. |
| `"UNSUBS"` | Unsubscribes from the specified symbols while leaving other active subscriptions intact. |
| `"VIEW"` | Modifies the list of fields returned for the specified symbols. |

---

## 3. Streaming Services Catalog

All streaming methods return request dictionaries that can be passed directly to `streamer.send(...)`:

### Level 1 Streaming (Delta-Based)
Level 1 services stream **changes** (deltas). When a field updates, only updated fields are sent.

> [!NOTE]
> Field `"0"` (Symbol) must **always** be included in the fields list.

#### 1. Level 1 Equities (`LEVELONE_EQUITIES`)
```python
streamer.send(streamer.level_one_equities(keys="AAPL,NVDA,SPY", fields="0,1,2,3,4,5,8,10,11"))
```
- **Fields Reference**:
  - `0`: Symbol, `1`: Bid Price, `2`: Ask Price, `3`: Last Price, `4`: Bid Size, `5`: Ask Size, `8`: Total Volume, `10`: High Price, `11`: Low Price, `12`: Close Price, `17`: Open Price, `18`: Net Change, `33`: Mark Price.

#### 2. Level 1 Options (`LEVELONE_OPTIONS`)
```python
streamer.send(streamer.level_one_options(keys="AAPL  250117C00200000", fields="0,2,3,4,8,9,20,28,29,30"))
```
- **Fields Reference**:
  - `0`: Symbol, `2`: Bid Price, `3`: Ask Price, `4`: Last Price, `8`: Volume, `9`: Open Interest, `20`: Strike Price, `28`: Delta, `29`: Gamma, `30`: Theta, `31`: Vega, `32`: Rho, `34`: Theoretical Option Value.

#### 3. Level 1 Futures (`LEVELONE_FUTURES`) & Futures Options (`LEVELONE_FUTURES_OPTIONS`)
```python
streamer.send(streamer.level_one_futures(keys="/ES,/NQ", fields="0,1,2,3,4,5,8"))
streamer.send(streamer.level_one_futures_options(keys="./OZCH24C5500", fields="0,1,2,3,4,5,8"))
```

#### 4. Level 1 Forex (`LEVELONE_FOREX`)
```python
streamer.send(streamer.level_one_forex(keys="EUR/USD,USD/JPY", fields="0,1,2,3,4,5,8"))
```

---

### Order Book Streaming (Full Snapshot Data)
Order book services stream **whole** depth snapshots with aggregate sizes at price levels.

- **NYSE Book**: `streamer.send(streamer.nyse_book("AAPL", "0,1,2,3"))`
- **NASDAQ Book**: `streamer.send(streamer.nasdaq_book("NVDA", "0,1,2,3"))`
- **Options Book**: `streamer.send(streamer.options_book("SPY   241220C00500000", "0,1,2,3"))`

---

### Chart & Candlestick Streaming (Sequence-Based)
Streams intraday 1-minute OHLCV candle updates with sequence numbers.

- **Equities Chart**: `streamer.send(streamer.chart_equity("AAPL,TSLA", "0,1,2,3,4,5,6,7,8"))`
  - Fields: `0`: key, `1`: Sequence, `2`: Open, `3`: High, `4`: Low, `5`: Close, `6`: Volume, `7`: Chart Time, `8`: Chart Day.
- **Futures Chart**: `streamer.send(streamer.chart_futures("/ES", "0,1,2,3,4,5,6"))`

---

### Screeners & Account Activity
- **Equity Screener**: `streamer.send(streamer.screener_equity("$DJI", "0,1,2,3"))`
- **Options Screener**: `streamer.send(streamer.screener_options("AAPL", "0,1,2,3"))`
- **Account Activity**: Real-time push notifications for order fills, cancels, and executions:
  ```python
  streamer.send(streamer.account_activity(keys="Account Activity", fields="0,1,2,3", command="SUBS"))
  ```

---

## 4. Translating Numeric Field IDs to Human-Readable Names

`schwabdev` includes a built-in translation dictionary `schwabdev.stream_fields`:

```python
import json
import schwabdev

def translated_handler(message: str):
    payload = json.loads(message)
    if "data" not in payload:
        return
    
    for item in payload["data"]:
        service = item.get("service")
        mapping = schwabdev.stream_fields.get(service, [])
        
        for record in item.get("content", []):
            readable = {}
            for k, v in record.items():
                if k.isdigit() and int(k) < len(mapping):
                    readable[mapping[int(k)]] = v
                else:
                    readable[k] = v
            print(f"[{service}] {record.get('key')}: {readable}")
```

---

## 5. Native Asynchronous Streaming (`StreamAsync`)

```python
import asyncio
import schwabdev

async def async_stream_main():
    async with schwabdev.ClientAsync() as client:
        streamer = schwabdev.StreamAsync(client)
        
        async def custom_receiver(msg):
            print("Async received:", msg)
            
        await streamer.start(receiver=custom_receiver)
        await streamer.send(streamer.level_one_equities("AAPL,MSFT", "0,1,2,3"))
        
        await asyncio.sleep(20)
        await streamer.stop()

asyncio.run(async_stream_main())
```
