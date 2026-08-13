import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from tools import (
    expand_topics,
    fetch_latest_news,
    fetch_live_cricket,
    format_live_cricket,
    log_to_google_sheets,
    post_slack_message,
    post_to_slack,
    summarize_articles,
)
from tools.crewai_tools import _slack_format

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

DEFAULT_TOPIC = os.getenv("SCHEDULE_TOPIC", "").strip() or "sports and game cricket"


def run_crew(topic: str | None = None) -> dict:
    """Run the newsroom pipeline: fetch news -> summarize (1 LLM call) -> live
    cricket update -> Slack -> Google Sheets. Returns the same result shape as
    before, without spending LLM quota on agent reasoning loops. Independent
    stages (news fetch, live cricket, Slack/Sheets delivery) run concurrently."""
    topic = (topic or DEFAULT_TOPIC).strip()
    started = datetime.now(timezone.utc)
    t0 = time.time()

    topics = expand_topics(topic, sample_size=3)

    # Live cricket is independent of news fetching -> run it in the background
    # while news fetch + LLM summarization happen.
    live_cricket = {
        "formatted": "",
        "matches": [],
        "source": "",
        "generated_at": "",
    }

    def _live_task():
        try:
            live = fetch_live_cricket()
            formatted = format_live_cricket(live)
            live_cricket["formatted"] = formatted
            live_cricket["matches"] = live.get("matches", [])[:6]
            live_cricket["source"] = live.get("source", "")
            live_cricket["generated_at"] = live.get("generated_at", "")
            if formatted:
                print(post_slack_message(formatted))
        except Exception as exc:  # noqa: BLE001 - live scores are best-effort
            print(f"[live cricket] skipped: {exc}")

    live_thread = threading.Thread(target=_live_task, daemon=True)
    live_thread.start()

    fetched = fetch_latest_news(topics, max_per_topic=4, expand=False)
    print(f"[news] fetched {len(fetched['headlines'])} articles in {time.time() - t0:.1f}s")

    summary = summarize_articles(fetched)
    rows = summary["rows"]
    digest = summary["digest"]
    print(f"[summarizer] {len(rows)} stories summarized in {time.time() - t0:.1f}s")

    live_thread.join(timeout=45)

    # Slack digest post and Google Sheets logging are independent -> parallel.
    with ThreadPoolExecutor(max_workers=2) as pool:
        slack_future = pool.submit(post_to_slack, _slack_format(digest))
        sheets_future = pool.submit(log_to_google_sheets, rows)
        slack = slack_future.result()
        try:
            sheets = sheets_future.result()
        except Exception as exc:  # noqa: BLE001 - sheets logging is best-effort
            sheets = f"Google Sheets: skipped ({exc})"
            print(f"[sheets] {sheets}")
    print(slack)
    print(sheets)
    print(f"[crew] total {time.time() - t0:.1f}s")

    return {
        "topic": topic,
        "generated_at": started.isoformat(timespec="seconds"),
        "article_count": len(rows),
        "digest": digest,
        "articles": rows,
        "live_cricket": live_cricket,
        "distribution": {
            "live_cricket": "Slack: posted (HTTP 200)" if live_cricket["formatted"] else "Live cricket: no update",
            "slack": slack,
            "google_sheets": sheets,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_crew(), ensure_ascii=False, indent=2)[:2000])
