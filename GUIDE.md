# 📖 AgentHunter — Complete Setup Guide

Everything you need to run AgentHunter locally in GitHub Codespaces.

## 🧰 Prerequisites

- GitHub account (free)
- GitHub Codespaces enabled (free tier = 60 hrs/month)
- That's it — no installs, no credit card, no cloud accounts needed

## 🚀 First Time Setup

### Step 1 — Open in Codespaces
1. Go to the repo on GitHub → click the green **Code** button → **Codespaces** tab → **Create codespace on main**
2. Wait ~2 minutes for the environment to load.

### Step 2 — Open a Terminal
In VS Code: press `Ctrl + `` (backtick) to open terminal.

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```
Wait for it to finish (~2 minutes first time).

### Step 4 — Start Everything
```bash
./start.sh
```
This single command:
- Kills any old processes
- Starts the API server (port 8000)
- Runs the first scan (finds ~1,000+ agents)
- Opens the dashboard (port 8501)

### Step 5 — Open the Dashboard
Go to the **PORTS** tab in VS Code (next to Terminal) → click the 🌐 globe icon next to port **8501**.

Your dashboard opens in the browser. **Done!** ✅

## 📋 Daily Usage

Every time you open the Codespace, just run:
```bash
./start.sh
```
That's it. One command starts everything.

## 🔧 Individual Commands

If you need to run things separately:

### Start the API only
```bash
uvicorn api.main:app --port 8000 &
```

### Start the Dashboard only
```bash
streamlit run dashboard/app.py
```

### Run a scan manually
```bash
python -u run_scan.py
```

### Check health of all agents
```bash
python scanners/health_checker.py
```

### Stop everything
```bash
pkill -f uvicorn && pkill -f streamlit
```

## 🌐 What's Running Where

| Service | Port | What It Does |
|---------|------|--------------|
| FastAPI | 8000 | Stores and serves all agent data |
| Streamlit | 8501 | The visual dashboard you interact with |

Only these two things run. Nothing else.

## 🔗 URLs To Bookmark

Once `./start.sh` is running, open these in your browser (via PORTS tab):

| URL | What You See |
|-----|--------------|
| `localhost:8501` | 📊 Main dashboard |
| `localhost:8000/docs` | 📖 API documentation (interactive) |
| `localhost:8000/agents` | 🤖 Raw JSON list of all agents |
| `localhost:8000/stats` | 📈 Stats breakdown |

## 📊 Dashboard Features

### Metrics Row
- **Total Agents** — how many discovered so far
- **Unique Models** — how many different AI models detected
- **Unique Frameworks** — how many frameworks found
- **🟢 Online / 🔴 Dead / ⚪ Unchecked** — health status counts

### Charts
- **Pie chart** — agents by AI model
- **Bar chart** — agents by framework

### Health Check Button
Click "🔍 Check Agent Health" to ping all agents live.
Results update in real time with 🟢 🔴 🟡 badges.

### Filters (Sidebar)
- Filter by model (GPT-4, Claude, Llama, etc.)
- Filter by framework (LangChain, CrewAI, etc.)
- Filter by status (Online / Dead / Unknown)

### Agents Table

| Column | Description |
|--------|-------------|
| Name | Agent/repo name |
| Model | Detected AI model |
| Framework | Detected framework |
| Type | chatbot / task-agent / crawler / multi-agent |
| Stars | GitHub stars or HF likes |
| Platform | Where it was found |
| Status | 🟢 🔴 🟡 ⚪ |
| Response Time | ms if online |
| URL | Link to original source |

## 🔌 Using the API

The API has interactive docs at `localhost:8000/docs` — you can test every endpoint right there.

### Get all agents
```bash
curl http://localhost:8000/agents
```

### Get agents filtered by model
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
1. Go to your GitHub repo
2. Click **Actions** tab
3. Click **Agent Crawl** workflow
4. Click **Run workflow** → **Run workflow**

Watch it run live in the logs.

## 🔑 GitHub Token (Optional — Increases Speed)

- **Without a token**, GitHub API allows 60 requests/hour.
- **With a token**, it allows 5,000 requests/hour — much faster scans.

To add a token:
1. Go to github.com/settings/tokens → **Generate new token (classic)**
2. Select scope: **public_repo** only
3. Copy the token
4. In Codespaces terminal:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

Or add it to Codespaces secrets:
github.com/settings/codespaces → **New secret** → Name: `GITHUB_TOKEN`

> ⚠️ **NEVER** paste your token into any code file or chat message

## 🐛 Common Errors & Fixes

### "Address already in use" on port 8000 or 8501
```bash
pkill -f uvicorn && pkill -f streamlit
./start.sh
```

### "ModuleNotFoundError: No module named X"
```bash
pip install -r requirements.txt
```

### Dashboard shows "Connection refused"
The API isn't running. Start it first:
```bash
uvicorn api.main:app --port 8000 &
sleep 3
streamlit run dashboard/app.py
```

### Stats show empty `{}`
The fingerprinter hasn't classified agents yet. Run a fresh scan:
```bash
python -u run_scan.py
```

### GitHub Actions shows "failed"
Check the Actions log — if agents were saved before the failure, data is safe.
The `continue-on-error: true` setting means one crash doesn't lose everything.

## 📂 Key Files Reference

| File | What To Edit |
|------|--------------|
| `scanners/github_scanner.py` | Add more GitHub topics to search |
| `scanners/hf_scanner.py` | Add more HuggingFace tags |
| `fingerprint/fingerprinter.py` | Add new model/framework keywords |
| `dashboard/app.py` | Customize the dashboard UI |
| `api/main.py` | Add new API endpoints |
| `.github/workflows/crawl.yml` | Change scan schedule |
| `start.sh` | Change startup behavior |

## 💡 Tips

- **Save Codespace hours** — stop your Codespace when not coding. GitHub Actions handles scanning automatically even when Codespace is off.
- **Set spending limit to $0** — go to github.com/settings/billing → Codespaces → set limit to $0 so you're never charged.
- **The database grows in GitHub** — `agent_hunter.db` gets committed after every Actions run. Your data is always safe even if Codespace is deleted.

## 🗺️ What's Next

Ideas to extend AgentHunter:
- Add Telegram bot directory scanner
- Add HuggingFace Spaces scanner (demos, not just models)
- Add agent comparison/benchmarking
- Deploy dashboard to Hugging Face Spaces (public URL, free)
- Add email digest of new agents found each week

---

**Built with GitHub Codespaces + Amazon Q + Claude • Zero cost • Growing database**