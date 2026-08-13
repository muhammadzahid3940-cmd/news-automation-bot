import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import run_pipeline  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        topic = (query.get("topic") or [None])[0]
        self._run(topic)

    def do_POST(self):
        topic = None
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length).decode("utf-8")
            if body:
                topic = json.loads(body).get("topic") or None
        except (json.JSONDecodeError, ValueError):
            topic = None
        self._run(topic)

    def _run(self, topic):
        try:
            result = run_pipeline(topic)
            self._send(
                200,
                {
                    "ok": True,
                    "topic": result["topic"],
                    "article_count": result["article_count"],
                },
            )
        except Exception as exc:  # noqa: BLE001
            self._send(500, {"ok": False, "error": str(exc)})

    def _send(self, status: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002 - silence request noise
        pass
