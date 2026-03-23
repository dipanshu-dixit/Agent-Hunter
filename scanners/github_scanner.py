import os
import time
import signal
import httpx
from typing import List, Dict
from github import Github, RateLimitExceededException, GithubException


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")


class GitHubScanner:

    TOPICS = [
        "ai-agent","llm-agent","autonomous-agent","multi-agent",
        "agent-framework","agentic-ai","openai-agent","ai-agents",
        "llm-agents","autonomous-agents","intelligent-agent",

        "langchain","crewai","autogpt","pydantic-ai","smolagents",
        "dspy","semantic-kernel","llamaindex","langraph","langgraph",
        "microsoft-autogen","autogen","taskweaver","camel-ai",
        "agentops","openai-assistants","openai-swarm",

        "mcp-server","mcp","function-calling","voice-agent",
        "rag-chatbot","ai-workflow","tool-calling","llm-tools",
        "ai-tools","llm-tool","code-agent","coding-agent",
        "browser-agent","web-agent","computer-use",

        "openai-api","anthropic","gemini-api","ollama","llm-app",
        "claude","gpt-4","llama","mistral","deepseek",

        "rag","retrieval-augmented-generation","vector-database",
        "ai-memory","long-term-memory",

        "composio","n8n","llm-chatbot","ai-assistant","chatgpt",
        "gpt-wrapper","llm-inference","ai-automation",
        "prompt-engineering","ai-pipeline","ai-orchestration",

        "ai-copilot","coding-assistant","devops-agent",
        "data-agent","research-agent","sales-agent",
        "customer-service-ai","ai-secretary",
    ]

    KEYWORD_QUERIES = [
        "langchain agent","crewai agent","autogen agent",
        "llm agent python","ai agent framework","openai agent",
        "claude agent","langgraph agent","pydantic ai agent",
        "autonomous llm agent","multi agent llm","rag agent",
        "voice ai agent","coding agent llm","browser agent ai",
        "mcp server agent","smolagents","dspy agent",
        "ai workflow agent","llm tool calling",
    ]

    PAGES_PER_TOPIC = 5
    PAGES_PER_KEYWORD = 3
    SLEEP_BETWEEN_REQUESTS = 2.5
    MAX_RETRIES = 3

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()
        self.api_base = "http://localhost:8000"

    def _get_existing_urls(self) -> set:
        try:
            resp = httpx.get(f"{self.api_base}/agents?limit=99999", timeout=30)
            if resp.status_code == 200:
                return {a.get("source_url", "") for a in resp.json() if a.get("source_url")}
        except Exception:
            pass
        return set()

    def _fetch_page(self, query: str, sort: str, page: int) -> list:
        signal.signal(signal.SIGALRM, timeout_handler)

        for attempt in range(self.MAX_RETRIES):
            signal.alarm(120)
            try:
                results = list(
                    self.github.search_repositories(query, sort=sort, order="desc")
                    .get_page(page)
                )
                signal.alarm(0)
                return results

            except TimeoutError:
                print(f"  ⚠️ Timeout on '{query}' page {page}")

            except RateLimitExceededException:
                wait = 60 * (attempt + 1)
                print(f"  ⚠️ Rate limited — waiting {wait}s...")
                time.sleep(wait)

            except GithubException as e:
                print(f"  ⚠️ GitHub error: {e}")
                time.sleep(5)

            except Exception as e:
                print(f"  ⚠️ Error: {e}")
                time.sleep(5)

            finally:
                signal.alarm(0)

        return []

    def _safe_get_readme(self, repo) -> str:
        try:
            signal.alarm(5)
            content = repo.get_readme().decoded_content.decode("utf-8", errors="ignore")
            signal.alarm(0)
            return content[:500]
        except Exception:
            signal.alarm(0)
            return ""

    # 🔥 AUTO TAGGING
    def _classify_repo(self, repo, readme: str) -> str:
        text = f"{repo.name} {repo.description or ''} {readme}".lower()

        if any(k in text for k in ["awesome-", "list of", "tutorial", "course", "boilerplate", "template"]):
            return "junk"

        agent_score = sum(k in text for k in ["agent", "autonomous", "assistant", "copilot"])
        framework_score = sum(k in text for k in ["framework", "sdk", "library", "platform"])
        tool_score = sum(k in text for k in ["tool", "cli", "wrapper", "plugin"])

        if agent_score >= max(framework_score, tool_score):
            return "agent"
        elif framework_score >= tool_score:
            return "framework"
        else:
            return "tool"

    # 🔥 SCORING
    def _score_repo(self, repo, category: str) -> int:
        score = 0

        stars = repo.stargazers_count
        if stars > 5000:
            score += 5
        elif stars > 1000:
            score += 4
        elif stars > 200:
            score += 3
        elif stars > 50:
            score += 2
        else:
            score += 1

        days_old = (time.time() - repo.updated_at.timestamp()) / 86400
        if days_old < 30:
            score += 3
        elif days_old < 90:
            score += 2
        elif days_old < 180:
            score += 1

        if category == "agent":
            score += 3
        elif category == "framework":
            score += 2

        return score

    def _repo_to_dict(self, repo) -> dict:
        readme = self._safe_get_readme(repo)
        category = self._classify_repo(repo, readme)
        score = self._score_repo(repo, category)

        return {
            "name": repo.full_name,
            "description": repo.description or "",
            "url": repo.html_url,
            "stars": repo.stargazers_count,
            "topics": repo.get_topics(),
            "last_updated": repo.updated_at.isoformat(),
            "readme_snippet": readme,

            # NEW
            "category": category,
            "score": score,
        }

    def _scan_queries(self, queries: list, pages: int, sort: str,
                      seen_urls: set, label: str) -> List[Dict]:

        results = []

        for i, query in enumerate(queries, 1):
            print(f"🔍 [{i}/{len(queries)}] {label}: '{query}'")

            for page in range(pages):
                repos = self._fetch_page(query, sort, page)
                if not repos:
                    break

                new_on_page = 0

                for repo in repos:
                    if repo.html_url in seen_urls:
                        continue

                    repo_dict = self._repo_to_dict(repo)

                    # 🚫 Skip junk
                    if repo_dict["category"] == "junk":
                        continue

                    seen_urls.add(repo.html_url)
                    results.append(repo_dict)
                    new_on_page += 1

                    print(f"  ✅ {repo.full_name} ({repo.stargazers_count}★) [{repo_dict['category']}]")

                time.sleep(self.SLEEP_BETWEEN_REQUESTS)

                if new_on_page == 0 and page >= 1:
                    break

        return results

    def scan(self) -> List[Dict]:
        seen_urls = self._get_existing_urls()
        print(f"Pre-loaded {len(seen_urls)} existing URLs")

        all_results = []

        print("\n=== PASS 1: TOPICS ===")
        topic_queries = [f"topic:{t}" for t in self.TOPICS]
        all_results += self._scan_queries(
            topic_queries, self.PAGES_PER_TOPIC, "stars", seen_urls, "TOPIC"
        )

        print("\n=== PASS 2: KEYWORDS ===")
        all_results += self._scan_queries(
            self.KEYWORD_QUERIES, self.PAGES_PER_KEYWORD, "updated", seen_urls, "KEYWORD"
        )

        print(f"\n🎯 Total new agents: {len(all_results)}")
        return all_results