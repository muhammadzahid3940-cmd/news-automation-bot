# NEWS Automation Bot

Fetches the latest trending news, summarizes it with an LLM, and distributes it to Slack and Google Sheets - on demand, on a schedule, and from the web.

## Pipeline (4 tools)

| # | Tool                          | What it does                                                        |
|---|-------------------------------|---------------------------------------------------------------------|
| 1 | `fetch_latest_news`           | Searches Google News (Serper) for trending headlines + source links |
| 2 | `summarize_articles`          | LLM (Gemini) writes a structured digest, dedupes, highlights key points |
| 3 | `post_to_slack`               | Posts the digest to a Slack channel via webhook                     |
| 4 | `log_to_google_sheets`        | Appends Date / Headline / Summary / Source URL rows to a Google Sheet |

Slack and Google Sheets are optional - the bot runs fine with just an LLM + Serper key.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your keys
```

Required keys:

- `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) - LLM for summarizing (https://aistudio.google.com)
- `SERPER_API_KEY` - Google News search (https://serper.dev)

Optional keys:

- `SLACK_WEBHOOK_URL` - Slack distribution
- `GOOGLE_SERVICE_ACCOUNT_JSON` or `GOOGLE_SERVICE_ACCOUNT_FILE` + `GOOGLE_SHEET_ID` - Google Sheets logging
- `SCHEDULE_TOPIC` - topic used by scheduled runs (default: `sports and game cricket`)

## Run

```bash
python main.py "sports and game cricket"    # CLI
python web.py                               # web UI at http://localhost:8000
```

## Automation (every 6 hours)

**GitHub Actions** (cloud): the workflow at `.github/workflows/news-pipeline.yml`
runs `main.py` every 6 hours (cron `0 */6 * * *`) and commits the refreshed
digest back into the repo. Can also be triggered manually from the Actions tab.

Setup:

1. Push this repo to GitHub.
2. Add repository secrets (Settings -> Secrets and variables -> Actions):
   - `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) - LLM for summarizing (https://aistudio.google.com)
   - `SERPER_API_KEY` - Google News search (https://serper.dev)
   - `SLACK_WEBHOOK_URL` - Slack distribution (optional)
   - `GOOGLE_SERVICE_ACCOUNT_JSON` - sheets service-account JSON (optional)
   - `GOOGLE_SHEET_ID` - sheet to log into (optional)
   - `SCHEDULE_TOPIC` - topic for scheduled runs (optional, default: `sports and game cricket`)

**Vercel cron** (cloud, alternative): the project includes `vercel.json` with a
cron that hits `/api/run` every 6 hours. Cron jobs + long function duration
(300s) require a paid Vercel plan.

## Deploy to Vercel

```bash
npm i -g vercel
vercel login
vercel --prod
```

Endpoints after deploy:

- `/api/run` - runs the pipeline (cron target, optional `?topic=`)
- `/api/digest` - returns the latest digest as JSON

## API (local)

- `GET /api/digest` - latest digest JSON
- `POST /api/run` - `{"topic": "cricket"}` - start a run
- `GET /api/status` - running state / last error
