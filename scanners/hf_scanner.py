from typing import List, Dict
import httpx


class HuggingFaceScanner:
    TAGS = ["agent", "tool-calling", "assistant", "function-calling"]
    API_URL = "https://huggingface.co/api/models"

    def __init__(self):
        self.api_base = "http://localhost:8000"

    def _get_existing_urls(self) -> set:
        try:
            resp = httpx.get(f"{self.api_base}/agents?limit=99999", timeout=30)
            if resp.status_code == 200:
                return {a.get("source_url", "") for a in resp.json() if a.get("source_url")}
        except httpx.HTTPError:
            pass
        return set()

    def scan(self, max_models_per_tag: int = 10) -> List[Dict]:
        results = []
        existing_urls = self._get_existing_urls()
        seen_ids = set()

        for i, tag in enumerate(self.TAGS, 1):
            print(f"🤗 [HuggingFace] Searching tag: {tag}...")
            models = self._search_models(tag, max_models_per_tag)

            for model in models:
                model_id = model.get("id", "")
                url = f"https://huggingface.co/{model_id}"
                if model_id in seen_ids or url in existing_urls:
                    print(f"⏭  Skipping duplicate: {model_id}")
                    continue
                seen_ids.add(model_id)

                pipeline = model.get('pipeline_tag', 'unknown')
                print(f"🤗 [HuggingFace] Found: {model_id} | {pipeline} | {model.get('likes', 0)} likes")

                results.append({
                    "name": model_id,
                    "description": f"{model.get('pipeline_tag', '')} - {', '.join(model.get('tags', [])[:3])}",
                    "url": url,
                    "stars": model.get("likes", 0),
                    "topics": model.get("tags", []),
                    "last_updated": model.get("lastModified", ""),
                    "readme_snippet": f"Author: {model.get('author', 'unknown')}, Downloads: {model.get('downloads', 0)}"
                })

            print(f"--- HF Progress: {i}/{len(self.TAGS)} tags done | {len(results)} models found so far ---")

        return results

    def _search_models(self, tag: str, limit: int) -> List[Dict]:
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    self.API_URL,
                    params={"filter": tag, "sort": "likes", "direction": -1, "limit": limit}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"⚠️  HuggingFace API error for tag {tag}: {str(e)}")
            return []
