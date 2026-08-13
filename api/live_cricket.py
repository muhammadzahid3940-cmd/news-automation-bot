import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tools import fetch_live_cricket  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = fetch_live_cricket()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
        except Exception as exc:  # noqa: BLE001 - best-effort live data
            body = json.dumps(
                {
                    "source": "error",
                    "matches": [],
                    "note": str(exc),
                    "generated_at": "",
                },
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002 - silence request noise
        pass
