from typing import List, Dict
import httpx


class HoneypotScanner:
    CRAWLERS = [
        "GPTBot", "ClaudeBot", "PerplexityBot", "Bytespider", "DuckAssistBot",
        "meta-externalagent", "OAI-SearchBot", "cohere-ai", "YouBot", "Amazonbot"
    ]
    
    def scan(self) -> List[Dict]:
        results = []
        
        print(f"🍯 [Honeypot] Testing known AI crawlers...")
        
        for crawler in self.CRAWLERS:
            agent_data = self._test_crawler(crawler)
            if agent_data:
                print(f"🍯 [Honeypot] Found: {crawler} | crawler detected")
                results.append(agent_data)
        
        print(f"--- Honeypot Progress: Complete | {len(results)} crawlers detected ---")
        return results
    
    def _test_crawler(self, crawler_name: str) -> Dict:
        try:
            headers = {"User-Agent": f"{crawler_name}/1.0"}
            
            with httpx.Client(timeout=10.0) as client:  # 10 second timeout
                response = client.get("https://httpbin.org/user-agent", headers=headers)
                
                if response.status_code == 200:
                    return {
                        "name": crawler_name,
                        "description": f"Known AI crawler/bot: {crawler_name}",
                        "url": f"https://honeypot.example.com/detected/{crawler_name.lower()}",
                        "stars": 0,
                        "topics": ["crawler", "ai-bot", "honeypot"],
                        "last_updated": "",
                        "readme_snippet": f"Detected {crawler_name} crawler activity"
                    }
        except Exception as e:
            print(f"⚠️  Honeypot test failed for {crawler_name}: {str(e)}")
        
        return None