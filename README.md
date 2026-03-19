# 🔭 AgentHunter — Live AI Agent Discovery Platform

**The internet's first open-source radar for AI agents.**

Automatically hunts, fingerprints, and catalogs every AI agent, bot, and autonomous system it can find — then lets you search, monitor, and health-check them all from a live dashboard.

## 🌟 What Is AgentHunter?

AgentHunter is an automated intelligence platform that continuously scans the public internet for AI agents — GitHub repos, HuggingFace models, Discord bots, known AI crawlers, and AI packages — then classifies and stores them in a searchable database.

**Think: Shodan, but for AI agents.**

## ✨ Features

- 🕷️ **5 Scanners** — GitHub, HuggingFace, Discord bots, known AI crawlers, PyPI/npm packages
- 🧠 **AI Fingerprinting** — Detects model (GPT-4, Claude, Gemini, Llama), framework (LangChain, CrewAI, AutoGen), capabilities, and agent type
- 💾 **Persistent Database** — SQLite locally, auto-committed to GitHub repo after every scan
- 🔌 **REST API** — FastAPI with full Swagger docs at `/docs`
- 📊 **Live Dashboard** — Streamlit UI with charts, filters, health checks
- 🟢 **Health Monitoring** — Ping any agent to check if it's online, dead, or unreachable
- ⚡ **Auto-Scans** — GitHub Actions runs every 6 hours automatically, forever
- 💰 **Zero Cost** — Runs 100% free on GitHub Codespaces + GitHub Actions

## 🚀 Quick Start (3 Commands)

```bash
# 1. Clone the repo
git clone https://github.com/hatemonkey69/Agent-Hunter.git
cd Agent-Hunter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start everything
./start.sh
```

Then open:
- **Dashboard** → http://localhost:8501
- **API Docs** → http://localhost:8000/docs

> See [GUIDE.md](GUIDE.md) for full step-by-step instructions.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    5 SCANNERS                        │
│  GitHub │ HuggingFace │ Discord │ Honeypot │ PyPI   │
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
              │  SQLite Database│  ← persists in GitHub repo
              │  agent_hunter.db│
              └────────┬────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
  ┌──────────────┐         ┌──────────────────┐
  │  FastAPI     │         │  Streamlit       │
  │  REST API    │         │  Dashboard       │
  │  :8000       │         │  :8501           │
  └──────────────┘         └──────────────────┘
```

## 📁 Project Structure

```
Agent-Hunter/
├── scanners/
│   ├── github_scanner.py      # Scans 24 GitHub topics
│   ├── hf_scanner.py          # Scans HuggingFace Hub
│   ├── discord_scanner.py     # Scrapes bot directories
│   ├── honeypot_scanner.py    # Logs known AI crawlers
│   ├── package_scanner.py     # Scans PyPI + npm
│   └── health_checker.py      # Pings agents for status
├── fingerprint/
│   └── fingerprinter.py       # AI model/framework detection
├── models/
│   └── agent_profile.py       # SQLModel database schema
├── api/
│   └── main.py                # FastAPI REST endpoints
├── dashboard/
│   └── app.py                 # Streamlit web UI
├── .github/workflows/
│   └── crawl.yml              # Auto-scan every 6 hours
├── run_scan.py                # Main scan runner
├── start.sh                   # One-command startup
├── requirements.txt
├── README.md                  # You are here
└── GUIDE.md                   # Full setup guide
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/agents` | List all agents (supports `?model=&framework=&limit=`) |
| GET | `/agents/{id}` | Get single agent |
| GET | `/agents/online` | Only online agents |
| GET | `/agents/dead` | Only dead agents |
| GET | `/stats` | Counts by model, framework, type |
| POST | `/agents` | Add/update an agent |
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

1. Spins up a fresh Ubuntu runner (free)
2. Installs Python dependencies
3. Starts the FastAPI server
4. Runs all 5 scanners with live progress output
5. Saves new agents to `agent_hunter.db`
6. Commits the updated database back to this repo
7. Runner shuts down — database is safe in the repo

**Result**: Database grows automatically, forever, at zero cost.

## 📈 Database Growth

| Time | Estimated Agents |
|------|------------------|
| Day 1 | ~3,900 |
| Week 1 | ~7,000 |
| Month 1 | ~20,000 |
| Month 6 | ~80,000+ |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| API Framework | FastAPI + Uvicorn |
| Database | SQLite + SQLModel |
| Dashboard | Streamlit + Plotly |
| Crawling | httpx + BeautifulSoup + crawl4ai |
| Browser | Playwright + Chromium |
| GitHub API | PyGithub |
| Scheduling | GitHub Actions |
| Dev Environment | GitHub Codespaces |

**Total cost**: $0/month

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

**Personal Use License** — This project and its growing database of AI agents is proprietary. 

- ✅ **Allowed**: Personal use, learning, research
- ❌ **Not Allowed**: Commercial use, redistribution, selling data
- 📧 **Contact**: securematehelp@gmail.com for commercial licensing

## ⭐ Star This Repo

If you find this useful, star the repo — it helps others discover it and motivates continued development.

---

**Built with 💙 by [@hatemonkey69](https://github.com/hatemonkey69)**
