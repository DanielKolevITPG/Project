from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from collections.abc import Callable, Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast, override
from urllib.parse import parse_qs, urlparse


# Ensure project root is importable when running `python src/ui_server.py`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from src.chatbot.router import bot
from src.database import db as database_db
from src.main import init_db, load_seed_data, setup_logging


QueryFn = Callable[..., object]
query_db = cast(QueryFn, database_db.execute_query)


UI_DIR = os.path.join(PROJECT_ROOT, "ui")
LOG_FILE = os.path.join(PROJECT_ROOT, "commands.log")

LOG_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - "
    + r"INPUT: (?P<input>.*?) \| INTENT: (?P<intent>[^|]+?)"
    + r"(?: \| PARAMS: (?P<params>\{.*?\}))?"
    + r" \| RESULT: (?P<result>OK|ERROR) \| MESSAGE: (?P<message>.*)$"
)


def _rows_to_dicts(rows_obj: object) -> list[dict[str, object]]:
    if not isinstance(rows_obj, list):
        return []
    rows = cast(list[object], rows_obj)
    result: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            if isinstance(row, sqlite3.Row):
                normalized_row: dict[str, object] = {}
                for key in row.keys():
                    normalized_row[str(key)] = row[key]
                result.append(normalized_row)
            continue
        typed_row = cast(Mapping[object, object], row)
        normalized_map: dict[str, object] = {}
        for key, value in typed_row.items():
            normalized_map[str(key)] = value
        result.append(normalized_map)
    return result


def _extract_param(raw_params: str | None, key: str) -> str | None:
    if not raw_params:
        return None
    pattern = re.compile(rf"['\"]{re.escape(key)}['\"]\s*:\s*['\"](.*?)['\"]")
    m = pattern.search(raw_params)
    if not m:
        return None
    value = m.group(1).strip()
    return value or None


