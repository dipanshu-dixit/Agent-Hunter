import os
import time
import signal
from typing import List, Dict
from github import Github, RateLimitExceededException


class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

class GitHubScanner:
    TOPICS = [
        "ai-agent", "llm-agent", "autonomous-agent", "gpt-agent", "claude-agent",
        "langchain", "autogpt", "crewai", "mcp-server", "llm-tools", "openai-agent",
        "chatbot", "voice-agent", "rag-chatbot", "llm-app", "ai-assistant",
        "multi-agent", "agent-framework", "llm-workflow", "agentic-ai",
        "function-calling", "tool-calling", "llm-router", "ai-workflow"
    ]
    
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()
    
    def scan(self, max_repos_per_topic: int = 100) -> List[Dict]:
        results = []
        seen_urls = set()
        
        for i, topic in enumerate(self.TOPICS, 1):
            print(f"📡 [GitHub] Searching topic: {topic}...")
            
            # Set timeout for this topic
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(120)  # 2 minute timeout per scanner
            
            try:
                repos = self._search_with_backoff(topic, max_repos_per_topic)
                
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
                
                print(f"--- Scan Progress: {i}/{len(self.TOPICS)} topics done | {len(results)} agents found so far ---")
                
            except TimeoutError:
                print(f"⚠️  Timeout on topic: {topic}, skipping...")
            finally:
                signal.alarm(0)  # Cancel timeout
        
        return results
    
    def _search_with_backoff(self, topic: str, max_results: int):
        retries = 0
        max_retries = 3
        results = []
        
        while retries < max_retries:
            try:
                # Set 30 second timeout for topic search
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
                
                query = f"topic:{topic}"
                repos = self.github.search_repositories(query, sort="stars", order="desc")
                
                for repo in repos:
                    if len(results) >= max_results:
                        break
                    results.append(repo)
                
                signal.alarm(0)  # Cancel timeout
                return results
                
            except (RateLimitExceededException, TimeoutError) as e:
                signal.alarm(0)  # Cancel timeout
                if isinstance(e, TimeoutError):
                    print(f"⚠️  Timeout on topic: {topic}, skipping...")
                    return []
                
                wait_time = 2 ** retries
                print(f"⚠️  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                retries += 1
        
        return results
    
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
