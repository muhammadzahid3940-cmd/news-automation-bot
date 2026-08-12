import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from vercel.routing.http import Request, Response  # noqa: E402

from pipeline import LATEST_FILE  # noqa: E402


def handler(request: Request) -> Response:
    if not LATEST_FILE.exists():
        return Response(json={"ok": False, "digest": ""})
    try:
        data = json.loads(LATEST_FILE.read_text(encoding="utf-8"))
        return Response(json={"ok": True, **data})
    except json.JSONDecodeError as exc:
        return Response(status_code=500, json={"ok": False, "error": str(exc)})
