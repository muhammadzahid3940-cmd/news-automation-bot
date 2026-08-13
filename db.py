import json
import os
from datetime import datetime, timezone


def database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def _connect():
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(
        database_url(), row_factory=dict_row, connect_timeout=15
    )


def _now_iso(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.astimezone(timezone.utc) if value else None


def init_db() -> None:
    """Create the runs/articles tables if they do not exist. No-op when
    DATABASE_URL is not configured."""
    if not database_url():
        return
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id BIGSERIAL PRIMARY KEY,
                    topic TEXT NOT NULL,
                    generated_at TIMESTAMPTZ NOT NULL,
                    digest TEXT NOT NULL,
                    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id BIGSERIAL PRIMARY KEY,
                    run_id BIGINT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    headline TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source TEXT,
                    url TEXT,
                    published_at TEXT
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_articles_run ON articles(run_id)"
            )
        conn.commit()


def save_run(result: dict) -> None:
    """Persist a pipeline result (one run + its articles) to Postgres.
    No-op when DATABASE_URL is not configured."""
    if not database_url():
        return
    init_db()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs (topic, generated_at, digest, meta)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    result.get("topic", ""),
                    _now_iso(result.get("generated_at")),
                    result.get("digest", ""),
                    json.dumps(
                        {
                            "live_cricket": result.get("live_cricket"),
                            "distribution": result.get("distribution"),
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
            run_id = cur.fetchone()["id"]
            for article in result.get("articles", []):
                cur.execute(
                    """
                    INSERT INTO articles
                        (run_id, headline, summary, source, url, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        article.get("headline", ""),
                        article.get("summary", ""),
                        article.get("source", ""),
                        article.get("url", ""),
                        article.get("date", ""),
                    ),
                )
        conn.commit()


def latest_run() -> dict | None:
    """Return the most recent stored run in the same shape as run_pipeline.
    None when DATABASE_URL is not configured or the DB has no rows."""
    if not database_url():
        return None
    init_db()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, topic, generated_at, digest, meta
                FROM runs
                ORDER BY id DESC
                LIMIT 1
                """
            )
            run = cur.fetchone()
            if not run:
                return None
            cur.execute(
                """
                SELECT headline, summary, source, url, published_at AS date
                FROM articles
                WHERE run_id = %s
                ORDER BY id
                """,
                (run["id"],),
            )
            articles = cur.fetchall()
    meta = run["meta"] or {}
    generated_at = run["generated_at"]
    return {
        "topic": run["topic"],
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "article_count": len(articles),
        "digest": run["digest"],
        "articles": articles,
        "live_cricket": meta.get(
            "live_cricket",
            {"formatted": "", "matches": [], "source": "", "generated_at": ""},
        ),
        "distribution": meta.get("distribution", {}),
    }
