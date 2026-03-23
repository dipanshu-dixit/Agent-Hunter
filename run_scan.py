"""AgentHunter — Main scan runner
Runs all scanners, fingerprints, saves to DB, sends Telegram summary
"""

import httpx
import sqlite3
import os
import time
from datetime import datetime, timezone
from scanners.github_scanner import GitHubScanner
from scanners.hf_scanner import HuggingFaceScanner
from scanners.package_scanner import PackageScanner
from fingerprint.fingerprinter import Fingerprinter
from notifications.telegram_notifier import notify_scan_started, notify_scan_complete, notify_error

API_URL = "http://localhost:8000/agents"
API_BASE = "http://localhost:8000"
DB_PATH = os.getenv("DATABASE_PATH", "agent_hunter.db")


def get_total_agents_from_db() -> int:
    """Read agent count directly from SQLite — always accurate, never depends on API health."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("SELECT COUNT(*) FROM agentprofile").fetchone()
            return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


def get_stats() -> dict:
    """Get model/framework breakdown from API"""
    try:
        response = httpx.get(f"{API_BASE}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except httpx.HTTPError:
        pass
    return {"models": {}, "frameworks": {}}

def main():
    start_time = time.time()
    print(f"\n{'='*60}")
    print(f"🚀 Starting AgentHunter scan — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    total_before = get_total_agents_from_db()
    print(f"💾 Agents in database before scan: {total_before}")
    
    # Send start notification
    notify_scan_started(total_before)
    
    github_scanner  = GitHubScanner()
    hf_scanner      = HuggingFaceScanner()
    package_scanner = PackageScanner()
    fingerprinter   = Fingerprinter()

    platform_counts = {"github": 0, "huggingface": 0, "packages": 0}

    print("📡 Running GitHub scanner...")
    github_results = github_scanner.scan()
    platform_counts["github"] = len(github_results)

    print("🤗 Running HuggingFace scanner...")
    hf_results = hf_scanner.scan()
    platform_counts["huggingface"] = len(hf_results)

    print("📦 Running Package scanner...")
    package_results = package_scanner.scan()
    platform_counts["packages"] = len(package_results)

    all_results = github_results + hf_results + package_results
    saved_count = 0
    failed_count = 0
    
    print(f"💾 Saving {len(all_results)} agents to database...")
    
    with httpx.Client(timeout=30.0) as client:
        for result in all_results:
            agent_data = fingerprinter.fingerprint(result)
            try:
                response = client.post(API_URL, json=agent_data)
                if response.status_code == 200:
                    print(f"✅ Saved: {agent_data['name']} to database")
                    saved_count += 1
                else:
                    print(f"❌ Failed to save: {agent_data['name']} - HTTP {response.status_code}")
                    failed_count += 1
            except Exception as e:
                print(f"❌ Failed to save: {agent_data['name']} - {str(e)}")
                failed_count += 1
    
    duration = int(time.time() - start_time)
    total_after = get_total_agents_from_db()
    stats = get_stats()

    print(f"\n🏁 SCAN COMPLETE!")
    print(f"Scanned {len(github_results)} from GitHub, {len(hf_results)} from HuggingFace, {len(package_results)} packages")
    print(f"✅ {saved_count} total saved | ❌ {failed_count} failed")
    print(f"💾 Total agents now: {total_after} (+{total_after - total_before} new)")
    
    # Send Telegram summary
    try:
        notify_scan_complete(
            total_before=total_before,
            total_after=total_after,
            by_platform=platform_counts,
            by_model=stats.get("models", {}),
            by_framework=stats.get("frameworks", {}),
            duration_seconds=duration,
            errors=failed_count,
        )
    except Exception as e:
        print(f"⚠️ Telegram notification failed: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n🚨 Fatal error: {e}")
        notify_error(str(e))