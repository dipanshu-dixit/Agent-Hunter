"""Run this to verify Telegram credentials: python test_telegram.py"""
import httpx, os, sys

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

print(f"TOKEN  : '{TOKEN[:10]}...{TOKEN[-5:]}'" if len(TOKEN) > 15 else f"TOKEN  : '{TOKEN}' ← EMPTY or too short!")
print(f"CHAT_ID: '{CHAT_ID}'")

if not TOKEN:
    print("\n❌ TELEGRAM_BOT_TOKEN is not set. Export it first:\n  export TELEGRAM_BOT_TOKEN=your_token_here")
    sys.exit(1)

r = httpx.get(f"https://api.telegram.org/bot{TOKEN}/getMe")
print(f"\ngetMe → {r.status_code}: {r.text}")

if r.status_code != 200:
    print("\n❌ Token is invalid. Get a new one from @BotFather → /token")
    sys.exit(1)

print("✅ Token is valid!")

if not CHAT_ID:
    print("\n⚠️  TELEGRAM_CHAT_ID not set. Get it from:")
    print(f"  https://api.telegram.org/bot{TOKEN}/getUpdates")
    print("  (send any message to your bot first, then check 'chat.id')")
    sys.exit(1)

r2 = httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": "✅ AgentHunter Telegram test OK!"})
print(f"\nsendMessage → {r2.status_code}: {r2.text}")
if r2.status_code == 200:
    print("✅ Message sent! Check your Telegram.")
else:
    print("❌ sendMessage failed — CHAT_ID is likely wrong.")
