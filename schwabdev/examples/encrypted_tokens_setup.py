"""
Encrypted Token Database Setup Demo for Schwabdev.
Demonstrates:
- Generating a Fernet encryption key
- Setting up Schwabdev with an encrypted SQLite tokens database
"""

import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import schwabdev

load_dotenv()

# 1. Generate a new cryptographic Fernet key if not already in env
existing_key = os.getenv("SCHWAB_ENCRYPTION_KEY")
if not existing_key:
    generated_key = Fernet.generate_key().decode()
    print("=== NEW ENCRYPTION KEY GENERATED ===")
    print(f"SCHWAB_ENCRYPTION_KEY={generated_key}")
    print("Save this key securely in your .env file or password manager!")
    encryption_key = generated_key
else:
    encryption_key = existing_key
    print("Using existing encryption key from environment.")

APP_KEY = os.getenv("SCHWAB_APP_KEY")
APP_SECRET = os.getenv("SCHWAB_APP_SECRET")
CALLBACK_URL = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

if not APP_KEY or not APP_SECRET:
    print("Please set SCHWAB_APP_KEY and SCHWAB_APP_SECRET in .env.")
    exit(1)

# 2. Initialize client with encryption key & dedicated encrypted database path
client = schwabdev.Client(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    callback_url=CALLBACK_URL,
    encryption=encryption_key,
    tokens_db="~/.schwabdev/tokens_encrypted.db"
)

print("\nClient successfully initialized with encrypted token database.")
print("Verifying connection...")
resp = client.linked_accounts()
if resp.ok:
    print(f"Successfully connected! Linked accounts count: {len(resp.json())}")
else:
    print("Response error:", resp.status_code, resp.text)
