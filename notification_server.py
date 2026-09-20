"""
notification_server.py
=======================
Local OS notification routing for the alerting matrix.
Lightweight HTTP server + notify-py (libnotify / DBus) for desktop alerts.
Started by start_neo.sh — runs in the background under python3.
"""
import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

HOST = "127.0.0.1"
PORT = 51820

try:
    from notifypy import Notify
    toaster = Notify(default_notification_application_name="NEO")
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False
    print("[notification_server] notify-py not installed — alerts will log only.", flush=True)


def show_toast(title: str, message: str, urgency: str = "normal"):
    """Fire a desktop notification via notify-py (self-threading).

    NOTE: notify-py has no duration parameter — the desktop environment owns the
    toast timeout. The old win10toast `duration` arguments are kept in the public
    signatures below for API compatibility and are intentionally ignored.
    """
    toaster.title = title
    toaster.message = message
    toaster.urgency = urgency
    return toaster.send(block=False)


class AlertHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that accepts POST alerts and shows desktop notifications."""

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body)
            title = data.get("title", "NEO Alert")
            message = data.get("message", "")
            duration = data.get("duration", 5)  # accepted for API compat — notify-py ignores it

            if HAS_TOAST:
                show_toast(title, message)
            else:
                print(f"[notification_server] {title}: {message}", flush=True)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"status":"error","reason":str(e)}).encode())

    def log_message(self, format, *args):
        pass  # Suppress HTTP request logging (silent mode)


class NotificationServer:
    """Wrapper class for the notification HTTP server."""

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self._server = None
        self._thread = None

    def start(self):
        """Start the notification server in a daemon thread."""
        self._server = HTTPServer((self.host, self.port), AlertHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"[notification_server] Listening on {self.host}:{self.port}", flush=True)

    def stop(self):
        """Shut down the server gracefully."""
        if self._server:
            self._server.shutdown()

    def send_alert(self, title: str, message: str, duration: int = 5):
        """Programmatic method to send an alert via the local HTTP endpoint."""
        try:
            import urllib.request
            payload = json.dumps({"title": title, "message": message, "duration": duration}).encode()
            req = urllib.request.Request(
                f"http://{self.host}:{self.port}/",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=2)
            return True
        except Exception:
            if HAS_TOAST:
                show_toast(title, message, urgency="critical")
            return False


if __name__ == "__main__":
    server = NotificationServer()
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()