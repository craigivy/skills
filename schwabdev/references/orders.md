# Order Construction & Routing Reference

The Charles Schwab API supports order placement and management for equities and equity/index options.

---

## 1. Key Limits & Rules

- **Rate Limits**: 120 order calls per minute, 4,000 order calls per day.
- **Fractional Shares**: Fractional share trading is **not** supported through the Trader API.
- **TOS Requirement**: ThinkorSwim must be enabled for your Schwab account.
- **Order ID Retrieval**: On `place_order()`, if successful (`HTTP 201 Created`), the new Order ID is returned in the `Location` response header:
  ```python
  resp = client.place_order(account_hash, order)
  order_id = resp.headers.get("Location", "/").split("/")[-1]
  ```

---

## 2. Order Schema Structure

Every order is defined as a Python dictionary containing top-level routing parameters and an `orderLegCollection` array:

```python
order = {
    "orderType": "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT" | "NET_DEBIT" | "NET_CREDIT",
    "session": "NORMAL" | "AM" | "PM" | "SEAMLESS",
    "duration": "DAY" | "GOOD_TILL_CANCEL" | "FILL_OR_KILL",
    "orderStrategyType": "SINGLE" | "OCO" | "TRIGGER",
    "price": "150.00",           # Required for LIMIT, NET_DEBIT, NET_CREDIT
    "stopPrice": "145.00",       # Required for STOP, STOP_LIMIT
    "complexOrderStrategyType": "NONE" | "VERTICAL" | "STRADDLE" | "STRANGLE" | "BUTTERFLY" | "CONDOR",
    "orderLegCollection": [
        {
            "instruction": "BUY" | "SELL" | "BUY_TO_OPEN" | "BUY_TO_CLOSE" | "SELL_TO_OPEN" | "SELL_TO_CLOSE",
            "quantity": 10,
            "instrument": {
                "symbol": "AAPL",
                "assetType": "EQUITY" | "OPTION"
            }
        }
    ]
}
```

---

## 3. Order Recipe Templates

### A. Buy Shares at Market Price
```python
market_buy = {
    "orderType": "MARKET",
    "session": "NORMAL",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 10,
            "instrument": {
                "symbol": "AMD",
                "assetType": "EQUITY"
            }
        }
    ]
}
```

---

### B. Sell Shares with a Limit Price
```python
limit_sell = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "duration": "GOOD_TILL_CANCEL",
    "orderStrategyType": "SINGLE",
    "price": "180.50",
    "orderLegCollection": [
        {
            "instruction": "SELL",
            "quantity": 25,
            "instrument": {
                "symbol": "AMD",
                "assetType": "EQUITY"
            }
        }
    ]
}
```

---

### C. Stop Loss Order
```python
stop_loss = {
    "orderType": "STOP",
    "session": "NORMAL",
    "duration": "GOOD_TILL_CANCEL",
    "orderStrategyType": "SINGLE",
    "stopPrice": "140.00",
    "orderLegCollection": [
        {
            "instruction": "SELL",
            "quantity": 50,
            "instrument": {
                "symbol": "NVDA",
                "assetType": "EQUITY"
            }
        }
    ]
}
```

---

### D. Single-Leg Option (Buy to Open Call)
> **Option Symbol Format (OSI Standard 21 chars)**:
> `Root (padded to 6 chars with spaces)` + `YYMMDD` + `C/P` + `Strike * 1000 (8 chars padded with leading zeros)`
> Example: `AAPL  250117C00200000` (AAPL Jan 17, 2025 $200 Call)

```python
option_buy = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "price": "3.50",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "complexOrderStrategyType": "NONE",
    "orderLegCollection": [
        {
            "instruction": "BUY_TO_OPEN",
            "quantity": 2,
            "instrument": {
                "symbol": "AAPL  250117C00200000",
                "assetType": "OPTION"
            }
        }
    ]
}
```

---

### E. Multi-Leg Vertical Put Spread
```python
vertical_spread = {
    "orderType": "NET_DEBIT",
    "session": "NORMAL",
    "price": "0.75",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "complexOrderStrategyType": "VERTICAL",
    "orderLegCollection": [
        {
            "instruction": "BUY_TO_OPEN",
            "quantity": 5,
            "instrument": {
                "symbol": "SPY   250117P00550000",
                "assetType": "OPTION"
            }
        },
        {
            "instruction": "SELL_TO_OPEN",
            "quantity": 5,
            "instrument": {
                "symbol": "SPY   250117P00540000",
                "assetType": "OPTION"
            }
        }
    ]
}
```

---

### F. One-Cancels-Other (OCO) Bracket Order
```python
oco_bracket = {
    "orderStrategyType": "OCO",
    "childOrderStrategies": [
        {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "duration": "GOOD_TILL_CANCEL",
            "price": "160.00",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": 10,
                    "instrument": {"symbol": "AAPL", "assetType": "EQUITY"}
                }
            ]
        },
        {
            "orderType": "STOP",
            "session": "NORMAL",
            "duration": "GOOD_TILL_CANCEL",
            "stopPrice": "140.00",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": 10,
                    "instrument": {"symbol": "AAPL", "assetType": "EQUITY"}
                }
            ]
        }
    ]
}
```

---

## 4. Lifecycle Methods

```python
# 1. Preview order
preview_resp = client.preview_order(account_hash, order)
if preview_resp.ok:
    print("Commission & fees:", preview_resp.json().get("orderValidationResult"))

# 2. Place order
place_resp = client.place_order(account_hash, order)
if place_resp.status_code == 201:
    order_id = place_resp.headers.get("Location", "/").split("/")[-1]
    
    # 3. Retrieve order details
    details = client.order_details(account_hash, order_id).json()
    status = details["status"] # e.g. "WORKING", "FILLED", "QUEUED"
    
    # 4. Modify / Replace order price
    order["price"] = "152.00"
    client.replace_order(account_hash, order_id, order)
    
    # 5. Cancel order
    client.cancel_order(account_hash, order_id)
```
