"""
Telegram notification system for AgentHunter
Sends scan summary after every run
"""

import os
import httpx
from datetime import datetime, timezone


def _utcnow_str():
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M UTC")


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_REPO = "dipanshu-dixit/Agent-Hunter"
GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID", "")
GITHUB_SHA = os.environ.get("GITHUB_SHA", "")
ACTIONS_URL = f"https://github.com/{GITHUB_REPO}/actions"
COMMIT_URL = f"https://github.com/{GITHUB_REPO}/commit/{GITHUB_SHA}" if GITHUB_SHA else f"https://github.com/{GITHUB_REPO}/commits/main"
RUN_URL = f"https://github.com/{GITHUB_REPO}/actions/runs/{GITHUB_RUN_ID}" if GITHUB_RUN_ID else ACTIONS_URL
DATA_URL = f"https://github.com/{GITHUB_REPO}/blob/main/agents_data.json"
HF_SPACE_URL = "https://huggingface.co/spaces/dipanshudixit/agent-hunter"


def send_telegram_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not set — skipping notification")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        response = httpx.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("✅ Telegram notification sent!")
            return True
        print(f"❌ Telegram failed: {response.status_code} — {response.text}")
        return False
    except httpx.HTTPError as e:
        print(f"❌ Telegram error: {e}")
        return False


def build_scan_summary(
    total_agents: int,
    new_agents: int,
    by_platform: dict,
    by_model: dict,
    by_framework: dict,
    duration_seconds: int,
    errors: int = 0,
) -> str:
    now = _utcnow_str()
    duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"

    if new_agents > 100:
        status = "🔥 Big haul!"
    elif new_agents > 20:
        status = "✅ Good run!"
    elif new_agents > 0:
        status = "📦 Small batch"
    else:
        status = "😴 No new agents"

    emoji_map = {"github": "🐙", "huggingface": "🤗", "packages": "📦"}
    platform_lines = "\n".join(
        f"  {emoji_map.get(p.lower(), '🔹')} {p.capitalize()}: <b>{c}</b>"
        for p, c in sorted(by_platform.items(), key=lambda x: -x[1])
    )

    model_lines = "\n".join(
        f"  • {m}: {c}" for m, c in sorted(by_model.items(), key=lambda x: -x[1])[:5]
        if m and m != "unknown"
    ) or "  • Not yet classified"

    framework_lines = "\n".join(
        f"  • {fw}: {c}" for fw, c in sorted(by_framework.items(), key=lambda x: -x[1])[:5]
        if fw and fw != "unknown"
    ) or "  • Not yet classified"

    error_line = f"\n⚠️ <b>{errors}</b> saves failed\n" if errors > 0 else ""
    sha_short = GITHUB_SHA[:7] if GITHUB_SHA else "unknown"

    return f"""🤖 <b>AgentHunter Scan Complete</b>
{status}

🕐 <b>{now}</b>
⏱ Duration: {duration_str}

━━━━━━━━━━━━━━━━━━━━
📊 <b>SCAN RESULTS</b>
━━━━━━━━━━━━━━━━━━━━
🆕 New agents found: <b>{new_agents}</b>
💾 Total in database: <b>{total_agents}</b>
{error_line}
━━━━━━━━━━━━━━━━━━━━
📡 <b>BY PLATFORM</b>
━━━━━━━━━━━━━━━━━━━━
{platform_lines}

━━━━━━━━━━━━━━━━━━━━
🧠 <b>TOP MODELS</b>
━━━━━━━━━━━━━━━━━━━━
{model_lines}

━━━━━━━━━━━━━━━━━━━━
⚙️ <b>TOP FRAMEWORKS</b>
━━━━━━━━━━━━━━━━━━━━
{framework_lines}

━━━━━━━━━━━━━━━━━━━━
🔗 <b>LINKS</b>
━━━━━━━━━━━━━━━━━━━━
▶️ <a href="{RUN_URL}">This Run's Logs</a>
📝 <a href="{COMMIT_URL}">Commit {sha_short}</a>
🗄️ <a href="{DATA_URL}">agents_data.json (GitHub)</a>
🤗 <a href="{HF_SPACE_URL}">Live Dashboard (HuggingFace)</a>
🐙 <a href="https://github.com/{GITHUB_REPO}">GitHub Repo</a>"""


def notify_scan_complete(
    total_before: int,
    total_after: int,
    by_platform: dict,
    by_model: dict,
    by_framework: dict,
    duration_seconds: int,
    errors: int = 0,
):
    new_agents = total_after - total_before
    message = build_scan_summary(
        total_agents=total_after,
        new_agents=new_agents,
        by_platform=by_platform,
        by_model=by_model,
        by_framework=by_framework,
        duration_seconds=duration_seconds,
        errors=errors,
    )
    return send_telegram_message(message)


def notify_scan_started(total_existing: int):
    now = _utcnow_str()
    message = f"""🚀 <b>AgentHunter Scan Started</b>

🕐 {now}
💾 Database currently: <b>{total_existing}</b> agents

Scanning GitHub, HuggingFace, Packages...
Will notify when complete ✅"""
    return send_telegram_message(message)


def notify_error(error_msg: str):
    now = _utcnow_str()
    message = f"""🚨 <b>AgentHunter — Scan Error</b>

🕐 {now}
❌ <code>{error_msg[:500]}</code>

<a href="{ACTIONS_URL}">Check GitHub Actions logs</a>"""
    return send_telegram_message(message)


if __name__ == "__main__":
    print("Testing Telegram notification...")
    notify_scan_complete(
        total_before=3892,
        total_after=3950,
        by_platform={"github": 45, "huggingface": 11, "packages": 0},
        by_model={"gpt-4": 450, "claude": 120, "llama": 380, "gemini": 89, "unknown": 2911},
        by_framework={"langchain": 890, "crewai": 210, "autogen": 180, "unknown": 2670},
        duration_seconds=4230,
        errors=3,
    )
