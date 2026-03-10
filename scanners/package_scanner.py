from typing import List, Dict
import httpx


class PackageScanner:
    PYPI_PACKAGES = [
        "langchain", "crewai", "autogen", "llama-index", "haystack", "semantic-kernel",
        "agentops", "phidata", "dspy", "openai-agents", "pydantic-ai", "smolagents"
    ]
    
    NPM_PACKAGES = [
        "langchain", "openai-agents", "ai-sdk", "llamaindex", "autogen"
    ]
    
    def scan(self) -> List[Dict]:
        results = []
        
        print(f"📦 [Packages] Scanning PyPI packages...")
        # Scan PyPI packages
        for package in self.PYPI_PACKAGES:
            data = self._scan_pypi(package)
            if data:
                print(f"📦 [PyPI] Found: {package} | {data.get('readme_snippet', '').split(',')[0]}")
                results.append(data)
        
        print(f"📦 [Packages] Scanning npm packages...")
        # Scan npm packages
        for package in self.NPM_PACKAGES:
            data = self._scan_npm(package)
            if data:
                print(f"📦 [npm] Found: {package} | {data.get('readme_snippet', '').split(',')[0]}")
                results.append(data)
        
        print(f"--- Packages Progress: Complete | {len(results)} packages found ---")
        return results
    
    def _scan_pypi(self, package: str) -> Dict:
        try:
            with httpx.Client(timeout=15.0) as client:  # 15 second timeout
                response = client.get(f"https://pypi.org/pypi/{package}/json")
                if response.status_code == 200:
                    data = response.json()
                    info = data["info"]
                    
                    return {
                        "name": f"pypi/{package}",
                        "description": info.get("summary", ""),
                        "url": info.get("home_page", f"https://pypi.org/project/{package}/"),
                        "stars": 0,
                        "topics": ["python-package", "pypi"],
                        "last_updated": "",
                        "readme_snippet": f"Version: {info.get('version', 'unknown')}, Author: {info.get('author', 'unknown')}"
                    }
        except Exception as e:
            print(f"⚠️  PyPI error for {package}: {str(e)}")
        return None
    
    def _scan_npm(self, package: str) -> Dict:
        try:
            with httpx.Client(timeout=15.0) as client:  # 15 second timeout
                response = client.get(f"https://registry.npmjs.org/{package}")
                if response.status_code == 200:
                    data = response.json()
                    latest = data.get("dist-tags", {}).get("latest", "")
                    version_info = data.get("versions", {}).get(latest, {})
                    
                    return {
                        "name": f"npm/{package}",
                        "description": data.get("description", ""),
                        "url": data.get("homepage", f"https://www.npmjs.com/package/{package}"),
                        "stars": 0,
                        "topics": ["npm-package", "javascript"],
                        "last_updated": "",
                        "readme_snippet": f"Version: {latest}, Author: {version_info.get('author', {}).get('name', 'unknown')}"
                    }
        except Exception as e:
            print(f"⚠️  npm error for {package}: {str(e)}")
        return None