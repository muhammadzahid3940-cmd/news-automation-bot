import json
import os
from pathlib import Path

import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.chdir(ROOT)

from vercel.routing.http import Request, Response  # noqa: E402

from pipeline import run_pipeline  # noqa: E402


def handler(request: Request) -> Response:
    try:
        topic = None
        if request.method == "GET":
            topic = request.query_params.get("topic") or None
        else:
            try:
                body = json.loads(request.body or "{}")
                topic = body.get("topic") or None
            except json.JSONDecodeError:
                pass

        result = run_pipeline(topic)
        return Response(json={"ok": True, "topic": result["topic"], "article_count": result["article_count"]})

    except Exception as exc:  # noqa: BLE001
        return Response(status_code=500, json={"ok": False, "error": str(exc)})
