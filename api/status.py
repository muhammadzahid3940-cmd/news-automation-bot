import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from db import latest_run  # noqa: E402


def _channels_config() -> dict:
    sheets_credentials = bool(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    )
    return {
        "slack": bool(os.getenv("SLACK_WEBHOOK_URL", "").strip()),
        "google_sheets": sheets_credentials
        and bool(
            os.getenv("GOOGLE_SHEET_ID", "").strip()
            or os.getenv("SPREADSHEET_ID", "").strip()
        ),
        "live_cricket": bool(
            os.getenv("CRICAPI_KEY", "").strip()
            or os.getenv("SERPER_API_KEY", "").strip()
        ),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        last = None
        try:
            last = latest_run()
        except Exception:  # noqa: BLE001 - serverless has no shared state
            pass
        obj = {
            "running": False,
            "last_error": None,
            "last_result": last,
            "channels": _channels_config(),
        }
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002 - silence request noise
        pass
