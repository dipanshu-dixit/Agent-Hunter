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
    # 20 distinct, non-overlapping topics
    TOPICS = [
        "ai-agent",
        "llm-agent",
        "autonomous-agent",
        "langchain",
        "crewai",
        "autogpt",
        "mcp-server",
        "openai-agent",
        "voice-agent",
        "rag-chatbot",
        "multi-agent",
        "agent-framework",
        "agentic-ai",
        "function-calling",
        "ai-workflow",
        "pydantic-ai",
        "smolagents",
        "dspy",
        "semantic-kernel",
        "composio",
    ]

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()
        self.api_base = "http://localhost:8000"

    def _get_existing_urls(self) -> set:
        """Pre-load all URLs already in DB to skip true duplicates across runs."""
        try:
            resp = httpx.get(f"{self.api_base}/agents?limit=9999", timeout=30)
            if resp.status_code == 200:
                return {a.get("source_url", "") for a in resp.json() if a.get("source_url")}
        except Exception:
            pass
        return set()

    def scan(self, max_repos_per_topic: int = 50) -> List[Dict]:
        results = []
        seen_urls = self._get_existing_urls()
        print(f"Pre-loaded {len(seen_urls)} existing URLs — will skip duplicates")

        for i, topic in enumerate(self.TOPICS, 1):
            print(f"📡 [{i}/{len(self.TOPICS)}] Scanning topic: {topic}...")
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(120)

            try:
                repos = list(
                    self.github.search_repositories(
                        f"topic:{topic}", sort="stars", order="desc"
                    ).get_page(0)
                )

                topic_count = 0
                for repo in repos[:max_repos_per_topic]:
                    if repo.html_url in seen_urls:
                        continue
                    seen_urls.add(repo.html_url)

                    readme = ""
                    try:
                        signal.alarm(5)
                        readme = repo.get_readme().decoded_content.decode("utf-8")[:500]
                        signal.alarm(0)
                    except Exception:
                        signal.alarm(0)

                    results.append({
                        "name": repo.full_name,
                        "description": repo.description or "",
                        "url": repo.html_url,
                        "stars": repo.stargazers_count,
                        "topics": repo.get_topics(),
                        "last_updated": repo.updated_at.isoformat(),
                        "readme_snippet": readme,
                    })
                    topic_count += 1
                    print(f"  ✅ {repo.full_name} ({repo.stargazers_count} stars)")

                print(f"  → {topic_count} new agents from {topic}")
                time.sleep(1)

            except TimeoutError:
                print(f"  ⚠️ Timeout on {topic}, skipping")
            except RateLimitExceededException:
                print(f"  ⚠️ Rate limited — waiting 60s...")
                time.sleep(60)
            finally:
                signal.alarm(0)

        print(f"GitHub scan complete: {len(results)} new agents")
        return results
