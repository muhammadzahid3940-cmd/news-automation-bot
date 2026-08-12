import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_TOPICS = "cricket"
CRICKET_QUERIES = "cricket match today, cricket T20, cricket test series, cricket world cup, cricket news"
SERPER_NEWS_URL = "https://google.serper.dev/news"

# ---------------------------------------------------------------------------
# Rotating universe of officially recognized world sports; each "sports" run
# covers a slice so every sport gets searched over consecutive runs.
# ---------------------------------------------------------------------------
ALL_SPORTS = [
    # --- IOC Summer Olympic sports & disciplines ---
    "archery", "recurve archery", "compound archery", "field archery",
    "artistic swimming", "synchronized swimming", "solo artistic swimming",
    "duet artistic swimming", "team artistic swimming", "mixed duet artistic swimming",
    "athletics", "track and field", "sprint", "100 metres", "200 metres", "400 metres",
    "800 metres", "1500 metres", "5000 metres", "10000 metres", "marathon",
    "ultramarathon", "hurdles", "110 metres hurdles", "400 metres hurdles",
    "3000 metres steeplechase", "relay race", "4x100 metres relay", "4x400 metres relay",
    "race walking", "20 kilometres race walk", "50 kilometres race walk",
    "long jump", "triple jump", "high jump", "pole vault", "shot put", "discus throw",
    "javelin throw", "hammer throw", "decathlon", "heptathlon", "cross country running",
    "mountain running", "trail running", "parkour", "badminton", "singles badminton",
    "doubles badminton", "mixed doubles badminton", "baseball", "softball",
    "fastpitch softball", "slowpitch softball", "basketball", "5x5 basketball",
    "3x3 basketball", "wheelchair basketball", "boxing", "amateur boxing",
    "professional boxing", "women's boxing", "breaking", "breakdancing",
    "canoe sprint", "canoe slalom", "kayak sprint", "kayak slalom", "canoe marathon",
    "canoe polo", "canoe freestyle", "dragon boat racing", "cricket", "test cricket",
    "one day cricket", "T20 cricket", "T20 world cup", "women's cricket",
    "beach cricket", "cycling road race", "cycling time trial", "track cycling",
    "sprint cycling", "keirin", "team pursuit", "omnium cycling", "mountain bike racing",
    "cross country cycling", "downhill cycling", "BMX racing", "BMX freestyle",
    "cyclocross", "diving", "10 metre platform diving", "3 metre springboard diving",
    "synchronized diving", "high diving", "equestrian dressage", "equestrian eventing",
    "show jumping", "fencing", "foil fencing", "epee fencing", "sabre fencing",
    "team fencing", "wheelchair fencing", "field hockey", "indoor hockey",
    "football", "soccer", "association football", "women's football", "futsal",
    "beach soccer", "five-a-side football", "arena football", "freestyle football",
    "powerchair football", "golf", "mini golf", "disc golf", "gymnastics",
    "artistic gymnastics", "rhythmic gymnastics", "trampoline gymnastics",
    "tumbling gymnastics", "acrobatic gymnastics", "aerobic gymnastics",
    "handball", "beach handball", "wheelchair handball", "judo", "karate",
    "karate kata", "karate kumite", "modern pentathlon", "rowing", "single sculls",
    "double sculls", "coxless four", "coxed eight", "lightweight rowing",
    "indoor rowing", "coastal rowing", "ocean rowing", "rugby union", "rugby sevens",
    "rugby league", "touch rugby", "tag rugby", "wheelchair rugby",
    "sailing", "match racing sailing", "team racing sailing", "windsurfing",
    "kiteboarding", "ice sailing", "shooting", "10 metre air pistol", "10 metre air rifle",
    "25 metre pistol", "50 metre rifle", "trap shooting", "skeet shooting",
    "double trap shooting", "running target shooting", "practical shooting",
    "skateboarding", "skateboard street", "skateboard park", "skateboard vert",
    "sport climbing", "bouldering", "lead climbing", "speed climbing",
    "surfing", "shortboard surfing", "longboard surfing", "standup paddleboard",
    "paddleboarding", "swimming", "freestyle swimming", "butterfly swimming",
    "backstroke", "breaststroke", "individual medley", "medley relay",
    "open water swimming", "marathon swimming", "finswimming", "para swimming",
    "table tennis", "singles table tennis", "doubles table tennis",
    "mixed doubles table tennis", "para table tennis", "taekwondo", "tennis",
    "singles tennis", "doubles tennis", "mixed doubles tennis", "wheelchair tennis",
    "beach tennis", "real tennis", "racketlon", "triathlon", "duathlon", "aquathlon",
    "winter triathlon", "swimrun", "paratriathlon", "volleyball", "beach volleyball",
    "snow volleyball", "sitting volleyball", "water polo", "weightlifting",
    "snatch weightlifting", "clean and jerk weightlifting", "powerlifting",
    "bodybuilding", "wrestling", "freestyle wrestling", "greco roman wrestling",
    "beach wrestling", # --- IOC Winter Olympic sports & disciplines ---
    "alpine skiing", "slalom skiing", "giant slalom", "super giant slalom",
    "downhill skiing", "alpine combined", "biathlon", "bobsleigh", "two man bobsleigh",
    "four man bobsleigh", "monobob", "cross country skiing", "skiathlon",
    "sprint cross country skiing", "team sprint skiing", "curling", "mixed doubles curling",
    "wheelchair curling", "figure skating", "singles figure skating", "pairs figure skating",
    "ice dance", "freestyle skiing", "freestyle aerials", "freestyle moguls",
    "ski cross", "ski big air", "ski halfpipe", "ski slopestyle", "ice hockey",
    "para ice hockey", "sledge hockey", "luge", "singles luge", "doubles luge",
    "nordic combined", "short track speed skating", "speed skating",
    "skeleton", "ski jumping", "large hill ski jumping", "snowboard halfpipe",
    "snowboard slopestyle", "snowboard big air", "snowboard cross", "snowboard parallel slalom",
    "snowboard parallel giant slalom", "telemark skiing",
    # --- GAISF / SportAccord member federations (recognized worldwide) ---
    "aikido", "air sports", "paragliding", "hang gliding", "skydiving", "parachuting",
    "paramotoring", "paraski", "alpinism", "mountaineering", "ice climbing",
    "american football", "flag football", "armwrestling", "aussie rules football",
    "australian rules football", "auto racing", "formula one", "rally racing",
    "stock car racing", "touring car racing", "endurance racing", "drag racing",
    "kart racing", "drift racing", "hillclimb racing", "bandy", "basque pelota",
    "jai alai", "billiards", "eight ball pool", "nine ball pool", "ten ball pool",
    "straight pool", "one pocket pool", "bank pool", "carom billiards",
    "three cushion billiards", "snooker", "english billiards", "bocce",
    "petanque", "lawn bowls", "bowling", "ten pin bowling", "five pin bowling",
    "candlepin bowling", "duckpin bowling", "boules", "brazilian jiu jitsu",
    "bridge", "contract bridge", "duplicate bridge", "capoeira", "casting sport",
    "chess", "classical chess", "rapid chess", "blitz chess", "correspondence chess",
    "chinese chess", "xiangqi", "shogi", "go", "othello", "renju", "gomoku",
    "backgammon", "mahjong", "scrabble", "draughts", "checkers", "international draughts",
    "american checkers", "russian draughts", "pool", "croquet", "association croquet",
    "golf croquet", "curling", "cycle polo", "cycle speedway", "dancesport",
    "ballroom dancing", "latin dancing", "rock n roll dancing", "darts",
    "steel tip darts", "soft tip darts", "dog agility", "equestrian vaulting",
    "equestrian endurance", "reining", "barrel racing", "rodeo", "bull riding",
    "bronc riding", "calf roping", "steer wrestling", "team roping",
    "horse racing", "thoroughbred racing", "steeplechase racing", "harness racing",
    "e-sports", "electronic sports", "esports", "fistball", "floorball",
    "footbag", "hacky sack", "go", "goalball", "grae", "grenade throwing",
    "gym ball", "hurling", "gaelic football", "ice stock sport", "indoor skydiving",
    "jet ski racing", "ju-jitsu", "jujitsu", "ne waza jujitsu", "kabaddi",
    "beach kabaddi", "kendo", "korfball", "kung fu", "wushu", "wushu taolu",
    "wushu sanda", "kyudo", "lacrosse", "field lacrosse", "box lacrosse",
    "women's lacrosse", "intercrosse", "lifesaving", "pool lifesaving",
    "ocean lifesaving", "surf lifesaving", "martial arts", "mixed martial arts",
    "mma", "muay thai", "kickboxing", "savate", "sambo", "silat", "hapkido",
    "tang soo do", "vovinam", "sumo", "sumo wrestling", "mind sports",
    "mini golf", "motocross", "supercross", "speedway racing", "enduro racing",
    "motorcycle trials", "motoGP", "motorcycle racing", "netball", "orienteering",
    "foot orienteering", "ski orienteering", "mountain bike orienteering",
    "trail orienteering", "paddle tennis", "padel", "pelota", "pickleball",
    "polo", "arena polo", "canoe polo", "powerboating", "offshore powerboat racing",
    "prak", "quadbike racing", "quidditch", "quadball", "racquetball", "rafting",
    "whitewater rafting", "rock climbing", "roller derby", "roller skating",
    "artistic roller skating", "inline speed skating", "inline hockey", "roller hockey",
    "rink hockey", "aggressive inline skating", "roller speed skating",
    "row", "rugby", "sepak takraw", "shuffleboard", "skibob", "snowbike",
    "squash", "singles squash", "doubles squash", "hardball squash",
    "soft tennis", "sport climbing", "tchoukball", "tug of war",
    "underwater hockey", "underwater rugby", "underwater football",
    "underwater target shooting", "volleyball", "wakeboarding", "cable wakeboarding",
    "wake surf", "waterskiing", "water ski slalom", "water ski tricks",
    "water ski jumping", "barefoot skiing", "kneeboarding", "wakeboard",
    "windsurfing", "paddleboard racing",
    # --- Paralympic & adaptive sports ---
    "paralympic sports", "boccia", "goalball", "para athletics", "para archery",
    "para badminton", "para canoe", "para cycling", "para equestrian",
    "para judo", "para powerlifting", "para rowing", "para shooting",
    "para taekwondo", "para triathlon", "wheelchair racing", "powerchair hockey",
    "sledge hockey", "amputee football", "blind football", "deaf sports",
    "deaf basketball", "paralympic alpine skiing", "paralympic biathlon",
    "paralympic cross country skiing", "paralympic snowboard",
    # --- Traditional & regional sports recognized by national federations ---
    "arbit", "beach flag", "boat racing", "boomerang", "buzkashi", "cammag",
    "cane fencing", "cestoball", "conker", "corkball", "cumbia soccer",
    "elephant polo", "falconry", "fencing", "folk wrestling", "glima", "gotball",
    "gourd ball", "hapkido", "harpastum", "headis", "ippon", "jianzi",
    "kabaddi", "kickball", "killerball", "kinnik", "knattleikr", "kobudo",
    "ladu", "longue paume", "lucha libre", "maniskiak", "marn grook",
    "mesoamerican ballgame", "mesoamerican handball", "nana", "ballooning",
    "pato", "pesapallo", "shinty", "sipa", "sla nam", "sherpa climbing",
    "snookball", "street hockey", "stoolball", "swing", "table football",
    "table soccer", "tamburello", "thorn game", "tossball", "unicycling",
    "unicycle hockey", "unicycle basketball", "vall subalp",
]

