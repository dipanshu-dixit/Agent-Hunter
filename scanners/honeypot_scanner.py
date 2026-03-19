from typing import List, Dict


class HoneypotScanner:
    """Disabled — was sending requests to httpbin.org with spoofed user-agents
    and recording them as discovered agents. Generated only fake noise."""

    def scan(self) -> List[Dict]:
        print("🍯 [Honeypot] Disabled — skipping.")
        return []
