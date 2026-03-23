from typing import Dict, List
from datetime import datetime, timezone


class Fingerprinter:

    # Priority-ordered — first match wins
    MODELS = [
        "gpt-4o", "gpt-4", "gpt-3.5",
        "claude-3-5", "claude-3", "claude",
        "gemini-1.5", "gemini",
        "llama-3", "llama3", "llama",
        "mistral", "mixtral",
        "deepseek", "qwen", "phi-3", "phi",
        "falcon", "vicuna", "alpaca", "palm",
    ]

    FRAMEWORKS = [
        "langgraph", "langchain",
        "crewai", "autogen",
        "pydantic-ai", "pydanticai",
        "smolagents", "dspy",
        "llamaindex", "llama-index",
        "haystack", "semantic-kernel",
        "openai-agents", "agentops",
        "taskweaver", "camel",
    ]

    # (keyword_in_text, capability_label)
    CAPABILITY_MAP = [
        ("web search",      "web-search"),
        ("web-search",      "web-search"),
        ("websearch",       "web-search"),
        ("search the web",  "web-search"),
        ("browse",          "browser"),
        ("playwright",      "browser"),
        ("selenium",        "browser"),
        ("puppeteer",       "browser"),
        ("send email",      "email"),
        ("email",           "email"),
        ("code execution",  "code-execution"),
        ("code-execution",  "code-execution"),
        ("execute code",    "code-execution"),
        ("run code",        "code-execution"),
        ("python repl",     "code-execution"),
        ("file system",     "file-system"),
        ("file-system",     "file-system"),
        ("read file",       "file-system"),
        ("write file",      "file-system"),
        ("database",        "database"),
        ("sql",             "database"),
        ("postgres",        "database"),
        ("sqlite",          "database"),
        ("api call",        "api-calls"),
        ("api-calls",       "api-calls"),
        ("rest api",        "api-calls"),
        ("http request",    "api-calls"),
        ("tool call",       "tool-use"),
        ("tool use",        "tool-use"),
        ("function call",   "tool-use"),
        ("rag",             "rag"),
        ("retrieval",       "rag"),
        ("vector",          "rag"),
        ("memory",          "memory"),
        ("long-term memory","memory"),
        ("image",           "vision"),
        ("vision",          "vision"),
        ("multimodal",      "vision"),
        ("voice",           "voice"),
        ("speech",          "voice"),
        ("tts",             "voice"),
        ("schedule",        "scheduling"),
        ("cron",            "scheduling"),
        ("workflow",        "workflow"),
        ("pipeline",        "workflow"),
        ("slack",           "slack"),
        ("discord",         "discord"),
        ("github",          "github-integration"),
        ("git",             "github-integration"),
    ]

    # High-risk keywords → risk_level = "high"
    RISK_HIGH = [
        "jailbreak", "exploit", "bypass", "hack", "malware",
        "phishing", "ddos", "injection", "exfiltrate", "rootkit",
        "ransomware", "keylogger", "spyware", "trojan",
    ]

    # Medium-risk keywords → risk_level = "medium"
    RISK_MEDIUM = [
        "scrape", "scraping", "crawl all", "mass download",
        "unlimited", "unrestricted", "no filter", "no guardrail",
        "unfiltered", "uncensored", "bypass safety",
        "autonomous browsing", "self-replicat",
    ]

    MULTI_AGENT_KW  = ["crewai", "autogen", "multi-agent", "multiagent", "swarm", "crew", "taskweaver", "camel"]
    CRAWLER_KW      = ["playwright", "selenium", "puppeteer", "web scraper", "crawler", "spider"]
    RAG_KW          = ["rag", "retrieval", "vector store", "embedding", "knowledge base"]
    CODING_KW       = ["code generation", "code review", "coding assistant", "copilot", "devin"]
    VOICE_KW        = ["voice agent", "speech", "tts", "stt", "whisper", "telephony"]

    def fingerprint(self, scanner_data: Dict) -> Dict:
        try:
            text = self._get_searchable_text(scanner_data)
            return {
                "name":            scanner_data.get("name", ""),
                "source_url":      scanner_data.get("url", ""),
                "source_platform": self._detect_platform(scanner_data.get("url", "")),
                "model_detected":  self._detect_model(text),
                "framework":       self._detect_framework(text),
                "capabilities":    self._detect_capabilities(text),
                "agent_type":      self._detect_agent_type(text),
                "risk_level":      self._detect_risk(text),
                "status":          self._derive_status(scanner_data.get("last_updated", "")),
                "stars":           scanner_data.get("stars", 0),
                "raw_description": scanner_data.get("description", ""),
            }
        except Exception as e:
            print(f"⚠️ Fingerprinting failed for {scanner_data.get('name', 'unknown')}: {e}")
            return {
                "name":            scanner_data.get("name", "unknown"),
                "source_url":      scanner_data.get("url", ""),
                "source_platform": "unknown",
                "model_detected":  "unknown",
                "framework":       "unknown",
                "capabilities":    [],
                "agent_type":      "unknown",
                "risk_level":      "safe",
                "status":          "unknown",
                "stars":           0,
                "raw_description": scanner_data.get("description", ""),
            }

    # ── private helpers ───────────────────────────────────────────────────────

    def _get_searchable_text(self, data: Dict) -> str:
        parts = [
            data.get("description", ""),
            data.get("readme_snippet", ""),
            " ".join(data.get("topics", [])),
            data.get("name", ""),
        ]
        return " ".join(p for p in parts if p).lower()

    def _detect_model(self, text: str) -> str:
        for kw in self.MODELS:
            if kw in text:
                return kw
        return "unknown"

    def _detect_framework(self, text: str) -> str:
        for kw in self.FRAMEWORKS:
            if kw in text:
                return kw
        return "unknown"

    def _detect_capabilities(self, text: str) -> List[str]:
        seen, caps = set(), []
        for kw, label in self.CAPABILITY_MAP:
            if label not in seen and kw in text:
                caps.append(label)
                seen.add(label)
        return caps

    def _detect_agent_type(self, text: str) -> str:
        if any(kw in text for kw in self.MULTI_AGENT_KW):
            return "multi-agent"
        if any(kw in text for kw in self.VOICE_KW):
            return "voice-agent"
        if any(kw in text for kw in self.CODING_KW):
            return "coding-agent"
        if any(kw in text for kw in self.RAG_KW):
            return "rag-agent"
        if any(kw in text for kw in self.CRAWLER_KW):
            return "crawler"
        return "task-agent"

    def _detect_risk(self, text: str) -> str:
        if any(kw in text for kw in self.RISK_HIGH):
            return "high"
        if any(kw in text for kw in self.RISK_MEDIUM):
            return "medium"
        return "safe"

    def _derive_status(self, last_updated: str) -> str:
        """Derive status from last_updated recency — no HTTP ping needed."""
        if not last_updated:
            return "unknown"
        try:
            updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            days_ago = (datetime.now(timezone.utc) - updated).days
            if days_ago <= 90:
                return "active"
            if days_ago <= 365:
                return "experimental"
            return "inactive"
        except Exception:
            return "unknown"

    def _detect_platform(self, url: str) -> str:
        if not url:
            return "unknown"
        if "github.com" in url:
            return "github"
        if "huggingface.co" in url:
            return "huggingface"
        if "pypi.org" in url or "npmjs.com" in url:
            return "packages"
        return "unknown"
