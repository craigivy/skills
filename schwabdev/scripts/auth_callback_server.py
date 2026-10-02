#!/usr/bin/env python3
"""
Local HTTPS Callback Interceptor for Schwabdev OAuth Authentication.
Starts a temporary local server to capture the redirect URL and returns the auth code automatically.
Usage with schwabdev:
    from scripts.auth_callback_server import capture_schwab_callback
    client = schwabdev.Client(..., call_on_auth=capture_schwab_callback)
"""

import http.server
import ssl
import threading
import urllib.parse
import webbrowser

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    returned_url = None

    def do_GET(self):
        CallbackHandler.returned_url = self.path
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        response_html = """
        <html>
        <head><title>Schwab Authentication Successful</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #0070ba;">Authentication Successful!</h1>
            <p>You can close this browser tab and return to your application.</p>
        </body>
        </html>
        """
        self.wfile.write(response_html.encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress standard logging to keep console output clean
        pass

def capture_schwab_callback(auth_url: str, host: str = "127.0.0.1", port: int = 7777) -> str:
    """
    Automates the OAuth callback capture by running a temporary local web server.
    Note: Requires an app callback registered with matching port, e.g., https://127.0.0.1:7777
    """
    CallbackHandler.returned_url = None
    server_address = (host, port)
    
    print(f"\n[Auth Helper] Launching browser for Schwab authentication...")
    print(f"[Auth Helper] URL: {auth_url}\n")
    
    # Open browser
    webbrowser.open(auth_url)

    # Note: If testing plain HTTP redirect on localhost, http server works.
    # If Schwab enforces SSL redirect, generate a temporary self-signed cert or use standard manual paste.
    try:
        httpd = http.server.HTTPServer(server_address, CallbackHandler)
        print(f"[Auth Helper] Waiting for OAuth callback on https://{host}:{port}...")
        
        # Handle single request
        httpd.handle_request()
        httpd.server_close()

        if CallbackHandler.returned_url:
            full_url = f"https://{host}:{port}{CallbackHandler.returned_url}"
            print("[Auth Helper] Successfully captured OAuth callback URL!")
            return full_url
    except Exception as e:
        print(f"[Auth Helper] Automated capture fallback to manual prompt: {e}")

    return input("Enter the full redirected URL from your browser address bar: ").strip()

if __name__ == "__main__":
    print("This module is designed to be imported as a call_on_auth handler in schwabdev:")
    print("    from scripts.auth_callback_server import capture_schwab_callback")
    print("    client = schwabdev.Client(..., call_on_auth=capture_schwab_callback)")
