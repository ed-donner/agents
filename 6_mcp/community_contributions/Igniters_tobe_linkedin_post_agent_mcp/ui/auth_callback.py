from __future__ import annotations

import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from config.settings import get_settings


@dataclass
class PendingCallback:
    code: str | None = None
    state: str | None = None
    error: str | None = None


class AuthCallbackStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._expected_state: str | None = None
        self._pending = PendingCallback()

    def set_expected_state(self, state: str) -> None:
        with self._lock:
            self._expected_state = state

    def get_expected_state(self) -> str | None:
        with self._lock:
            return self._expected_state

    def set_callback(self, code: str | None, state: str | None, error: str | None) -> None:
        with self._lock:
            self._pending = PendingCallback(code=code, state=state, error=error)

    def consume(self) -> PendingCallback:
        with self._lock:
            current = self._pending
            self._pending = PendingCallback()
            return current


STORE = AuthCallbackStore()
SERVER: ThreadingHTTPServer | None = None
SERVER_THREAD: threading.Thread | None = None


def start_callback_server() -> None:
    global SERVER, SERVER_THREAD
    if SERVER:
        return
    settings = get_settings()
    settings.validate_linkedin()
    callback_path = settings.callback_path

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != callback_path:
                self.send_response(404)
                self.end_headers()
                return
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            state = params.get("state", [None])[0]
            error = params.get("error", [None])[0]
            STORE.set_callback(code=code, state=state, error=error)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>LinkedIn authorization received.</h2><p>Return to the app and click Finalize LinkedIn Auth.</p></body></html>"
            )

        def log_message(self, format: str, *args) -> None:
            return

    SERVER = ThreadingHTTPServer((settings.callback_host, settings.callback_port), CallbackHandler)
    SERVER_THREAD = threading.Thread(target=SERVER.serve_forever, daemon=True)
    SERVER_THREAD.start()
