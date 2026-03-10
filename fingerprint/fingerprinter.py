from typing import Dict, List


class Fingerprinter:
    MODELS = ["gpt-4", "gpt-3.5", "claude", "gemini", "llama", "mistral", "mixtral", "qwen"]
    FRAMEWORKS = ["langchain", "crewai", "autogen", "llamaindex", "haystack", "semantic-kernel"]
    CAPABILITIES = ["web-search", "email", "code-execution", "browser", "file-system", "database", "api-calls"]
    CRAWLER_KEYWORDS = ["playwright", "selenium"]
    
    def fingerprint(self, scanner_data: Dict) -> Dict:
        text = self._get_searchable_text(scanner_data)
        
        return {
            "name": scanner_data.get("name", ""),
            "source_url": scanner_data.get("url", ""),
            "source_platform": self._detect_platform(scanner_data.get("url", "")),
            "model_detected": self._detect_keyword(text, self.MODELS),
            "framework": self._detect_keyword(text, self.FRAMEWORKS),
            "capabilities": self._detect_capabilities(text),
            "agent_type": self._detect_agent_type(text),
            "risk_level": "safe",
            "stars": scanner_data.get("stars", 0),
            "raw_description": scanner_data.get("description", "")
        }
    
    def _get_searchable_text(self, data: Dict) -> str:
        parts = [
            data.get("description", ""),
            data.get("readme_snippet", ""),
            " ".join(data.get("topics", []))
        ]
        return " ".join(parts).lower()
    
    def _detect_keyword(self, text: str, keywords: List[str]) -> str:
        for keyword in keywords:
            if keyword in text:
                return keyword
        return "unknown"
    
    def _detect_capabilities(self, text: str) -> List[str]:
        return [cap for cap in self.CAPABILITIES if cap in text or cap.replace("-", "") in text]
    
    def _detect_agent_type(self, text: str) -> str:
        if "crewai" in text or "autogen" in text:
            return "multi-agent"
        if any(kw in text for kw in self.CRAWLER_KEYWORDS):
            return "crawler"
        return "task-agent"
    
    def _detect_platform(self, url: str) -> str:
        if "github.com" in url:
            return "github"
        if "huggingface.co" in url:
            return "huggingface"
        return "unknown"
