# 🔭 AgentHunter — Live AI Agent Discovery Platform

**The internet's first open-source radar for AI agents.**

Automatically hunts, fingerprints, and catalogs every AI agent, bot, and autonomous system it can find — then stores them in a searchable database and pushes the live dataset to a public HuggingFace dashboard.

**Think: Shodan, but for AI agents.**

## ✨ Features

- 🕷️ **3 Active Scanners** — GitHub (39 topics × 3 pages), HuggingFace models, PyPI/npm packages
- 🧠 **AI Fingerprinting** — Detects model (GPT-4, Claude, Gemini, Llama), framework (LangChain, CrewAI, AutoGen), capabilities, and agent type
- 💾 **Persistent Database** — SQLite rebuilt from `agents_data.json` snapshot on every run
- 🔌 **REST API** — FastAPI with full Swagger docs at `/docs`
- 📊 **Live Dashboard** — Hosted on HuggingFace Spaces, auto-updated after every scan
- ⚡ **Auto-Scans** — GitHub Actions runs every 6 hours automatically, forever
- 💰 **Zero Cost** — Runs 100% free on GitHub Codespaces + GitHub Actions

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/dipanshu-dixit/Agent-Hunter.git
cd Agent-Hunter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start everything
./start.sh
```

Then open:
- **API Docs** → http://localhost:8000/docs
- **Live Dashboard** → https://huggingface.co/spaces/dipanshudixit/agent-hunter

> See [GUIDE.md](GUIDE.md) for full step-by-step instructions.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  3 ACTIVE SCANNERS                   │
│       GitHub    │   HuggingFace   │   PyPI/npm       │
└──────────────────────┬──────────────────────────────┘
                       │ raw agent data
                       ▼
              ┌─────────────────┐
              │  Fingerprinter  │  ← detects model, framework,
              │  (AI Analysis)  │    capabilities, type
              └────────┬────────┘
                       │ AgentProfile
                       ▼
              ┌─────────────────┐
              │  SQLite Database│  ← ephemeral per run
              │  agent_hunter.db│    rebuilt from snapshot
              └────────┬────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
  ┌──────────────┐         ┌──────────────────────┐
  │  FastAPI     │         │  agents_data.json     │
  │  REST API    │         │  (committed to GitHub)│
  │  :8000       │         └──────────┬───────────┘
  └──────────────┘                    │
                                      ▼
                           ┌──────────────────────┐
                           │  HuggingFace Space   │
                           │  Live Dashboard      │
                           │  (auto-pushed)       │
                           └──────────────────────┘
```

## 📁 Project Structure

```
Agent-Hunter/
├── scanners/
│   ├── github_scanner.py      # Scans 39 GitHub topics × 3 pages
│   ├── hf_scanner.py          # Scans HuggingFace Hub models
│   ├── package_scanner.py     # Scans PyPI + npm packages
│   └── health_checker.py      # Pings agents for status
├── fingerprint/
│   └── fingerprinter.py       # AI model/framework detection
├── models/
│   ├── agent_profile.py       # SQLModel database schema
│   └── scan_state.py          # Scan state tracking schema
├── api/
│   └── main.py                # FastAPI REST endpoints
├── notifications/
│   └── telegram_notifier.py   # Telegram scan summary alerts
├── .github/workflows/
│   └── crawl.yml              # Auto-scan every 6 hours
├── run_scan.py                # Main scan runner
├── restore_snapshot.py        # Loads agents_data.json → SQLite
├── export_snapshot.py         # Dumps SQLite → agents_data.json
├── start.sh                   # One-command local startup
├── requirements.txt
├── agents_data.json           # Cumulative agent database (committed)
├── stats_data.json            # Aggregated stats (committed)
├── README.md
├── GUIDE.md
└── DOCS.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/agents` | List all agents (`?model=&framework=&limit=`) |
| GET | `/agents/{id}` | Get single agent by ID |
| GET | `/agents/online` | Only online agents |
| GET | `/agents/dead` | Only dead agents |
| GET | `/stats` | Counts by model, framework, type |
| POST | `/agents` | Add/update an agent (upsert by URL) |
| PATCH | `/agents/{id}` | Update agent fields |

Full interactive docs: http://localhost:8000/docs

## 🗄️ Data Collected Per Agent

| Field | Example |
|-------|---------|
| name | `langchain-ai/langchain` |
| source_platform | `github` |
| model_detected | `gpt-4` |
| framework | `langchain` |
| capabilities | `["web-search", "code-execution"]` |
| agent_type | `multi-agent` |
| risk_level | `safe` |
| stars | `128977` |
| status | `online` |
| response_time_ms | `234` |
| first_seen | `2026-03-10T12:00:00` |
| last_seen | `2026-03-11T06:00:00` |

## ⚙️ How Auto-Scanning Works

GitHub Actions runs `.github/workflows/crawl.yml` every 6 hours:

1. Checks out repo with full history
2. Installs Python 3.11 dependencies
3. Runs `restore_snapshot.py` — loads `agents_data.json` into fresh SQLite DB
4. Starts FastAPI server, polls until healthy
5. Runs all scanners → fingerprints → saves to DB via API
6. Runs `export_snapshot.py` — dumps DB back to `agents_data.json` + `stats_data.json`
7. Commits and pushes both JSON files to GitHub
8. Uploads both JSON files to HuggingFace Space `src/` directory
9. Sends detailed Telegram notification with run link, commit link, and stats

**Result**: Database grows automatically, forever, at zero cost. Dashboard always shows latest data.

## 📈 Database Growth

| Time | Estimated Agents |
|------|------------------|
| Day 1 | ~3,500 |
| Week 1 | ~7,000 |
| Month 1 | ~20,000 |
| Month 6 | ~80,000+ |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11 |
| API Framework | FastAPI + Uvicorn |
| Database | SQLite + SQLModel |
| Dashboard | HuggingFace Spaces (Streamlit) |
| Crawling | httpx + PyGithub |
| GitHub API | PyGithub |
| HF Upload | huggingface_hub |
| Notifications | Telegram Bot API |
| Scheduling | GitHub Actions |
| Dev Environment | GitHub Codespaces |

**Total cost**: $0/month

## 🔑 Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | Auto-provided — used for git push |
| `HF_TOKEN` | HuggingFace write token — uploads dataset to Space |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for scan notifications |
| `TELEGRAM_CHAT_ID` | Your Telegram chat/channel ID |

## 🤝 Contributing

1. Fork the repo
2. Open in GitHub Codespaces
3. Add a new scanner in `scanners/`
4. Submit a PR

Ideas for new scanners:
- Telegram bot directories
- HuggingFace Spaces (not just models)
- Agent marketplaces (e2b.dev, composio.dev)
- Twitter/X bot accounts
- Slack app directory

## 📜 License

This project uses a dual license:

| | Code | Dataset (`agents_data.json`) |
|---|---|---|
| Personal use | ✅ | ✅ |
| Academic research | ✅ | ✅ (with attribution) |
| Commercial use | ✅ | ❌ |
| Redistribution | ✅ | ❌ |
| Sell / sublicense | ✅ | ❌ |

- **Code** → MIT License (free to use, modify, distribute)
- **Dataset** → Proprietary (personal use only)
- 📧 Commercial dataset licensing: securematehelp@gmail.com

See [LICENSE](LICENSE) for full terms.

---

**Built with 💙 by [@dipanshu-dixit](https://github.com/dipanshu-dixit)**
