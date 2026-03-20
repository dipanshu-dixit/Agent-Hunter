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
        # Core agent topics
        "ai-agent",
        "llm-agent",
        "autonomous-agent",
        "multi-agent",
        "agent-framework",
        "agentic-ai",
        "openai-agent",
        # Frameworks
        "langchain",
        "crewai",
        "autogpt",
        "pydantic-ai",
        "smolagents",
        "dspy",
        "semantic-kernel",
        "llamaindex",
        "langraph",
        "microsoft-autogen",
        # Capabilities
        "mcp-server",
        "function-calling",
        "voice-agent",
        "rag-chatbot",
        "ai-workflow",
        "tool-calling",
        "llm-tools",
        # Models/Platforms
        "openai-api",
        "anthropic",
        "gemini-api",
        "ollama",
        "llm-app",
        # Ecosystems
        "composio",
        "n8n",
        "llm-chatbot",
        "ai-assistant",
        "chatgpt",
        "gpt-wrapper",
        "rag",
        "llm-inference",
        "ai-automation",
        "prompt-engineering",
    ]

    # Pages to scan per topic — 3 pages × 30 repos = up to 90 repos per topic
    PAGES_PER_TOPIC = 3

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()
        self.api_base = "http://localhost:8000"

    def _get_existing_urls(self) -> set:
        """Pre-load all URLs already in DB to skip duplicates across runs."""
        try:
            resp = httpx.get(f"{self.api_base}/agents?limit=99999", timeout=30)
            if resp.status_code == 200:
                return {a.get("source_url", "") for a in resp.json() if a.get("source_url")}
        except Exception:
            pass
        return set()

    def scan(self, max_repos_per_topic: int = 90) -> List[Dict]:
        results = []
        seen_urls = self._get_existing_urls()
        print(f"Pre-loaded {len(seen_urls)} existing URLs — will skip duplicates")

        for i, topic in enumerate(self.TOPICS, 1):
            print(f"📡 [{i}/{len(self.TOPICS)}] Scanning topic: {topic}...")
            topic_count = 0
            topic_results = []

            for page in range(self.PAGES_PER_TOPIC):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(120)

                try:
                    repos = list(
                        self.github.search_repositories(
                            f"topic:{topic}", sort="stars", order="desc"
                        ).get_page(page)
                    )

                    if not repos:
                        signal.alarm(0)
                        break  # No more results for this topic

                    new_on_page = 0
                    for repo in repos[:max_repos_per_topic - topic_count]:
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

                        topic_results.append({
                            "name": repo.full_name,
                            "description": repo.description or "",
                            "url": repo.html_url,
                            "stars": repo.stargazers_count,
                            "topics": repo.get_topics(),
                            "last_updated": repo.updated_at.isoformat(),
                            "readme_snippet": readme,
                        })
                        topic_count += 1
                        new_on_page += 1
                        print(f"  ✅ {repo.full_name} ({repo.stargazers_count} stars)")

                    signal.alarm(0)

                    # If entire page was already known, no point going deeper
                    if new_on_page == 0:
                        print(f"  → Page {page} fully known, stopping pagination")
                        break

                    if topic_count >= max_repos_per_topic:
                        break

                    time.sleep(1)

                except TimeoutError:
                    signal.alarm(0)
                    print(f"  ⚠️ Timeout on {topic} page {page}, skipping")
                    break
                except RateLimitExceededException:
                    signal.alarm(0)
                    print(f"  ⚠️ Rate limited — waiting 60s...")
                    time.sleep(60)
                    break
                finally:
                    signal.alarm(0)

            results.extend(topic_results)
            print(f"  → {topic_count} new agents from {topic}")

        print(f"GitHub scan complete: {len(results)} new agents")
        return results
