from __future__ import annotations

import json
import queue
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from lab_llm.live import EventBroadcaster, format_sse_event
from lab_llm.store import DashboardStore

PACKAGE_STATIC_DIR = Path(__file__).with_name("static")
FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"


class DashboardHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        store: DashboardStore,
        broadcaster: EventBroadcaster | None = None,
    ) -> None:
        super().__init__(server_address, DashboardRequestHandler)
        self.store = store
        self.broadcaster = broadcaster or EventBroadcaster()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    server: DashboardHTTPServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._serve_static("index.html", "text/html; charset=utf-8")
            return
        if path == "/api/events":
            self._handle_sse()
            return
        if path == "/app.js":
            self._serve_static("app.js", "application/javascript; charset=utf-8")
            return
        if path == "/styles.css":
            self._serve_static("styles.css", "text/css; charset=utf-8")
            return
        if path.startswith("/assets/"):
            self._serve_static(path.removeprefix("/"), _guess_content_type(path))
            return
        if path == "/api/sessions":
            self._send_json({"sessions": self.server.store.list_sessions()})
            return

        if path.startswith("/api/sessions/"):
            self._handle_session_api(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _handle_session_api(self, path: str) -> None:
        status, payload = resolve_api_payload(self.server.store, path)
        if status != HTTPStatus.OK:
            self.send_error(status, str(payload))
            return
        self._send_json(payload)

    def _serve_static(self, filename: str, content_type: str) -> None:
        static_dir = FRONTEND_DIST_DIR if FRONTEND_DIST_DIR.exists() else PACKAGE_STATIC_DIR
        path = static_dir / filename
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Static asset missing")
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: Any) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_sse(self) -> None:
        subscriber = self.server.broadcaster.subscribe()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            self.wfile.write(b"event: connected\ndata: {}\n\n")
            self.wfile.flush()
            while True:
                try:
                    event = subscriber.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue
                if event is None:
                    break
                self.wfile.write(format_sse_event(event))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return
        finally:
            self.server.broadcaster.unsubscribe(subscriber)


def run_server(
    host: str, port: int, store: DashboardStore, broadcaster: EventBroadcaster | None = None
) -> None:
    server = DashboardHTTPServer((host, port), store, broadcaster)
    print(f"lab-llm dashboard listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def resolve_api_payload(
    store: DashboardStore, path: str
) -> tuple[HTTPStatus, dict[str, Any] | list[dict[str, Any]] | str]:
    if path == "/api/sessions":
        return HTTPStatus.OK, {"sessions": store.list_sessions()}

    parts = [part for part in path.split("/") if part]
    if len(parts) < 3 or parts[:2] != ["api", "sessions"]:
        return HTTPStatus.NOT_FOUND, "Not found"

    session_id = parts[2]
    if len(parts) == 3:
        payload = store.get_session_detail(session_id)
    elif len(parts) == 4 and parts[3] == "turns":
        payload = store.get_session_turns(session_id)
    elif len(parts) == 4 and parts[3] == "logs":
        payload = store.get_session_logs(session_id)
    elif len(parts) == 4 and parts[3] == "inspect":
        payload = store.get_session_inspect(session_id)
    else:
        return HTTPStatus.NOT_FOUND, "Not found"

    if payload is None:
        return HTTPStatus.NOT_FOUND, "Session not found"
    return HTTPStatus.OK, payload


def _guess_content_type(path: str) -> str:
    if path.endswith(".css"):
        return "text/css; charset=utf-8"
    if path.endswith(".js"):
        return "application/javascript; charset=utf-8"
    if path.endswith(".html"):
        return "text/html; charset=utf-8"
    if path.endswith(".svg"):
        return "image/svg+xml"
    return "application/octet-stream"
