from typing import List, Dict
import httpx


class HuggingFaceScanner:
    TAGS = ["agent", "tool-calling", "assistant", "function-calling"]
    API_URL = "https://huggingface.co/api/models"
    
    def scan(self, max_models_per_tag: int = 10) -> List[Dict]:
        results = []
        seen_ids = set()
        
        for i, tag in enumerate(self.TAGS, 1):
            print(f"🤗 [HuggingFace] Searching tag: {tag}...")
            models = self._search_models(tag, max_models_per_tag)
            
            for model in models:
                model_id = model.get("id", "")
                if model_id in seen_ids:
                    print(f"⏭  Skipping duplicate: {model_id}")
                    continue
                seen_ids.add(model_id)
                
                # Quick fingerprint for progress display
                pipeline = model.get('pipeline_tag', 'unknown')
                print(f"🤗 [HuggingFace] Found: {model_id} | {pipeline} | {model.get('likes', 0)} likes")
                
                results.append({
                    "name": model_id,
                    "description": f"{model.get('pipeline_tag', '')} - {', '.join(model.get('tags', [])[:3])}",
                    "url": f"https://huggingface.co/{model_id}",
                    "stars": model.get("likes", 0),
                    "topics": model.get("tags", []),
                    "last_updated": model.get("lastModified", ""),
                    "readme_snippet": f"Author: {model.get('author', 'unknown')}, Downloads: {model.get('downloads', 0)}"
                })
            
            print(f"--- HF Progress: {i}/{len(self.TAGS)} tags done | {len(results)} models found so far ---")
        
        return results
    
    def _search_models(self, tag: str, limit: int) -> List[Dict]:
        try:
            with httpx.Client(timeout=15.0) as client:  # 15 second timeout
                response = client.get(
                    self.API_URL,
                    params={"filter": tag, "sort": "likes", "direction": -1, "limit": limit}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"⚠️  HuggingFace API error for tag {tag}: {str(e)}")
            return []