RULES_SPORTS_WORDS = ("sport", "sports", "games", "game", "all", "every", "general")
SPORTS_ROTATION_FILE = (
    Path(__file__).resolve().parent.parent / "output" / ".sports_rotation"
)
SPORTS_SAMPLE_SIZE = 3


def rotate_sports(sample_size: int = SPORTS_SAMPLE_SIZE) -> str:
    """Round-robin slice of ALL_SPORTS so every officially recognized sport in
    the world gets searched over consecutive runs."""
    try:
        offset = int(SPORTS_ROTATION_FILE.read_text().strip() or 0)
    except (OSError, ValueError):
        offset = 0
    names = len(ALL_SPORTS)
    chunk = [ALL_SPORTS[(offset + i) % names] for i in range(min(sample_size, names))]
    try:
        SPORTS_ROTATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        SPORTS_ROTATION_FILE.write_text(str((offset + len(chunk)) % names))
    except OSError:
        pass
    return ", ".join(sorted(set(chunk)))


def expand_topics(user_input: str, sample_size: int = SPORTS_SAMPLE_SIZE) -> str:
    """Turn a topic query into a comma-separated list of search phrases.
    Cricket -> cricket beats; broad 'sports' queries -> a rotating sample of all
    officially recognized world sports; otherwise the raw topic is returned."""
    text = (user_input or "").strip().lower()
    if "cricket" in text:
        return ", ".join(CRICKET_QUERIES.split(",")[:3])
    tokens = {t.strip(".,!?;:()") for t in text.split()}
    if tokens & set(RULES_SPORTS_WORDS):
        return rotate_sports(sample_size)
    return user_input.strip()


