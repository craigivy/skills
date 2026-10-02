# Troubleshooting & FAQs Reference

Common issues encountered when using the `schwabdev` library, diagnosis steps, and resolutions.

---

## 1. HTTP Status Code Catalog

### `400 Bad Request`
- **Causes**:
  - Invalid parameters passed to an API call.
  - Option symbol missing required spaces or formatting (e.g., `AAPL  250117C00200000`).
  - Request body JSON missing required fields for an order (e.g. `orderLegCollection` missing `positionEffect` or `instruction`).
  - Requesting price history or option chains with invalid date formats (expected ISO 8601 or epoch ms).
- **Fix**: Check `client.validate_params=True` to catch client-side errors, and print the raw `response.text` or `response.json()` for Schwab's specific error message.

---

### `401 Unauthorized`
- **Causes**:
  - Access token expired and automatic refresh failed.
  - Refresh token expired (after 7 days) or was invalidated by another login session.
  - Invalid `app_key` or `app_secret`.
- **Fix**:
  - Run `client.update_tokens(force_refresh_token=True)` to re-authenticate.
  - Inspect expiration with `scripts/check_tokens.py`.
  - Delete corrupted `~/.schwabdev/tokens.db` and log in again.

---

### `403 Forbidden`
- **Causes**:
  - App in Schwab Developer Portal is in **"Approved - Pending"** status instead of **"Ready for use"**. It can take 24–48 hours for Schwab to activate a new developer app.
  - Missing an API product: App has only "Accounts and Trading" OR only "Market Data", but the endpoint requires the other.
  - ThinkorSwim (TOS) is not enabled on your Schwab brokerage account (required for orders and balances).
- **Fix**:
  - Go to [developer.schwab.com/dashboard/apps](https://developer.schwab.com/dashboard/apps) -> View Details -> Modify App -> Ensure both products are enabled and status is "Ready for use".
  - Log into ThinkorSwim desktop/web/mobile at least once with your Schwab credentials to activate TOS for your account.

---

### `429 Too Many Requests`
- **Limits**:
  - **120 requests/minute** for standard REST API endpoints.
  - **4,000 order-related calls/day**.
  - **500 concurrent streamed keys** across all services.
- **Fix**:
  - Do **not** poll REST API endpoints (`client.quotes()`, `client.quote()`) in tight loops for real-time prices. Use `schwabdev.Stream` instead.
  - Implement exponential backoff or use `asyncio.sleep()` when executing batch operations.

---

### `500 / 503 Server Errors`
- **Causes**:
  - Schwab internal maintenance windows (often during weekends or between 12:00 AM – 04:00 AM ET).
- **Fix**: Retry request after a brief delay. Check Schwab developer community/Discord if outages persist.

---

## 2. Platform & OS Specific Issues

### macOS Python SSL Certificate Error
- **Symptom**: `ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]` when connecting or refreshing tokens.
- **Fix**: Run the certificate installer included with Python on macOS:
  ```bash
  open /Applications/Python\ 3.11/Install\ Certificates.command
  # (Replace 3.11 with your installed Python version)
  ```

---

### Callback URL Mismatch
- **Symptom**: Schwab OAuth login page reports `Invalid redirect_uri` or returns to an error page.
- **Fix**:
  - Callback URLs must start with `https` and point to `127.0.0.1` or `localhost`.
  - Must not have a trailing slash (e.g., use `https://127.0.0.1`, not `https://127.0.0.1/`).
  - The URL configured in `schwabdev.Client(callback_url=...)` must match **exactly** one of the callback URLs registered in your Schwab Developer App.

---

### Multiple Processes & Token Database Locking
- **Symptom**: `sqlite3.OperationalError: database is locked` or tokens continually getting overwritten.
- **Fix**:
  - Multiple client instances across scripts must point to the same `tokens_db` path (default `~/.schwabdev/tokens.db`).
  - Avoid initializing independent streamers in multiple processes using the same credentials; Schwab allows only **one active WebSocket connection** per account.
