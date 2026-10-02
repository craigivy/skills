#!/usr/bin/env python3
"""
CLI Utility to inspect token database validity and expiration.
Usage:
    python check_tokens.py [--db ~/.schwabdev/tokens.db] [--key YOUR_FERNET_KEY]
"""

import argparse
import datetime
import os
import sqlite3
import sys

def check_tokens(db_path: str, encryption_key: str = None):
    expanded_path = os.path.expanduser(db_path)
    if not os.path.exists(expanded_path):
        print(f"Error: Token database not found at {expanded_path}")
        return 1

    conn = sqlite3.connect(expanded_path)
    cursor = conn.cursor()

    print(f"--- Inspecting Token DB: {expanded_path} ---")
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Tables to inspect
    tables = [
        ("access_token", "Access Token (30 min)", datetime.timedelta(minutes=30)),
        ("refresh_token", "Refresh Token (7 days)", datetime.timedelta(days=7)),
        ("id_token", "ID Token", None)
    ]

    for table_name, label, validity_period in tables:
        try:
            cursor.execute(f"SELECT token, date_issued FROM {table_name} LIMIT 1")
            row = cursor.fetchone()
            if not row:
                print(f"[-] {label}: Not found in database.")
                continue

            token_val, date_issued_str = row
            is_encrypted = token_val.startswith("enc:") if isinstance(token_val, str) else False

            issued_dt = None
            if date_issued_str:
                try:
                    # ISO format parsing
                    issued_dt = datetime.datetime.fromisoformat(date_issued_str)
                    if issued_dt.tzinfo is None:
                        issued_dt = issued_dt.replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    issued_dt = None

            print(f"[+] {label}:")
            print(f"    - Encrypted at rest: {is_encrypted}")
            if issued_dt:
                print(f"    - Issued At: {issued_dt.isoformat()}")
                if validity_period:
                    expires_at = issued_dt + validity_period
                    time_left = expires_at - now_utc
                    if time_left.total_seconds() > 0:
                        mins, secs = divmod(int(time_left.total_seconds()), 60)
                        hours, mins = divmod(mins, 60)
                        days, hours = divmod(hours, 24)
                        print(f"    - Status: VALID (Expires in {days}d {hours}h {mins}m {secs}s at {expires_at.isoformat()})")
                    else:
                        print(f"    - Status: EXPIRED (Expired {-time_left.total_seconds() / 60:.1f} minutes ago)")
            else:
                print("    - Issued At: Unknown")
        except sqlite3.OperationalError as e:
            print(f"[-] {label} table check error: {e}")

    conn.close()
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Schwabdev token database expiration.")
    parser.add_argument("--db", default="~/.schwabdev/tokens.db", help="Path to tokens.db file")
    parser.add_argument("--key", default=None, help="Fernet encryption key (if encrypted)")
    args = parser.parse_args()

    sys.exit(check_tokens(args.db, args.key))