def _env(*names):
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Tool 1: Fetch trending news
# ---------------------------------------------------------------------------
def fetch_latest_news(
    topics: str = DEFAULT_TOPICS,
    max_per_topic: int = 5,
    expand: bool = True,
    max_topics: int = 10,
) -> dict:
    """Search Google News (via Serper) for the latest trending headlines for one
    or more comma-separated topics. When expand=True, broad 'sports' queries are
    expanded to a rotating sample of all officially recognized world sports.
    Returns {"topics": [...], "headlines": [...]} with headline, link, source,
    snippet and date per article."""
    api_key = _env("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "SERPER_API_KEY is not set. Get a free key at https://serper.dev and add it to .env"
        )

    if expand:
        topics = expand_topics(topics)
    topics_list = [t.strip() for t in topics.split(",") if t.strip()] or [
        "artificial intelligence"
    ]
    if max_topics > 0:
        topics_list = topics_list[:max_topics]
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    headlines = []
    for topic in topics_list:
        resp = requests.post(
            SERPER_NEWS_URL,
            headers=headers,
            json={"q": f"trending news {topic}", "num": max_per_topic, "gl": "us"},
            timeout=30,
        )
        resp.raise_for_status()
        for item in resp.json().get("news", []):
            source = item.get("source")
            if isinstance(source, dict):
                source = source.get("name")
            headlines.append(
                {
                    "headline": item.get("title"),
                    "link": item.get("link"),
                    "source": source,
                    "snippet": item.get("snippet", ""),
                    "date": item.get("date", ""),
                }
            )

    return {"topics": topics_list, "headlines": dedupe_articles(headlines)}


