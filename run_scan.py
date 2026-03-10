import httpx
from scanners.github_scanner import GitHubScanner
from scanners.hf_scanner import HuggingFaceScanner
from scanners.discord_scanner import DiscordScanner
from scanners.honeypot_scanner import HoneypotScanner
from scanners.package_scanner import PackageScanner
from fingerprint.fingerprinter import Fingerprinter

API_URL = "http://localhost:8000/agents"

def main():
    print("🚀 Starting AgentScout scan...")
    
    github_scanner = GitHubScanner()
    hf_scanner = HuggingFaceScanner()
    discord_scanner = DiscordScanner()
    honeypot_scanner = HoneypotScanner()
    package_scanner = PackageScanner()
    fingerprinter = Fingerprinter()
    
    print("📡 Running GitHub scanner...")
    github_results = github_scanner.scan()
    
    print("🤗 Running HuggingFace scanner...")
    hf_results = hf_scanner.scan()
    
    print("💬 Running Discord scanner...")
    discord_results = discord_scanner.scan()
    
    print("🍯 Running Honeypot scanner...")
    honeypot_results = honeypot_scanner.scan()
    
    print("📦 Running Package scanner...")
    package_results = package_scanner.scan()
    
    all_results = github_results + hf_results + discord_results + honeypot_results + package_results
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
    
    print(f"\n🏁 SCAN COMPLETE!")
    print(f"Scanned {len(github_results)} from GitHub, {len(hf_results)} from HuggingFace, {len(discord_results)} from Discord, {len(honeypot_results)} honeypots, {len(package_results)} packages")
    print(f"✅ {saved_count} total saved | ❌ {failed_count} failed")

if __name__ == "__main__":
    main()