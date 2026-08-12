import json
import os
import sys
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from crew import run_crew

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "output"
DIGEST_FILE = OUTPUT_DIR / "digest.md"
LATEST_FILE = OUTPUT_DIR / "latest.json"

DEFAULT_TOPIC = os.getenv("SCHEDULE_TOPIC", "").strip() or "sports and game cricket"

# ---------------------------------------------------------------------------
# In-memory run log (shared with the web UI)
# ---------------------------------------------------------------------------
LOG_MAX = 500
_LOGS = deque(maxlen=LOG_MAX)
_LOG_LOCK = threading.Lock()


def log(message: str) -> None:
    """Append a timestamped line to the run log shown in the web UI."""
    with _LOG_LOCK:
        _LOGS.append(
            {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "msg": message,
            }
        )


def get_logs() -> list[dict]:
    with _LOG_LOCK:
        return list(_LOGS)


def clear_logs() -> None:
    with _LOG_LOCK:
        _LOGS.clear()


# ---------------------------------------------------------------------------
# Stdout capture: let the web worker stream pipeline prints into the run log
# ---------------------------------------------------------------------------
class _Tee:
    """Wraps a stream so complete lines are both forwarded and logged."""

    def __init__(self, stream, sink):
        self._stream = stream
        self._sink = sink
        self._buffer = ""

    def write(self, data: str) -> int:
        self._stream.write(data)
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if line:
                self._sink(line)
        return len(data)

    def flush(self) -> None:
        self._stream.flush()


def tee_stream(stream, sink):
    """Replace sys.stdout/sys.stderr with a tee. Returns a restore function."""
    name = "stdout" if stream is sys.stdout else "stderr"
    wrapper = _Tee(stream, sink)
    original = getattr(sys, name)
    setattr(sys, name, wrapper)
    return lambda: setattr(sys, name, original)


def _clean_surrogates(value):
    """Recursively replace lone surrogate characters with U+FFFD so strings
    survive UTF-8 encoding (files, logs, JSON responses)."""
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace").decode("utf-8")
    if isinstance(value, dict):
        return {k: _clean_surrogates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean_surrogates(v) for v in value]
    return value


def run_pipeline(topic: str | None = None, save: bool = True) -> dict:
    """Run the CrewAI newsroom pipeline: fetch news -> summarize -> Slack -> Sheets."""
    topic = (topic or DEFAULT_TOPIC).strip()
    log(f"Run started \u2014 topic: {topic}")
    try:
        result = _clean_surrogates(run_crew(topic))
        log(f"Run complete \u2014 {result['article_count']} stories, digest generated")
        log(f"    -> {result['distribution']['slack']}")
        log(f"    -> {result['distribution']['google_sheets']}")
    except Exception as exc:  # noqa: BLE001
        log(f"Run failed: {exc}")
        raise

    if save:
        OUTPUT_DIR.mkdir(exist_ok=True)
        DIGEST_FILE.write_text(result["digest"], encoding="utf-8")
        LATEST_FILE.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log("Digest saved to output/latest.json")

    return result


if __name__ == "__main__":
    result = run_pipeline()
    print("\n--- DIGEST ---")
    print(result["digest"])
    print(f"\nSaved to {DIGEST_FILE}")