# ---------------------------------------------------------------------------
# Tool 2: Intelligent summarizer (LLM with automatic multi-key failover)
# ---------------------------------------------------------------------------
def _llm_candidates() -> list[tuple[str, object, str, str]]:
    """Return (provider, client, model, label) candidates, one per configured key
    and Gemini model. Gemini free tier limits each MODEL to ~20 requests/day, so
    several models are registered and the retry loop falls over to the next model
    when one is rate limited. Identical keys/models are deduplicated."""
    candidates = []
    seen = set()

    def _add(provider, client, model, label, key, model_name=None):
        identity = (key, model_name or model)
        if not key or identity in seen:
            return
        seen.add(identity)
        candidates.append((provider, client, model, label))

    openai_key = _env("OPENAI_API_KEY")
    if openai_key:
        from openai import OpenAI

        _add(
            "openai",
            OpenAI(api_key=openai_key),
            _env("OPENAI_MODEL") or "gpt-4o-mini",
            "OpenAI",
            openai_key,
        )

    gemini_models = [
        m.strip()
        for m in _env("GEMINI_MODELS", "MODEL_NAME", "GEMINI_MODEL_NAME").split(",")
        if m.strip()
    ] or [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
    ]
    gemini_models = [
        m.replace("gemini/", "").replace("models/", "") for m in gemini_models
    ]
    for label, name in (("Google", "GOOGLE_API_KEY"), ("Gemini", "GEMINI_API_KEY")):
        key = _env(name)
        if key:
            from google import genai

            for model in gemini_models:
                _add("gemini", genai.Client(api_key=key), model, label, key, model)

    if not candidates:
        raise RuntimeError(
            "No LLM API key found for the summarizer. Set OPENAI_API_KEY "
            "or GOOGLE_API_KEY in .env"
        )
    return candidates


def _is_rate_limit(message: str) -> bool:
    return (
        "429" in message
        or "RESOURCE_EXHAUSTED" in message
        or "quota" in message.lower()
        or "rate limit" in message.lower()
    )


def _retry_delay(message: str):
    match = re.search(r"retry in ([\d.]+)s", message, re.IGNORECASE)
    if not match:
        match = re.search(r"retryDelay.*?(\d+)s", message, re.IGNORECASE)
    if not match:
        match = re.search(r"try again in ([\d.]+)s", message, re.IGNORECASE)
    if not match:
        match = re.search(r"Please retry in ([\d.]+)s", message, re.IGNORECASE)
    return match


