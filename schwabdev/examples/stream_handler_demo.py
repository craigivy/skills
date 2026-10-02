"""
WebSocket Stream Handler Demo for Schwabdev.
Demonstrates:
- Starting Streamer background thread
- Subscribing to Level 1 Equities and Account Activity
- Decoding field indices to human-readable names using schwabdev.stream_fields
"""

import json
import os
import time
from dotenv import load_dotenv
import schwabdev

load_dotenv()

APP_KEY = os.getenv("SCHWAB_APP_KEY")
APP_SECRET = os.getenv("SCHWAB_APP_SECRET")
CALLBACK_URL = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

def handle_stream_message(message: str):
    """
    Callback invoked whenever a message arrives from Schwab WebSocket.
    Translates numeric keys into readable metric names.
    """
    try:
        data_obj = json.loads(message)
    except Exception:
        print("Raw Message:", message)
        return

    # Check for heartbeat/notifications
    if "notify" in data_obj:
        print("[NOTIFY]", data_obj["notify"])
        return

    if "response" in data_obj:
        print("[RESPONSE]", data_obj["response"])
        return

    if "data" in data_obj:
        for entry in data_obj["data"]:
            service = entry.get("service")
            field_map = schwabdev.stream_fields.get(service, [])

            for item in entry.get("content", []):
                symbol = item.get("key", "UNKNOWN")
                decoded = {}
                for k, v in item.items():
                    if k.isdigit() and int(k) < len(field_map):
                        decoded[field_map[int(k)]] = v
                    else:
                        decoded[k] = v
                print(f"[{service}] {symbol:6s} -> {decoded}")

def main():
    if not APP_KEY or not APP_SECRET:
        print("Set SCHWAB_APP_KEY and SCHWAB_APP_SECRET in .env.")
        return

    client = schwabdev.Client(app_key=APP_KEY, app_secret=APP_SECRET, callback_url=CALLBACK_URL)
    streamer = schwabdev.Stream(client)

    print("Starting Schwabdev Streamer...")
    streamer.start(receiver=handle_stream_message, daemon=True)

    # Subscribe to Level 1 Equities (0=Symbol, 1=Bid, 2=Ask, 3=Last, 4=Bid Size, 5=Ask Size, 8=Volume)
    symbols = "AAPL,NVDA,TSLA,SPY"
    print(f"Subscribing to Level 1 data for: {symbols}")
    streamer.send(streamer.level_one_equities(keys=symbols, fields="0,1,2,3,4,5,8,10,11,18"))

    # Also subscribe to real-time Account Activity (fills, orders)
    streamer.send(streamer.account_activity())

    print("Listening for 30 seconds (Ctrl+C to stop)...")
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping streamer...")
        streamer.stop(clear_subscriptions=True)

if __name__ == "__main__":
    main()
