# 📖 AgentHunter — Complete Setup Guide

Everything you need to run AgentHunter locally or via GitHub Actions.

## 🧰 Prerequisites

- GitHub account (free)
- GitHub Codespaces enabled (free tier = 60 hrs/month)
- HuggingFace account (free) — for dashboard updates
- Telegram bot (optional) — for scan notifications

## 🚀 First Time Setup

### Step 1 — Open in Codespaces
1. Go to https://github.com/dipanshu-dixit/Agent-Hunter
2. Click the green **Code** button → **Codespaces** tab → **Create codespace on main**
3. Wait ~2 minutes for the environment to load.

### Step 2 — Open a Terminal
In VS Code: press `Ctrl + `` (backtick) to open terminal.

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Start Everything
```bash
./start.sh
```
This single command:
- Kills any old processes
- Restores the database from `agents_data.json`
- Starts the API server (port 8000)
- Runs the first scan

### Step 5 — View the Dashboard
The live dashboard is on HuggingFace Spaces — no local port needed:
👉 https://huggingface.co/spaces/dipanshudixit/agent-hunter

For the raw API:
- Go to the **PORTS** tab in VS Code → click 🌐 next to port **8000**
- Append `/docs` to the URL for interactive API docs

## 🔑 Setting Up GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | How to Get It |
|-------------|---------------|
| `HF_TOKEN` | https://huggingface.co/settings/tokens → New token → Fine-grained → Write on `dipanshudixit/agent-hunter` Space |
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token |
| `TELEGRAM_CHAT_ID` | Message [@userinfobot](https://t.me/userinfobot) → copy your chat ID |

`GITHUB_TOKEN` is auto-provided by GitHub Actions — no setup needed.

## 📋 Daily Usage

Every time you open the Codespace, just run:
```bash
./start.sh
```

## 🔧 Individual Commands

### Start the API only
```bash
uvicorn api.main:app --port 8000 &
```

### Restore DB from snapshot
```bash
python restore_snapshot.py
```

### Run a scan manually
```bash
python -u run_scan.py
```

### Export DB to JSON
```bash
python export_snapshot.py
```

### Check health of all agents
```bash
python scanners/health_checker.py
```

### Stop everything
```bash
pkill -f uvicorn
```

## 🌐 What's Running Where

| Service | Port | What It Does |
|---------|------|--------------|
| FastAPI | 8000 | Stores and serves all agent data |
| HuggingFace Space | — | Live dashboard, auto-updated after every Actions run |

## 🔗 URLs

| URL | What You See |
|-----|--------------|
| `localhost:8000/docs` | 📖 API documentation (interactive) |
| `localhost:8000/agents` | 🤖 Raw JSON list of all agents |
| `localhost:8000/stats` | 📈 Stats breakdown |
| https://huggingface.co/spaces/dipanshudixit/agent-hunter | 📊 Live dashboard |
| https://github.com/dipanshu-dixit/Agent-Hunter | 🐙 GitHub repo + JSON snapshots |

## 🔌 Using the API

### Get all agents
```bash
curl http://localhost:8000/agents
```

### Filter by model
```bash
curl "http://localhost:8000/agents?model=gpt-4&limit=10"
```

### Get stats
```bash
curl http://localhost:8000/stats | python -m json.tool
```

### Get only online agents
```bash
curl http://localhost:8000/agents/online
```

## ⚙️ Auto-Scanning (GitHub Actions)

The repo auto-scans every 6 hours via GitHub Actions — no action needed from you.

To trigger a scan manually:
1. Go to https://github.com/dipanshu-dixit/Agent-Hunter/actions
2. Click **Agent Crawl** workflow
3. Click **Run workflow** → **Run workflow**

Watch it run live in the logs.

## 🔑 GitHub Token (Increases Scan Speed)

- **Without a token**: GitHub API allows 60 requests/hour
- **With a token**: 5,000 requests/hour — much faster scans

The `GITHUB_TOKEN` secret is auto-provided in Actions. For local runs:
```bash
export GITHUB_TOKEN=your_token_here
```

> ⚠️ **NEVER** paste your token into any code file or commit it

## 🐛 Common Errors & Fixes

### "Address already in use" on port 8000
```bash
pkill -f uvicorn
./start.sh
```

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Dashboard shows old data
The HuggingFace Space updates automatically after every Actions run. If you need it now, trigger a manual run from the Actions tab.

### GitHub Actions shows "failed"
Check the Actions log. All data steps have `continue-on-error: true` — if agents were saved before the failure, data is safe in `agents_data.json`.

### HF upload fails
Check that `HF_TOKEN` secret is set correctly in GitHub repo secrets with write access to the `dipanshudixit/agent-hunter` Space.

## 📂 Key Files Reference

| File | What To Edit |
|------|--------------|
| `scanners/github_scanner.py` | Add more GitHub topics to search |
| `scanners/hf_scanner.py` | Add more HuggingFace tags |
| `fingerprint/fingerprinter.py` | Add new model/framework keywords |
| `api/main.py` | Add new API endpoints |
| `.github/workflows/crawl.yml` | Change scan schedule |
| `start.sh` | Change startup behavior |

## 💡 Tips

- **Save Codespace hours** — stop your Codespace when not coding. GitHub Actions handles scanning automatically even when Codespace is off.
- **Set spending limit to $0** — go to github.com/settings/billing → Codespaces → set limit to $0.
- **Data is always safe** — `agents_data.json` is committed to GitHub after every run. Even if Codespace is deleted, all data is in the repo.

---

**Built with GitHub Codespaces + Amazon Q • Zero cost • Growing database**
