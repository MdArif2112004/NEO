"""
notification_server.py
=======================
Local OS notification routing for the alerting matrix.
Lightweight HTTP server + win10toast for desktop alerts.
Referenced by start_neo.bat — runs silently via pythonw.
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
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False
    print("[notification_server] win10toast not installed — alerts will log only.", flush=True)


class AlertHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that accepts POST alerts and shows desktop notifications."""

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body)
            title = data.get("title", "NEO Alert")
            message = data.get("message", "")
            duration = data.get("duration", 5)

            if HAS_TOAST:
                toaster.show_toast(title, message, duration=duration, threaded=True)
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
        except Exception as e:
            if HAS_TOAST:
                toaster.show_toast(title, message, duration=duration, threaded=True)
            return False


if __name__ == "__main__":
    server = NotificationServer()
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()