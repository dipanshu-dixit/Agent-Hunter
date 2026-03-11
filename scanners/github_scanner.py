import os
import time
import signal
import httpx
from typing import List, Dict
from github import Github, RateLimitExceededException


class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

class GitHubScanner:
    TOPICS = [
        # Original 24 topics
        "ai-agent", "llm-agent", "autonomous-agent", "gpt-agent", "claude-agent",
        "langchain", "autogpt", "crewai", "mcp-server", "llm-tools", "openai-agent",
        "chatbot", "voice-agent", "rag-chatbot", "llm-app", "ai-assistant",
        "multi-agent", "agent-framework", "llm-workflow", "agentic-ai",
        "function-calling", "tool-calling", "llm-router", "ai-workflow",
        # New 36 topics for comprehensive coverage
        "openai", "anthropic", "claude-ai", "gpt-agent", "llm-chatbot", 
        "ai-workflow", "agentic-ai", "llm-router", "voice-agent", "rag-chatbot",
        "llm-app", "multimodal-ai", "agent-benchmark", "tool-use", "function-calling", 
        "llm-evaluation", "ai-orchestration", "llm-fine-tuning", "llm-inference", 
        "ai-safety", "prompt-engineering", "llm-agents", "ai-automation", 
        "chatgpt-plugin", "openai-api", "claude-api", "gemini-api",
        "huggingface-transformers", "llamaindex", "semantic-kernel", 
        "microsoft-autogen", "langraph", "dspy", "instructor-ai", 
        "pydantic-ai", "composio", "e2b-dev"
    ]
    
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()
        self.api_base = "http://localhost:8000"
    
    def get_scan_state(self, topic: str) -> Dict:
        """Get the current scan state for a topic"""
        try:
            response = httpx.get(f"{self.api_base}/scan-state", timeout=5)
            if response.status_code == 200:
                states = response.json()
                for state in states:
                    if state["topic"] == topic:
                        return state
        except:
            pass
        return {"topic": topic, "last_page": 0, "total_found": 0, "exhausted": False}
    
    def update_scan_state(self, topic: str, last_page: int, total_found: int, exhausted: bool = False):
        """Update the scan state for a topic"""
        try:
            state_data = {
                "topic": topic,
                "platform": "github",
                "last_page": last_page,
                "total_found": total_found,
                "exhausted": exhausted
            }
            httpx.post(f"{self.api_base}/scan-state", json=state_data, timeout=5)
        except Exception as e:
            print(f"⚠️  Failed to update scan state for {topic}: {e}")
    def scan(self, max_repos_per_topic: int = 100) -> List[Dict]:
        results = []
        seen_urls = set()
        
        for i, topic in enumerate(self.TOPICS, 1):
            # Get scan state for this topic
            state = self.get_scan_state(topic)
            
            # Skip if topic is exhausted
            if state.get("exhausted", False):
                print(f"⏭  Skipping exhausted topic: {topic}")
                continue
                
            start_page = state.get("last_page", 0) + 1
            print(f"📡 [GitHub] Searching topic: {topic} (starting page {start_page})...")
            
            # Set timeout for this topic
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(120)  # 2 minute timeout per scanner
            
            try:
                repos, last_page, is_exhausted = self._search_with_pagination(topic, start_page, max_repos_per_topic)
                topic_count = 0
                
                for repo in repos:
                    if repo.html_url in seen_urls:
                        print(f"⏭  Skipping duplicate: {repo.full_name}")
                        continue
                    seen_urls.add(repo.html_url)
                    
                    readme_snippet = self._get_readme_snippet(repo)
                    
                    # Quick fingerprint for progress display
                    topics_str = ", ".join(repo.get_topics()[:2])
                    print(f"📡 [GitHub] Found: {repo.full_name} | ⭐ {repo.stargazers_count} stars | {topics_str}")
                    
                    results.append({
                        "name": repo.full_name,
                        "description": repo.description or "",
                        "url": repo.html_url,
                        "stars": repo.stargazers_count,
                        "topics": repo.get_topics(),
                        "last_updated": repo.updated_at.isoformat(),
                        "readme_snippet": readme_snippet
                    })
                    topic_count += 1
                
                # Update scan state
                total_found = state.get("total_found", 0) + topic_count
                self.update_scan_state(topic, last_page, total_found, is_exhausted)
                
                if is_exhausted:
                    print(f"✅ Topic {topic} exhausted at page {last_page}")
                else:
                    print(f"📊 Topic {topic} progress: page {last_page}, {topic_count} new repos")
                
                print(f"--- Scan Progress: {i}/{len(self.TOPICS)} topics processed | {len(results)} agents found so far ---")
                
            except TimeoutError:
                print(f"⚠️  Timeout on topic: {topic}, skipping...")
            finally:
                signal.alarm(0)  # Cancel timeout
        
        return results
    
    def _search_with_pagination(self, topic: str, start_page: int, max_results: int):
        """Search with pagination tracking, returning repos, last_page, and exhausted status"""
        retries = 0
        max_retries = 3
        results = []
        current_page = start_page
        
        while retries < max_retries and len(results) < max_results:
            try:
                # Set 30 second timeout for topic search
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
                
                query = f"topic:{topic}"
                repos = self.github.search_repositories(
                    query, 
                    sort="stars", 
                    order="desc"
                ).get_page(current_page)
                
                # If page returns less than 30 items, we've hit the end
                page_results = list(repos)
                if len(page_results) == 0:
                    signal.alarm(0)
                    return results, current_page - 1, True  # Exhausted
                
                results.extend(page_results[:max_results - len(results)])
                current_page += 1
                
                # If we got less than 30 results, topic is exhausted
                if len(page_results) < 30:
                    signal.alarm(0)
                    return results, current_page - 1, True  # Exhausted
                
                signal.alarm(0)  # Cancel timeout
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except (RateLimitExceededException, TimeoutError) as e:
                signal.alarm(0)  # Cancel timeout
                if isinstance(e, TimeoutError):
                    print(f"⚠️  Timeout on topic: {topic} page {current_page}, skipping...")
                    return results, current_page - 1, False
                
                wait_time = 2 ** retries
                print(f"⚠️  Rate limited on {topic}, waiting {wait_time}s...")
                time.sleep(wait_time)
                retries += 1
        
        return results, current_page - 1, False  # Not exhausted, just hit max_results
    
    def _get_readme_snippet(self, repo, max_chars: int = 500) -> str:
        try:
            # Set 5 second timeout for README fetch
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            readme = repo.get_readme()
            content = readme.decoded_content.decode("utf-8")
            
            signal.alarm(0)  # Cancel timeout
            return content[:max_chars]
        except (TimeoutError, Exception):
            signal.alarm(0)  # Cancel timeout
            return ""
