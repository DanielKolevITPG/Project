from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


# Ensure project root is importable when running `python src/ui_server.py`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from src.chatbot.router import bot
from src.main import init_db, load_seed_data, setup_logging


UI_DIR = os.path.join(PROJECT_ROOT, "ui")


def _read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _guess_content_type(path: str) -> str:
    p = path.lower()
    if p.endswith(".html"):
        return "text/html; charset=utf-8"
    if p.endswith(".css"):
        return "text/css; charset=utf-8"
    if p.endswith(".js"):
        return "application/javascript; charset=utf-8"
    if p.endswith(".svg"):
        return "image/svg+xml"
    if p.endswith(".png"):
        return "image/png"
    return "application/octet-stream"


class UIHandler(BaseHTTPRequestHandler):
    server_version = "FootballManagerUI/1.0"

    def log_message(self, fmt: str, *args) -> None:
        # Avoid noisy default stdout logs; app logs commands in commands.log.
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", ""):
            file_path = os.path.join(UI_DIR, "index.html")
            return self._send(
                200, _read_file_bytes(file_path), "text/html; charset=utf-8"
            )

        # Static assets: /assets/...
        if path.startswith("/assets/"):
            rel = path[len("/assets/") :]
            rel = rel.replace("/", os.sep)
            file_path = os.path.abspath(os.path.join(UI_DIR, "assets", rel))
            if not file_path.startswith(
                os.path.abspath(os.path.join(UI_DIR, "assets"))
            ):
                return self._send(403, b"Forbidden", "text/plain; charset=utf-8")
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return self._send(404, b"Not found", "text/plain; charset=utf-8")
            return self._send(
                200, _read_file_bytes(file_path), _guess_content_type(file_path)
            )

        return self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/command":
            return self._send(404, b"Not found", "text/plain; charset=utf-8")

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8"))
            text = (payload.get("text") or "").strip()
        except Exception:
            body = json.dumps({"ok": False, "error": "Invalid JSON payload."}).encode(
                "utf-8"
            )
            return self._send(400, body, "application/json; charset=utf-8")

        if not text:
            body = json.dumps({"ok": False, "error": "Empty command."}).encode("utf-8")
            return self._send(400, body, "application/json; charset=utf-8")

        try:
            response, exit_flag = bot.handle(text)
            body = json.dumps(
                {"ok": True, "response": response, "exit": bool(exit_flag)},
                ensure_ascii=False,
            ).encode("utf-8")
            return self._send(200, body, "application/json; charset=utf-8")
        except Exception as e:
            body = json.dumps(
                {"ok": False, "error": str(e)},
                ensure_ascii=False,
            ).encode("utf-8")
            return self._send(500, body, "application/json; charset=utf-8")


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    setup_logging()
    init_db()
    load_seed_data()

    httpd = ThreadingHTTPServer((host, port), UIHandler)
    print(f"UI running on http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    httpd.serve_forever()


if __name__ == "__main__":
    h = os.environ.get("UI_HOST", "127.0.0.1")
    p = int(os.environ.get("UI_PORT", "8000"))
    run(h, p)
