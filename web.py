import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import pipeline
from db import latest_run
from page import PAGE

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

app = FastAPI(title="News Automation Bot", version="2.0.0")

STATE = {"running": False, "last_error": None, "last_result": None}
STATE_LOCK = threading.Lock()

PORT = int(os.getenv("WEB_PORT", "8000"))

# Lines from uvicorn's own access/startup logging - not pipeline output.
_UVICORN_NOISE = re.compile(
    r"(^\d{1,3}(\.\d{1,3}){3}:\d+ - \"|"
    r"^INFO:\s+(Started server|Waiting for application|Application startup|"
    r"Uvicorn running|Shutting down|Finished server process))"
)


class RunRequest(BaseModel):
    topic: str = "sports and game cricket"


def _friendly_error(exc: Exception) -> str:
    """Turn raw exceptions into a short, actionable message for the UI."""
    message = str(exc)
    if "RESOURCE_EXHAUSTED" in message or "quota" in message.lower():
        match = re.search(r"Please retry in ([\d.]+)s", message)
        hint = f" Retry suggested in ~{int(float(match.group(1)))}s." if match else ""
        return (
            "LLM quota exceeded (Gemini free tier allows ~20 requests/day)."
            + hint
            + " Set OPENAI_API_KEY in .env for more headroom, then run again."
        )
    return message[:300] + ("..." if len(message) > 300 else "")


def _clean_log_line(line: str) -> str | None:
    """Strip terminal escapes / box-drawing banners; None if nothing meaningful."""
    line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line)
    line = line.replace("\ufffd", "").strip()
    if not line:
        return None
    line = re.sub(r"^[\u2500-\u257f\u2580-\u259f\u00a0\s]+", "", line)
    line = re.sub(r"[\u2500-\u257f\u2580-\u259f\u00a0\s]+$", "", line).strip()
    if not line:
        return None
    box_only = re.sub(r"[\u2500-\u257f\u2580-\u259f\s]", "", line)
    if len(box_only) < 2:
        return None
    return line


def _sink_log(line: str) -> None:
    """Feed one captured output line into the run log, filtering server noise."""
    if _UVICORN_NOISE.match(line):
        return
    cleaned = _clean_log_line(line)
    if cleaned:
        pipeline.log(cleaned)


def _worker(topic: str):
    restore_stdout = pipeline.tee_stream(sys.stdout, _sink_log)
    restore_stderr = pipeline.tee_stream(sys.stderr, _sink_log)
    try:
        result = pipeline.run_pipeline(topic)
        with STATE_LOCK:
            STATE["last_result"] = result
            STATE["last_error"] = None
    except Exception as exc:  # noqa: BLE001
        with STATE_LOCK:
            STATE["last_error"] = _friendly_error(exc)
        pipeline.log(f"Error: {exc}")
    finally:
        restore_stdout()
        restore_stderr()
        with STATE_LOCK:
            STATE["running"] = False


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE


def _channels_config() -> dict:
    """Which distribution channels are actually configured right now."""
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
            os.getenv("CRICAPI_KEY", "").strip() or os.getenv("SERPER_API_KEY", "").strip()
        ),
    }


@app.get("/api/status")
def status():
    with STATE_LOCK:
        running = STATE["running"]
        error = STATE["last_error"]
        last = STATE["last_result"]
    return JSONResponse(
        {
            "running": running,
            "last_error": error,
            "last_result": last,
            "channels": _channels_config(),
        }
    )


@app.get("/api/logs")
def logs():
    return JSONResponse({"logs": pipeline.get_logs()})


@app.post("/api/logs/clear")
def logs_clear():
    pipeline.clear_logs()
    return JSONResponse({"ok": True})


@app.post("/api/run")
def run(request: RunRequest):
    topic = request.topic.strip() or pipeline.DEFAULT_TOPIC
    with STATE_LOCK:
        if STATE["running"]:
            raise HTTPException(status_code=409, detail="A run is already in progress")
        STATE["running"] = True
        STATE["last_error"] = None
    threading.Thread(target=_worker, args=(topic,), daemon=True).start()
    return JSONResponse({"status": "started", "topic": topic})


