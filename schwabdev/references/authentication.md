# Authentication & Token Management Reference

The Charles Schwab API uses OAuth 2.0 with short-lived **access tokens** and longer-lived **refresh tokens**. `schwabdev` provides automated token persistence, proactive background refresh, and optional rest encryption.

---

## 1. Token Lifecycles & Architecture

| Token Type | Lifespan | Stored in DB | Purpose |
| :--- | :--- | :--- | :--- |
| **Access Token** | 30 minutes | `access_token` table | Sent in `Authorization: Bearer <token>` header with every REST and WebSocket request. |
| **Refresh Token** | 7 days | `refresh_token` table | Used automatically by `schwabdev` to fetch new access tokens without requiring user interaction. |
| **ID Token** | Variable | `id_token` table | OpenID Connect token containing user identity details. |

### Proactive Renewal Mechanism
- `schwabdev` checks token expiration before making requests.
- If the **access token** is within 60 seconds of expiring or has expired, it automatically calls Schwab's token refresh endpoint using the valid refresh token.
- If the **refresh token** is within 30 minutes of expiring (or has expired), `schwabdev` prompts for re-authentication.
- **Tip**: To prevent weekend expiration from interrupting weekday trading, manually trigger a refresh token update ahead of time:
  ```python
  client.update_tokens(force_refresh_token=True)
  ```

---

## 2. Interactive First-Time Login Flow

1. When `schwabdev.Client(...)` is initialized without existing tokens:
   - It generates the Schwab OAuth authorization URL containing your `app_key` and `callback_url`.
   - By default (`open_browser_for_auth=True`), it attempts to open the authorization URL in your default web browser.
   - It prints instructions and the URL to the terminal.
2. In the browser:
   - Log in with your Charles Schwab brokerage credentials.
   - Authorize access to your accounts.
   - The browser redirects to your configured callback URL (e.g., `https://127.0.0.1/?code=...&session=...`).
3. Back in the terminal:
   - Copy the full redirected URL from the browser address bar (or just the authorization code).
   - Paste it into the terminal prompt.
   - `schwabdev` exchanges the code for access and refresh tokens, storing them in SQLite at `tokens_db` (defaults to `~/.schwabdev/tokens.db`).

---

## 3. Headless & Custom Authentication (`call_on_auth`)

For headless servers, containerized environments (Docker), or custom GUI applications where terminal prompts are impractical, provide a custom `call_on_auth` callback function:

```python
import schwabdev

def custom_auth_handler(auth_url: str) -> str:
    """
    Called with the Schwab authorization URL.
    Must return either:
      1. The full returned callback URL (e.g. 'https://127.0.0.1/?code=C0.xxx&session=yyy')
      2. Or just the code string ('C0.xxx')
    """
    print(f"Please visit: {auth_url}")
    # Example: Send auth_url to Discord/Slack/Telegram webhook,
    # or listen on a local web server (see scripts/auth_callback_server.py).
    returned_url = input("Enter returned redirect URL: ")
    return returned_url

client = schwabdev.Client(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    callback_url="https://127.0.0.1:7777",
    call_on_auth=custom_auth_handler,
    open_browser_for_auth=False
)
```

---

## 4. Token Database Encryption (Fernet)

To secure tokens stored at rest in `tokens.db`:

```python
from cryptography.fernet import Fernet
import schwabdev

# 1. Generate an encryption key once and store it securely (e.g., in an env var or secret manager)
encryption_key = Fernet.generate_key().decode()
# Example key: "k9_m8V...=="

# 2. Pass the key to Client initialization
client = schwabdev.Client(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    encryption=encryption_key,
    tokens_db="~/.schwabdev/secure_tokens.db"
)
```

> [!CAUTION]
> If you enable encryption, you **must** supply the same encryption key on subsequent runs. If the key is lost, the tokens cannot be decrypted and the user must re-authenticate.

---

## 5. Global Environment Configuration

Store your credentials in `~/.schwabdev/env.json` to avoid hardcoding or managing `.env` files across multiple scripts:

```python
import schwabdev

schwabdev.save_env_global(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    callback_url="https://127.0.0.1"
)
```

Once saved:
```python
# Both lines resolve keys automatically from ~/.schwabdev/env.json:
client = schwabdev.Client()
client_async = schwabdev.ClientAsync()
```

---

## 6. Accessing Raw Tokens Directly

You can inspect the active tokens directly from the `tokens` object:

```python
# Current access token (JWT string)
access_token = client.tokens.access_token

# Current refresh token
refresh_token = client.tokens.refresh_token

# OpenID Connect ID token
id_token = client.tokens.id_token
```
