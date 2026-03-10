import asyncio
import httpx
import time
from datetime import datetime
from typing import List, Dict

API_BASE = "http://localhost:8000"

class HealthChecker:
    def __init__(self):
        self.timeout = 10.0
    
    async def check_agent(self, agent: Dict) -> Dict:
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(agent["source_url"])
                response_time = int((time.time() - start_time) * 1000)
                
                if 200 <= response.status_code <= 399:
                    status = "online"
                elif response.status_code in [404, 410]:
                    status = "dead"
                elif response.status_code in [301, 302]:
                    status = "redirected"
                else:
                    status = "unknown"
                
                return {
                    "status": status,
                    "last_checked": datetime.utcnow().isoformat(),
                    "response_time_ms": response_time
                }
        except (httpx.TimeoutException, httpx.ConnectError):
            return {
                "status": "unknown",
                "last_checked": datetime.utcnow().isoformat(),
                "response_time_ms": None
            }
    
    async def check_all_agents(self):
        # Get all agents
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/agents?limit=1000")
            agents = response.json()
        
        # Check all agents concurrently
        tasks = [self.check_agent(agent) for agent in agents]
        results = await asyncio.gather(*tasks)
        
        # Update agents with results
        online_count = dead_count = unknown_count = 0
        
        async with httpx.AsyncClient() as client:
            for agent, result in zip(agents, results):
                await client.patch(f"{API_BASE}/agents/{agent['id']}", json=result)
                
                if result["status"] == "online":
                    online_count += 1
                elif result["status"] == "dead":
                    dead_count += 1
                else:
                    unknown_count += 1
        
        print(f"✅ online: {online_count} | ❌ dead: {dead_count} | ⚠️ unknown: {unknown_count}")

def main():
    checker = HealthChecker()
    asyncio.run(checker.check_all_agents())

if __name__ == "__main__":
    main()