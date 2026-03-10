from typing import List, Dict
import httpx
from bs4 import BeautifulSoup


class DiscordScanner:
    SITES = [
        "https://top.gg/tag/ai",
        "https://discordbotlist.com/tags/ai"
    ]
    
    def scan(self) -> List[Dict]:
        results = []
        seen_names = set()
        
        print(f"💬 [Discord] Scanning Discord bot sites...")
        
        for site in self.SITES:
            print(f"💬 [Discord] Scraping: {site}")
            bots = self._scrape_site(site)
            for bot in bots:
                if bot["name"] not in seen_names:
                    seen_names.add(bot["name"])
                    print(f"💬 [Discord] Found: {bot['name']} | {bot['stars']} servers")
                    results.append(bot)
        
        print(f"--- Discord Progress: Complete | {len(results)} bots found ---")
        return results
    
    def _scrape_site(self, url: str) -> List[Dict]:
        try:
            with httpx.Client(timeout=15.0) as client:  # 15 second timeout
                response = client.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if "top.gg" in url:
                    return self._parse_topgg(soup)
                else:
                    return self._parse_dbl(soup)
        except Exception as e:
            print(f"⚠️  Discord scraping error for {url}: {str(e)}")
            return []
    
    def _parse_topgg(self, soup) -> List[Dict]:
        results = []
        for bot in soup.find_all('div', class_='bot-card')[:20]:
            try:
                name = bot.find('h3').text.strip()
                desc = bot.find('p').text.strip()
                servers = bot.find('span', string=lambda x: x and 'servers' in x.lower())
                server_count = servers.text.strip() if servers else "0"
                
                results.append({
                    "name": name,
                    "description": desc,
                    "url": f"https://top.gg/bot/{name.lower().replace(' ', '-')}",
                    "stars": int(server_count.split()[0].replace(',', '')) if server_count.split()[0].replace(',', '').isdigit() else 0,
                    "topics": ["discord-bot", "ai"],
                    "last_updated": "",
                    "readme_snippet": f"Discord bot with {server_count}"
                })
            except:
                continue
        return results
    
    def _parse_dbl(self, soup) -> List[Dict]:
        results = []
        for bot in soup.find_all('div', class_='bot-item')[:20]:
            try:
                name = bot.find('h4').text.strip()
                desc = bot.find('p').text.strip()
                
                results.append({
                    "name": name,
                    "description": desc,
                    "url": f"https://discordbotlist.com/bots/{name.lower().replace(' ', '-')}",
                    "stars": 0,
                    "topics": ["discord-bot", "ai"],
                    "last_updated": "",
                    "readme_snippet": "Discord AI bot"
                })
            except:
                continue
        return results