def _format_log_entry(line: str) -> str | None:
    m = LOG_RE.match(line)
    if not m:
        return None

    ts = m.group("ts")
    hhmmss = ts[11:19]
    intent = m.group("intent").strip()
    status = m.group("result").strip()
    raw_input = m.group("input").strip()
    raw_params = m.group("params")

    if intent == "transfer_player" and status == "OK":
        player = _extract_param(raw_params, "player") or "Unknown player"
        to_club = _extract_param(raw_params, "to_club") or "Unknown club"
        return f"{hhmmss} | Player {player} moved to club {to_club}"

    if status == "ERROR":
        return f"{hhmmss} | Failed: {raw_input}"

    return f"{hhmmss} | {raw_input}"


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
    server_version: str = "FootballManagerUI/1.0"

    @override
    def log_message(self, format: str, *args: object) -> None:
        # Avoid noisy default stdout logs; app logs commands in commands.log.
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        _ = self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/leagues":
            try:
                rows = query_db(
                    (
                        "SELECT l.id, l.name, l.season, "
                        + "(SELECT COUNT(*) FROM league_teams lt WHERE lt.league_id = l.id) AS teams_count, "
                        + "(SELECT COUNT(*) FROM matches m WHERE m.league_id = l.id) AS matches_count "
                        + "FROM leagues l "
                        + "ORDER BY l.created_at DESC, l.name ASC"
                    ),
                    fetchall=True,
                )
                leagues = _rows_to_dicts(rows)
                body = json.dumps({"ok": True, "leagues": leagues}, ensure_ascii=False).encode(
                    "utf-8"
                )
                return self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                body = json.dumps(
                    {"ok": False, "error": str(e)}, ensure_ascii=False
                ).encode("utf-8")
                return self._send(500, body, "application/json; charset=utf-8")

        if path == "/api/teams":
            try:
                rows = query_db(
                    (
                        "SELECT c.id, c.name, "
                        + "COUNT(p.id) AS players_count "
                        + "FROM clubs c "
                        + "LEFT JOIN players p ON p.club_id = c.id "
                        + "GROUP BY c.id, c.name "
                        + "ORDER BY c.name ASC"
                    ),
                    fetchall=True,
                )
                teams = _rows_to_dicts(rows)
                body = json.dumps({"ok": True, "teams": teams}, ensure_ascii=False).encode(
                    "utf-8"
                )
                return self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                body = json.dumps(
                    {"ok": False, "error": str(e)}, ensure_ascii=False
                ).encode("utf-8")
                return self._send(500, body, "application/json; charset=utf-8")

        if path == "/api/matches":
            try:
                query = parse_qs(parsed.query or "")
                league_id_text = (query.get("league_id") or [""])[0]
                if not league_id_text.isdigit():
                    body = json.dumps(
                        {"ok": False, "error": "Missing league_id query parameter."},
                        ensure_ascii=False,
                    ).encode("utf-8")
                    return self._send(400, body, "application/json; charset=utf-8")

                league_id = int(league_id_text)
                rows = query_db(
                    (
                        "SELECT m.id, m.round_no, "
                        + "h.name AS home_name, "
                        + "a.name AS away_name, "
                        + "m.home_goals, "
                        + "m.away_goals, "
                        + "m.status "
                        + "FROM matches m "
                        + "JOIN clubs h ON h.id = m.home_club_id "
                        + "JOIN clubs a ON a.id = m.away_club_id "
                        + "WHERE m.league_id = ? "
                        + "ORDER BY m.round_no ASC, m.id ASC"
                    ),
                    (league_id,),
                    fetchall=True,
                )
                matches = _rows_to_dicts(rows)
                body = json.dumps({"ok": True, "matches": matches}, ensure_ascii=False).encode(
                    "utf-8"
                )
                return self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                body = json.dumps(
                    {"ok": False, "error": str(e)}, ensure_ascii=False
                ).encode("utf-8")
                return self._send(500, body, "application/json; charset=utf-8")

        if path == "/api/league-teams":
            try:
                query = parse_qs(parsed.query or "")
                league_id_text = (query.get("league_id") or [""])[0]
                if not league_id_text.isdigit():
                    body = json.dumps(
                        {"ok": False, "error": "Missing league_id query parameter."},
                        ensure_ascii=False,
                    ).encode("utf-8")
                    return self._send(400, body, "application/json; charset=utf-8")

                league_id = int(league_id_text)
                rows = query_db(
                    (
                        "SELECT c.id, c.name "
                        + "FROM league_teams lt "
                        + "JOIN clubs c ON c.id = lt.club_id "
                        + "WHERE lt.league_id = ? "
                        + "ORDER BY c.name ASC"
                    ),
                    (league_id,),
                    fetchall=True,
                )
                teams = _rows_to_dicts(rows)
                body = json.dumps({"ok": True, "teams": teams}, ensure_ascii=False).encode(
                    "utf-8"
                )
                return self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                body = json.dumps(
                    {"ok": False, "error": str(e)}, ensure_ascii=False
                ).encode("utf-8")
                return self._send(500, body, "application/json; charset=utf-8")

        if path == "/api/logs":
            try:
                if not os.path.exists(LOG_FILE):
                    body = json.dumps({"ok": True, "logs": []}, ensure_ascii=False).encode(
                        "utf-8"
                    )
                    return self._send(200, body, "application/json; charset=utf-8")

                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\n") for line in f.readlines()]

                formatted_lines: list[str] = []
                for line in lines:
                    entry = _format_log_entry(line)
                    if entry:
                        formatted_lines.append(entry)

                body = json.dumps(
                    {"ok": True, "logs": formatted_lines[-80:]},
                    ensure_ascii=False,
                ).encode("utf-8")
                return self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                body = json.dumps(
                    {"ok": False, "error": str(e)}, ensure_ascii=False
                ).encode("utf-8")
                return self._send(500, body, "application/json; charset=utf-8")

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
            payload = cast(dict[str, object], json.loads(raw.decode("utf-8")))
            raw_text = payload.get("text")
            text = raw_text.strip() if isinstance(raw_text, str) else ""
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