def _scheduler_loop():
    """Optional auto-refresh: re-run the pipeline every RUN_INTERVAL_MINUTES so
    the digest, Slack feed and live cricket card stay current. 0 disables it."""
    interval = int(os.getenv("RUN_INTERVAL_MINUTES", "0") or 0)
    if interval <= 0:
        return
    topic = pipeline.DEFAULT_TOPIC
    pipeline.log(f"Auto-refresh enabled \u2014 pipeline will run every {interval} min")
    while True:
        time.sleep(interval * 60)
        with STATE_LOCK:
            if STATE["running"]:
                continue
            STATE["running"] = True
            STATE["last_error"] = None
        pipeline.log(f"Scheduled auto-refresh run \u2014 topic: {topic}")
        threading.Thread(target=_worker, args=(topic,), daemon=True).start()


@app.get("/api/digest")
def digest():
    with STATE_LOCK:
        last = STATE["last_result"]
    if not last:
        try:
            latest = latest_run()
            if latest:
                return JSONResponse(latest)
        except Exception:  # noqa: BLE001 - fall back to the file copy
            pass
        file_latest = pipeline.LATEST_FILE
        if file_latest.exists():
            try:
                return JSONResponse(json.loads(latest.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
        return JSONResponse({"digest": "", "articles": []})
    return JSONResponse(last)


LIVE_CACHE = {"data": None, "ts": 0.0}
LIVE_CACHE_TTL = 20.0


@app.get("/api/live-cricket")
def live_cricket():
    """Fresh live cricket scores, cached briefly so the UI can poll cheaply."""
    now = time.time()
    if LIVE_CACHE["data"] is None or now - LIVE_CACHE["ts"] > LIVE_CACHE_TTL:
        try:
            from tools import fetch_live_cricket

            LIVE_CACHE["data"] = fetch_live_cricket()
            LIVE_CACHE["ts"] = now
        except Exception as exc:  # noqa: BLE001 - best-effort live data
            return JSONResponse(
                {
                    "source": "error",
                    "matches": [],
                    "note": str(exc),
                    "generated_at": "",
                }
            )
    return JSONResponse(LIVE_CACHE["data"])




def _cricket_ticker_loop():
    """Real-time cricket watcher: polls live scores and posts each change to
    Slack the moment it happens (deduped + throttled so the channel stays
    useful). No LLM calls - runs off the free CricAPI/web-search source."""
    if "cricket" not in pipeline.DEFAULT_TOPIC.lower():
        return
    if os.getenv("SLACK_LIVE", "1") in ("0", "false", "False", "no"):
        return
    interval = max(30, int(os.getenv("CRICKET_TICKER_SECONDS", "60") or 60))
    throttle = int(os.getenv("CRICKET_TICKER_THROTTLE_SECONDS", "180") or 180)
    last_key = ""
    last_post = 0.0
    pipeline.log(
        f"Real-time cricket ticker enabled - live updates to Slack every {interval}s"
    )
    while True:
        time.sleep(interval)
        try:
            from tools import fetch_live_cricket, format_live_cricket, post_slack_message

            live = fetch_live_cricket()
            key = json.dumps(live.get("matches", []), ensure_ascii=False)[:2000]
            if not key or key == last_key:
                continue
            last_key = key
            now = time.time()
            if now - last_post < throttle:
                continue
            body = format_live_cricket(live)
            if not body:
                continue
            stamp = datetime.now().strftime("%d %b %Y \u00b7 %H:%M:%S")
            message = f"\u26a1 *{stamp}*\n*Live cricket update*\n" + body
            print(post_slack_message(message))
            last_post = now
            pipeline.log(f"Live cricket changed - posted update to Slack")
        except Exception as exc:  # noqa: BLE001 - ticker must never kill the server
            print(f"[cricket ticker] skipped: {exc}")


if __name__ == "__main__":
    threading.Thread(target=_scheduler_loop, daemon=True).start()
    threading.Thread(target=_cricket_ticker_loop, daemon=True).start()
    print(f"News Automation Bot UI: http://localhost:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
