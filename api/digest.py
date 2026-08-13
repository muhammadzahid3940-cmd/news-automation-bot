import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from db import latest_run  # noqa: E402
from pipeline import LATEST_FILE  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = latest_run()
            if data:
                self._send(200, {"ok": True, **data})
                return
        except Exception:  # noqa: BLE001 - fall back to the file copy
            pass
        if not LATEST_FILE.exists():
            self._send(200, {"ok": False, "digest": ""})
            return
        try:
            data = json.loads(LATEST_FILE.read_text(encoding="utf-8"))
            self._send(200, {"ok": True, **data})
        except json.JSONDecodeError as exc:
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