def _generate_with_retry(candidates: list, contents: str) -> str:
    """Generate with automatic key failover: on a rate limit, switch to the next
    configured key immediately; only wait once every key has been limited."""
    last_error = None
    max_attempts = len(candidates) * 6
    attempts = 0
    while attempts < max_attempts:
        cycle_limited = False
        for provider, client, model, label in candidates:
            attempts += 1
            try:
                if provider == "gemini":
                    return client.models.generate_content(model=model, contents=contents).text
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": contents}],
                    temperature=0.4,
                    max_tokens=2048,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:  # noqa: BLE001 - surface friendly error
                last_error = exc
                message = str(exc)
                if "404" in message or "no longer available" in message or "not found" in message:
                    print(
                        f"    [summarizer] model '{model}' unavailable - skipping"
                    )
                    continue
                if _is_rate_limit(message):
                    cycle_limited = True
                    if len(candidates) > 1:
                        print(
                            f"    [summarizer] '{label}/{model}' rate limited - switching"
                        )
                    continue
                match = _retry_delay(message)
                wait = min(70, int(float(match.group(1))) + 2) if match else 15
                print(
                    f"    [summarizer] transient error, waiting {wait}s "
                    f"(attempt {attempts}/{max_attempts})"
                )
                time.sleep(wait)
        if cycle_limited:
            match = _retry_delay(str(last_error))
            wait = min(70, int(float(match.group(1))) + 2) if match else 15
            print(
                f"    [summarizer] all keys rate limited, waiting {wait}s before retrying"
            )
            time.sleep(wait)
    raise RuntimeError(f"LLM summarization failed after retries: {last_error}")


def summarize_articles(articles: dict) -> dict:
    """Summarize fetched articles into a markdown digest plus structured rows
    (headline, summary, source, url) for logging. One batched LLM call."""
    headlines = dedupe_articles(articles.get("headlines", []))
    if not headlines:
        return {
            "digest": "# Daily News Digest\n\nNo articles found for the requested topic.",
            "rows": [],
            "articles": [],
        }

    payload = json.dumps(
        [
            {
                "headline": a.get("headline"),
                "link": a.get("link"),
                "source": a.get("source"),
                "date": a.get("date", ""),
            }
            for a in headlines
        ],
        ensure_ascii=False,
        indent=1,
    )

    prompt = (
        "You are an expert news summarizer. Below is a JSON list of news articles "
        f"for the topic: {articles.get('topics', ['news'])}.\n"
        "Write a concise, factual 2-3 sentence summary for EACH article. Remove "
        "duplicate coverage. Return ONLY a valid JSON array (no markdown fences) of "
        'objects with keys: "headline", "summary", "source", "url".\n\n'
        f"ARTICLES:\n{payload}"
    )

    candidates = _llm_candidates()
    raw = _generate_with_retry(candidates, prompt).strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)

    try:
        summaries = json.loads(raw)
    except json.JSONDecodeError:
        summaries = []

    if not isinstance(summaries, list):
        summaries = []

    rows = []
    used_urls = set()
    for item in summaries:
        url = (item.get("url") or "").strip()
        if not url or url in used_urls:
            continue
        used_urls.add(url)
        rows.append(
            {
                "date": _now_iso(),
                "headline": (item.get("headline") or "").strip(),
                "summary": (item.get("summary") or "").strip(),
                "source": (item.get("source") or "").strip(),
                "url": url,
            }
        )

    if not rows:
        rows = [
            {
                "date": _now_iso(),
                "headline": a.get("headline") or "",
                "summary": a.get("snippet") or "",
                "source": a.get("source") or "",
                "url": a.get("link") or "",
            }
            for a in headlines
        ]

    # Live Slack updates: post each summary to Slack the moment it is ready, so
    # the channel gets real-time updates instead of a single end-of-run digest.
    if rows and _env("SLACK_WEBHOOK_URL") and _env("SLACK_LIVE", "1") not in (
        "0",
        "false",
        "False",
        "no",
    ):
        max_live = int(_env("SLACK_LIVE_MAX") or "15")
        for row in rows[:max_live]:
            stamp = datetime.now().strftime("%d %b %Y \u00b7 %H:%M:%S")
            source = f" ({row['source']})" if row["source"] else ""
            link = f"<{row['url']}|Full story>" if row["url"] else ""
            try:
                post_slack_message(
                    f"\u26a1 *{stamp}*\n"
                    f"*{row['headline']}*{source}\n"
                    f"{row['summary']}\n\n"
                    f"{link}"
                )
                print(
                    f"    [live slack] posted: {row['headline'][:60]}"
                )
            except Exception as exc:  # noqa: BLE001 - keep summarizing if a post fails
                print(f"    [live slack] post failed: {exc}")
                break

    topic = ", ".join(articles.get("topics", []))
    lines = [
        f"# Daily News Digest - {topic}",
        f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        f"{len(rows)} fresh articles on {topic}.",
        "",
        "## Top Stories",
        "",
    ]
    for row in rows:
        link = f"[link]({row['url']})" if row["url"] else ""
        source = f" ({row['source']})" if row["source"] else ""
        lines.append(f"- **{row['headline']}**{source} {link}")
        lines.append(f"  {row['summary']}")
        lines.append("")

    return {
        "digest": "\n".join(lines).strip(),
        "rows": rows,
        "articles": headlines,
    }


