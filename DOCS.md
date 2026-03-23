# 📚 AgentHunter — Technical Documentation

Complete technical reference for AgentHunter's data collection, storage, and pipeline.

## 📋 Table of Contents

- [How It Works](#how-it-works)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Scanner Details](#scanner-details)
- [Fingerprinting Engine](#fingerprinting-engine)
- [Health Monitoring](#health-monitoring)
- [GitHub Actions Pipeline](#github-actions-pipeline)
- [Usage Examples](#usage-examples)

## 🔄 How It Works

AgentHunter operates on a continuous discovery cycle triggered every 6 hours by GitHub Actions:

```
agents_data.json (GitHub repo)
        │
        ▼ restore_snapshot.py
  SQLite DB (ephemeral)
        │
        ▼ scanners → fingerprinter → POST /agents
  SQLite DB (grown)
        │
        ▼ export_snapshot.py
  agents_data.json + stats_data.json
        │
        ├──▶ git commit + push (GitHub repo)
        │
        └──▶ huggingface_hub upload (HF Space src/)
                    │
                    ▼
          Live Dashboard (Streamlit on HF Spaces)
```

## 🕷️ Data Collection Process

### Phase 1: Restore
`restore_snapshot.py` loads `agents_data.json` from the repo into a fresh SQLite DB before each run. This is what makes the database accumulate across runs — the DB is ephemeral (not committed), the JSON is permanent.

### Phase 2: Discovery
Each scanner runs independently and returns a list of raw dicts:

**GitHub Scanner** (main source — ~95% of all agents)
- 39 topics × 3 pages × 30 repos = up to 3,510 repos per run
- Pre-loads all existing URLs from API to skip known agents
- Stops pagination early if entire page is already known
- Fetches first 500 chars of README per repo
- SIGALRM timeouts: 120s per page, 5s per README

**HuggingFace Scanner**
- 4 tags: `agent`, `tool-calling`, `assistant`, `function-calling`
- 10 models per tag = 40 max per run
- Pre-loads existing URLs to skip known models

**Package Scanner**
- 12 PyPI + 5 npm fixed packages
- Same 17 packages every run — upserted as no-ops if already in DB

### Phase 3: Fingerprinting
Raw scanner dict → fingerprinted agent dict → POST to API

### Phase 4: Export
`export_snapshot.py` reads directly from SQLite (never from API) and writes:
- `agents_data.json` — full array of all agents
- `stats_data.json` — counts by model, framework, agent_type

### Phase 5: Publish
- JSON files committed to GitHub main branch
- JSON files uploaded to HuggingFace Space `src/` directory via `huggingface_hub`

## 🗄️ Database Schema

### AgentProfile Table

```sql
CREATE TABLE agentprofile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL UNIQUE,
    source_platform VARCHAR NOT NULL,
    model_detected VARCHAR DEFAULT 'unknown',
    framework VARCHAR DEFAULT 'unknown',
    capabilities JSON DEFAULT '[]',
    agent_type VARCHAR DEFAULT 'unknown',
    risk_level VARCHAR DEFAULT 'safe',
    stars INTEGER DEFAULT 0,
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    raw_description TEXT DEFAULT '',
    status VARCHAR DEFAULT 'unchecked',
    last_checked DATETIME,
    response_time_ms INTEGER
);

CREATE INDEX ix_agentprofile_source_url ON agentprofile (source_url);
```

### Field Definitions

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `id` | INTEGER | Auto-incrementing primary key | 1, 2, 3... |
| `name` | VARCHAR | Agent/repository name | `microsoft/autogen` |
| `source_url` | VARCHAR | Unique URL — dedup key | `https://github.com/microsoft/autogen` |
| `source_platform` | VARCHAR | Where discovered | `github`, `huggingface` |
| `model_detected` | VARCHAR | AI model identified | `gpt-4`, `claude`, `llama`, `unknown` |
| `framework` | VARCHAR | Framework detected | `langchain`, `crewai`, `autogen` |
| `capabilities` | JSON | Array of capabilities | `["web-search", "code-execution"]` |
| `agent_type` | VARCHAR | Type classification | `multi-agent`, `task-agent`, `crawler` |
| `risk_level` | VARCHAR | Safety assessment | `safe` |
| `stars` | INTEGER | GitHub stars or HF likes | 15420 |
| `first_seen` | DATETIME | When first discovered | `2026-03-10T12:00:00` |
| `last_seen` | DATETIME | Last upsert timestamp | `2026-03-11T06:00:00` |
| `raw_description` | TEXT | Original description text | `Multi-agent conversation framework` |
| `status` | VARCHAR | Health check status | `online`, `dead`, `unknown`, `unchecked` |
| `last_checked` | DATETIME | Last health check time | `2026-03-11T08:30:00` |
| `response_time_ms` | INTEGER | Response time in ms | 234 |

### Deduplication

Three layers:
1. **In-run**: GitHub and HF scanners pre-load existing URLs from API and skip them
2. **DB constraint**: `source_url` has `UNIQUE` — insert fails on duplicate
3. **API upsert**: `POST /agents` checks by `source_url`, updates if exists — no crash

## 🔌 API Reference

Base URL: `http://localhost:8000`

### GET /health
```json
{"status": "healthy"}
```

### GET /agents
Query params: `model`, `framework`, `limit` (default 100, max 10000)

```bash
curl "http://localhost:8000/agents?model=gpt-4&limit=10"
```

### GET /agents/{id}
Single agent by ID. Returns 404 if not found.

### GET /agents/online
All agents with `status = "online"`.

### GET /agents/dead
All agents with `status = "dead"`.

### GET /stats
```json
{
  "models": {"gpt-4": 145, "claude": 89, "unknown": 2800},
  "frameworks": {"langchain": 456, "crewai": 123, "unknown": 2400},
  "agent_types": {"multi-agent": 234, "task-agent": 890, "crawler": 45}
}
```

### POST /agents
Upsert by `source_url`. Creates new or updates existing.

### PATCH /agents/{id}
Update specific fields (used by health checker).

## 🔍 Scanner Details

### GitHub Scanner

```python
TOPICS = [
    "ai-agent", "llm-agent", "autonomous-agent", "multi-agent", "agent-framework",
    "agentic-ai", "openai-agent", "langchain", "crewai", "autogpt", "pydantic-ai",
    "smolagents", "dspy", "semantic-kernel", "llamaindex", "langraph",
    "microsoft-autogen", "mcp-server", "function-calling", "voice-agent",
    "rag-chatbot", "ai-workflow", "tool-calling", "llm-tools", "openai-api",
    "anthropic", "gemini-api", "ollama", "llm-app", "composio", "n8n",
    "llm-chatbot", "ai-assistant", "chatgpt", "gpt-wrapper", "rag",
    "llm-inference", "ai-automation", "prompt-engineering"
]
PAGES_PER_TOPIC = 3  # 3 × 30 = 90 repos max per topic
```

Rate limiting: waits 60s on `RateLimitExceededException`. 1s sleep between pages.

### HuggingFace Scanner

```python
TAGS = ["agent", "tool-calling", "assistant", "function-calling"]
# 10 models per tag, sorted by likes
```

### Package Scanner

```python
PYPI_PACKAGES = [
    "langchain", "crewai", "autogen", "llama-index", "haystack",
    "semantic-kernel", "agentops", "phidata", "dspy", "openai-agents",
    "pydantic-ai", "smolagents"
]
NPM_PACKAGES = ["langchain", "openai-agents", "ai-sdk", "llamaindex", "autogen"]
```

## 🧠 Fingerprinting Engine

Text sources: `description + readme_snippet + topics` (all lowercased)

**Model detection** — first match wins:
```python
MODELS = ["gpt-4", "gpt-3.5", "claude", "gemini", "llama", "mistral", "mixtral", "qwen"]
```

**Framework detection** — first match wins:
```python
FRAMEWORKS = ["langchain", "crewai", "autogen", "llamaindex", "haystack", "semantic-kernel"]
```

**Capability detection** — all matches:
```python
CAPABILITIES = ["web-search", "email", "code-execution", "browser", "file-system", "database", "api-calls"]
```

**Agent type:**
- `multi-agent` if crewai or autogen in text
- `crawler` if playwright or selenium in text
- `task-agent` otherwise

**Platform detection** from URL:
- `github.com` → `github`
- `huggingface.co` → `huggingface`
- else → `unknown`

## 🏥 Health Monitoring

`scanners/health_checker.py` — run manually or integrate into scan:

```python
# Status logic
200-399 → "online"
404, 410 → "dead"
301, 302 → "redirected"
timeout/error → "unknown"
```

All agents checked concurrently via `asyncio.gather`. 10s timeout per URL. Updates `status`, `response_time_ms`, `last_checked` via `PATCH /agents/{id}`.

## ⚙️ GitHub Actions Pipeline

File: `.github/workflows/crawl.yml`

Schedule: every 6 hours (`0 */6 * * *`) + manual trigger

```
Step 1  checkout (fetch-depth: 0)
Step 2  setup Python 3.11
Step 3  pip install -r requirements.txt
Step 4  python restore_snapshot.py          [continue-on-error]
Step 5  uvicorn start + health poll (30 × 2s)
Step 6  python run_scan.py                  [continue-on-error]
          └─ env: GITHUB_TOKEN, TELEGRAM_BOT_TOKEN,
                  TELEGRAM_CHAT_ID, GITHUB_RUN_ID, GITHUB_SHA
Step 7  python3 export_snapshot.py          [continue-on-error]
Step 8  git fetch + checkout origin/main    [continue-on-error]
          + python3 export_snapshot.py (re-export on fresh tree)
          + git add agents_data.json stats_data.json
          + git commit + git push
Step 9  pip install huggingface_hub         [continue-on-error]
          + upload agents_data.json → src/agents_data.json
          + upload stats_data.json  → src/stats_data.json
          └─ repo: dipanshudixit/agent-hunter (space)
```

Required secrets: `HF_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## 💡 Usage Examples

### Python — query the API
```python
import requests

stats = requests.get("http://localhost:8000/stats").json()
print(f"Models detected: {len(stats['models'])}")

agents = requests.get("http://localhost:8000/agents?limit=1000").json()
popular = [a for a in agents if a['stars'] > 1000]
print(f"Popular agents: {len(popular)}")
```

### SQLite — direct queries
```sql
-- Top 10 most starred agents
SELECT name, stars, framework FROM agentprofile
ORDER BY stars DESC LIMIT 10;

-- Count by platform
SELECT source_platform, COUNT(*) FROM agentprofile
GROUP BY source_platform;

-- Recently discovered
SELECT name, first_seen FROM agentprofile
WHERE first_seen > datetime('now', '-7 days');
```

### Trigger a manual scan
```bash
# Via GitHub Actions UI
# Go to: https://github.com/dipanshu-dixit/Agent-Hunter/actions
# Click "Agent Crawl" → "Run workflow"

# Or locally
python -u run_scan.py
```

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes (Actions) | GitHub API access + git push |
| `HF_TOKEN` | Yes (Actions) | HuggingFace Space write access |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram notifications |
| `TELEGRAM_CHAT_ID` | Optional | Telegram target chat |
| `DATABASE_URL` | Optional | SQLite URL (default: `sqlite:///agent_hunter.db`) |
| `DATABASE_PATH` | Optional | SQLite file path (default: `agent_hunter.db`) |
| `GITHUB_RUN_ID` | Auto (Actions) | Used in Telegram run link |
| `GITHUB_SHA` | Auto (Actions) | Used in Telegram commit link |

---

**For setup instructions, see [GUIDE.md](GUIDE.md). For the live dashboard, visit https://huggingface.co/spaces/dipanshudixit/agent-hunter**
