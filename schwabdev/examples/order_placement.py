"""
Order Placement & Lifecycle Demo for Schwabdev.
Demonstrates:
- Retrieving account hashes
- Previewing an order
- Submitting an order
- Extracting Order ID from Location response header
- Fetching order details and status
- Replacing and canceling orders
"""

import os
import time
from dotenv import load_dotenv
import schwabdev

load_dotenv()

APP_KEY = os.getenv("SCHWAB_APP_KEY")
APP_SECRET = os.getenv("SCHWAB_APP_SECRET")
CALLBACK_URL = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

def main():
    if not APP_KEY or not APP_SECRET:
        print("Please configure SCHWAB_APP_KEY and SCHWAB_APP_SECRET.")
        return

    client = schwabdev.Client(app_key=APP_KEY, app_secret=APP_SECRET, callback_url=CALLBACK_URL)

    # 1. Get primary account hash
    accounts_resp = client.linked_accounts()
    if not accounts_resp.ok:
        print("Failed to get linked accounts:", accounts_resp.text)
        return

    accounts = accounts_resp.json()
    account_hash = accounts[0]["hashValue"]
    print(f"Using Account Hash: {account_hash[:10]}... (Account: {accounts[0]['accountNumber']})")

    # 2. Build a Limit Buy Order for 1 share well below market (safe test order)
    test_order = {
        "orderType": "LIMIT",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "price": "5.00",  # Limit price
        "orderLegCollection": [
            {
                "instruction": "BUY",
                "quantity": 1,
                "instrument": {
                    "symbol": "INTC",
                    "assetType": "EQUITY"
                }
            }
        ]
    }

    # 3. Preview Order
    print("\n--- Previewing Order ---")
    preview_resp = client.preview_order(account_hash, test_order)
    if preview_resp.ok:
        print("Preview Result:", preview_resp.json())
    else:
        print(f"Preview Failed ({preview_resp.status_code}): {preview_resp.text}")

    # Prompt user before actual placement
    proceed = input("\nDo you want to submit this test order? (y/N): ").strip().lower()
    if proceed != "y":
        print("Order placement aborted.")
        return

    # 4. Place Order
    print("\n--- Submitting Order ---")
    place_resp = client.place_order(account_hash, test_order)
    print(f"Status: {place_resp.status_code}")

    if place_resp.status_code == 201:
        # Extract Order ID from Location header
        location_header = place_resp.headers.get("Location", "")
        order_id = location_header.split("/")[-1] if location_header else None
        print(f"Order Placed Successfully! Order ID: {order_id}")

        if order_id:
            # 5. Query Order Details
            time.sleep(1)
            details_resp = client.order_details(account_hash, order_id)
            if details_resp.ok:
                order_info = details_resp.json()
                print(f"Order Status: {order_info.get('status')}")
                print(f"Remaining Quantity: {order_info.get('remainingQuantity')}")

            # 6. Cancel Order
            cancel = input("Cancel this order now? (Y/n): ").strip().lower()
            if cancel != "n":
                cancel_resp = client.cancel_order(account_hash, order_id)
                print(f"Cancel Response Code: {cancel_resp.status_code}")
    else:
        print("Place order failed:", place_resp.text)

if __name__ == "__main__":
    main()