# ---------------------------------------------------------------------------
# Tool 3: Slack integration
# ---------------------------------------------------------------------------
def post_slack_message(text: str) -> str:
    """Post one message to Slack via webhook. Skips gracefully if not configured."""
    slack_url = _env("SLACK_WEBHOOK_URL")
    if not slack_url:
        return "Slack: not configured (set SLACK_WEBHOOK_URL to enable)"
    resp = requests.post(
        slack_url,
        json={"text": text[:3900]},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Slack webhook failed: HTTP {resp.status_code} - {resp.text[:200]}")
    return f"Slack: posted (HTTP {resp.status_code})"


def post_to_slack(digest: str) -> str:
    """Post the digest to Slack via webhook. Skips gracefully if not configured."""
    return post_slack_message(digest)


# ---------------------------------------------------------------------------
# Tool 3b: Live cricket match details (real-time scores)
# ---------------------------------------------------------------------------
SERPER_SEARCH_URL = "https://google.serper.dev/search"
CRICAPI_URL = "https://api.cricapi.com/v1/currentMatches"


def _score_text(score_lines: list) -> str:
    parts = []
    for s in score_lines or []:
        inning = s.get("inning", "")
        runs = s.get("r", s.get("run", ""))
        wickets = s.get("w", "")
        overs = s.get("o", s.get("overs", ""))
        parts.append(
            f"{inning}: {runs}/{wickets} ({overs} ov)"
        )
    return " | ".join(parts)


def _score_from_text(text: str) -> str:
    """Pull a score like 'IND 245/4' out of a headline/snippet if present."""
    match = re.search(
        r"([A-Za-z\u00c0-\u017f]{2,8})\s+(\d{1,3})/(\d{1,2})(?:\s*\(([^)]*)\))?",
        text,
    )
    if match:
        return f"{match.group(1)} {match.group(2)}/{match.group(3)}"
    return ""


def fetch_live_cricket() -> dict:
    """Fetch current live cricket match details in real time. Uses CricAPI when
    CRICAPI_KEY is set (accurate, structured), otherwise falls back to a Serper
    web search for live-score headlines/snippets."""
    cricapi_key = _env("CRICAPI_KEY")
    if cricapi_key:
        resp = requests.get(
            CRICAPI_URL, params={"apikey": cricapi_key}, timeout=30
        )
        resp.raise_for_status()
        matches = []
        for item in (resp.json().get("data") or [])[:8]:
            status = item.get("status") or ""
            if not item.get("score"):
                continue
            matches.append(
                {
                    "title": item.get("name") or status,
                    "score": _score_text(item.get("score")),
                    "status": status,
                    "venue": item.get("venue", ""),
                    "link": item.get("matchUrl", ""),
                }
            )
        if matches:
            return {"source": "CricAPI", "matches": matches, "generated_at": _now_iso()}

    api_key = _env("SERPER_API_KEY")
    if not api_key:
        return {
            "source": "none",
            "matches": [],
            "note": "No live cricket source configured: set CRICAPI_KEY (free at cricapi.com) or SERPER_API_KEY",
            "generated_at": _now_iso(),
        }
    resp = requests.post(
        SERPER_SEARCH_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": "cricket live score today", "num": 5, "gl": "in"},
        timeout=30,
    )
    resp.raise_for_status()
    matches = []
    for item in resp.json().get("organic", [])[:5]:
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""
        score = _score_from_text(f"{title} {snippet}") or _score_from_text(snippet)
        if not title:
            continue
        matches.append(
            {
                "title": title,
                "score": score,
                "status": snippet[:140],
                "venue": "",
                "link": item.get("link", ""),
            }
        )
    return {"source": "Serper", "matches": matches, "generated_at": _now_iso()}


def format_live_cricket(data: dict) -> str:
    """Human-readable live cricket update for Slack."""
    matches = data.get("matches") or []
    stamp = data.get("generated_at", "")[:16].replace("T", " ")
    if not matches:
        note = data.get("note", "No live cricket matches right now.")
        return f"\ud83c\udfcf CRICKET UPDATE ({stamp})\n{note}"
    lines = [
        f"\ud83c\udfcf LIVE CRICKET \u2014 {stamp} (via {data.get('source', 'web')})"
    ]
    for m in matches[:6]:
        lines.append(f"\u2022 *{m['title']}*")
        if m.get("score"):
            lines.append(f"  {m['score']}")
        if m.get("status"):
            lines.append(f"  {m['status'][:100]}")
        if m.get("link"):
            lines.append(f"  <{m['link']}|details>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: Google Sheets logger
# ---------------------------------------------------------------------------
def _sheets_client():
    import gspread

    json_content = _env("GOOGLE_SERVICE_ACCOUNT_JSON")
    json_file = _env("GOOGLE_SERVICE_ACCOUNT_FILE")
    if json_content:
        return gspread.service_account_from_dict(json.loads(json_content))
    json_file = json_file or _env("GOOGLE_APPLICATION_CREDENTIALS")
    if json_file:
        return gspread.service_account(filename=json_file)
    raise RuntimeError(
        "Google Sheets credentials missing: set GOOGLE_SERVICE_ACCOUNT_JSON "
        "(inline JSON) or GOOGLE_SERVICE_ACCOUNT_FILE / "
        "GOOGLE_APPLICATION_CREDENTIALS (path to service account .json)"
    )


def log_to_google_sheets(rows: list[dict]) -> str:
    """Append structured rows (Date, Headline, Summary, Source URL) to Google Sheets."""
    if not rows:
        return "Google Sheets: nothing to log"
    sheet_id = _env("GOOGLE_SHEET_ID", "SPREADSHEET_ID")
    if not sheet_id:
        return "Google Sheets: not configured (set GOOGLE_SHEET_ID)"
    try:
        client = _sheets_client()
    except RuntimeError as exc:
        return f"Google Sheets: skipped ({exc})"

    try:
        worksheet = client.open_by_key(sheet_id).sheet1
    except Exception as exc:  # noqa: BLE001 - report the underlying cause clearly
        cause = getattr(exc, "__cause__", None)
        detail = str(cause) or str(exc) or type(exc).__name__
        hint = ""
        if "has not been used" in detail or "disabled" in detail:
            hint = (
                " Enable the Google Sheets API at "
                "https://console.developers.google.com/apis/api/sheets.googleapis.com/"
                "overview?project=news-update-505306"
            )
        elif "permission" in detail.lower() or "not found" in detail.lower():
            hint = (
                " Share spreadsheet 330397769471 with "
                "daily-update@news-update-505306.iam.gserviceaccount.com (Editor)"
            )
        return f"Google Sheets: skipped ({detail[:220]}{hint})"
    try:
        existing = [r for r in worksheet.get_all_values() if any(r)]
    except Exception:  # noqa: BLE001 - treat read failure as empty sheet
        existing = []
    values = (
        [["Date", "Headline", "Summary", "Source URL"]] if not existing else []
    )
    for row in rows:
        values.append(
            [row["date"], row["headline"], row["summary"], row["url"]]
        )
    worksheet.append_rows(values, value_input_option="USER_ENTERED")
    return f"Google Sheets: logged {len(rows)} rows"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def dedupe_articles(headlines: list[dict]) -> list[dict]:
    seen_links, seen_titles, unique = set(), set(), []
    for item in headlines:
        link = (item.get("link") or "").strip().lower()
        title = (item.get("headline") or "").strip().lower()
        if link and link in seen_links:
            continue
        if title and title in seen_titles:
            continue
        if link:
            seen_links.add(link)
        if title:
            seen_titles.add(title)
        unique.append(item)
    return unique
