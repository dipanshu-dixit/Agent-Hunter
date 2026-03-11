"""
Telegram notification system for AgentHunter
Sends scan summary after every run
"""

import os
import httpx
import json
from datetime import datetime


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_REPO = "hatemonkey69/Agent-Hunter"
DB_URL = f"https://github.com/{GITHUB_REPO}/blob/main/agent_hunter.db"
ACTIONS_URL = f"https://github.com/{GITHUB_REPO}/actions"


def send_telegram_message(text: str) -> bool:
    """Send a message via Telegram Bot API"""
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
        else:
            print(f"❌ Telegram failed: {response.status_code} — {response.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False


def build_scan_summary(
    total_agents: int,
    new_agents: int,
    updated_agents: int,
    by_platform: dict,
    by_model: dict,
    by_framework: dict,
    duration_seconds: int,
    errors: int = 0,
) -> str:
    """Build a rich Telegram message with scan results"""

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"

    # Status emoji based on new finds
    if new_agents > 100:
        status = "🔥 Big haul!"
    elif new_agents > 20:
        status = "✅ Good run!"
    elif new_agents > 0:
        status = "📦 Small batch"
    else:
        status = "😴 No new agents"

    # Platform breakdown
    platform_lines = ""
    for platform, count in sorted(by_platform.items(), key=lambda x: -x[1]):
        emoji = {
            "github": "🐙",
            "huggingface": "🤗",
            "discord": "💬",
            "honeypot": "🍯",
            "packages": "📦",
        }.get(platform.lower(), "🔹")
        platform_lines += f"  {emoji} {platform.capitalize()}: <b>{count}</b>\n"

    # Top models
    top_models = sorted(by_model.items(), key=lambda x: -x[1])[:5]
    model_lines = ""
    for model, count in top_models:
        if model and model != "unknown":
            model_lines += f"  • {model}: {count}\n"
    if not model_lines:
        model_lines = "  • Not yet classified\n"

    # Top frameworks
    top_frameworks = sorted(by_framework.items(), key=lambda x: -x[1])[:5]
    framework_lines = ""
    for fw, count in top_frameworks:
        if fw and fw != "unknown":
            framework_lines += f"  • {fw}: {count}\n"
    if not framework_lines:
        framework_lines = "  • Not yet classified\n"

    # Error note
    error_line = ""
    if errors > 0:
        error_line = f"\n⚠️ <b>{errors}</b> agents failed to process\n"

    message = f"""🤖 <b>AgentHunter Scan Complete</b>
{status}

🕐 <b>{now}</b>
⏱ Duration: {duration_str}

━━━━━━━━━━━━━━━━━━━━
📊 <b>SCAN RESULTS</b>
━━━━━━━━━━━━━━━━━━━━

🆕 New agents found: <b>{new_agents}</b>
🔄 Updated agents: <b>{updated_agents}</b>
💾 Total in database: <b>{total_agents}</b>
{error_line}
━━━━━━━━━━━━━━━━━━━━
📡 <b>SOURCES</b>
━━━━━━━━━━━━━━━━━━━━
{platform_lines.rstrip()}

━━━━━━━━━━━━━━━━━━━━
🧠 <b>TOP MODELS DETECTED</b>
━━━━━━━━━━━━━━━━━━━━
{model_lines.rstrip()}

━━━━━━━━━━━━━━━━━━━━
⚙️ <b>TOP FRAMEWORKS</b>
━━━━━━━━━━━━━━━━━━━━
{framework_lines.rstrip()}

━━━━━━━━━━━━━━━━━━━━
🔗 <b>LINKS</b>
━━━━━━━━━━━━━━━━━━━━
📂 <a href="{ACTIONS_URL}">View Full Run Logs</a>
🗄️ <a href="https://github.com/{GITHUB_REPO}">GitHub Repo + Database</a>"""

    return message


def notify_scan_complete(
    total_before: int,
    total_after: int,
    by_platform: dict,
    by_model: dict,
    by_framework: dict,
    duration_seconds: int,
    errors: int = 0,
):
    """Main function — call this at end of run_scan.py"""
    new_agents = total_after - total_before
    updated_agents = max(0, total_after - new_agents)  # simplified

    message = build_scan_summary(
        total_agents=total_after,
        new_agents=new_agents,
        updated_agents=updated_agents,
        by_platform=by_platform,
        by_model=by_model,
        by_framework=by_framework,
        duration_seconds=duration_seconds,
        errors=errors,
    )

    return send_telegram_message(message)


def notify_scan_started(total_existing: int):
    """Optional — send message when scan kicks off"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    message = f"""🚀 <b>AgentHunter Scan Started</b>

🕐 {now}
💾 Database currently: <b>{total_existing}</b> agents

Scanning GitHub, HuggingFace, Discord, Honeypots, Packages...
Will notify when complete ✅"""
    return send_telegram_message(message)


def notify_error(error_msg: str):
    """Send alert if something goes badly wrong"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    message = f"""🚨 <b>AgentHunter — Scan Error</b>

🕐 {now}
❌ <code>{error_msg[:500]}</code>

<a href="{ACTIONS_URL}">Check GitHub Actions logs</a>"""
    return send_telegram_message(message)


if __name__ == "__main__":
    # Test the notifier
    print("Testing Telegram notification...")
    notify_scan_complete(
        total_before=3892,
        total_after=3950,
        by_platform={"github": 45, "huggingface": 11, "discord": 2, "packages": 0},
        by_model={"gpt-4": 450, "claude": 120, "llama": 380, "gemini": 89, "unknown": 2911},
        by_framework={"langchain": 890, "crewai": 210, "autogen": 180, "unknown": 2670},
        duration_seconds=4230,
        errors=3,
    )