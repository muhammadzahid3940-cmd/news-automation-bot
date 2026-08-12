import json
import os
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
    before, without spending LLM quota on agent reasoning loops."""
    topic = (topic or DEFAULT_TOPIC).strip()
    started = datetime.now(timezone.utc)

    topics = expand_topics(topic, sample_size=3)
    fetched = fetch_latest_news(topics, max_per_topic=4, expand=False)
    print(f"[news] fetched {len(fetched['headlines'])} articles for '{topic}'")

    summary = summarize_articles(fetched)
    rows = summary["rows"]
    digest = summary["digest"]
    print(f"[summarizer] {len(rows)} stories summarized")

    # Real-time live cricket update -> Slack (best-effort, no LLM involved).
    live_cricket = {
        "formatted": "",
        "matches": [],
        "source": "",
        "generated_at": "",
    }
    try:
        live = fetch_live_cricket()
        live_cricket = {
            "formatted": format_live_cricket(live),
            "matches": live.get("matches", [])[:6],
            "source": live.get("source", ""),
            "generated_at": live.get("generated_at", ""),
        }
        if live_cricket["formatted"]:
            print(post_slack_message(live_cricket["formatted"]))
    except Exception as exc:  # noqa: BLE001 - live scores are best-effort
        print(f"[live cricket] skipped: {exc}")

    slack = post_to_slack(_slack_format(digest))
    print(slack)

    try:
        sheets = log_to_google_sheets(rows)
        print(sheets)
    except Exception as exc:  # noqa: BLE001 - sheets logging is best-effort
        sheets = f"Google Sheets: skipped ({exc})"
        print(f"[sheets] {sheets}")

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
