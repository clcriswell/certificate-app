import httpx
from typing import List, Dict, Any

class TwitterExtractor:
    """Twitter API client for recent tweets search."""
    SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

    def __init__(self, bearer_token: str):
        self.client = httpx.AsyncClient(timeout=20.0, headers={
            "Authorization": f"Bearer {bearer_token}"
        })

    async def fetch_posts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        params = {
            "query": query,
            "max_results": min(limit, 100),
            "tweet.fields": "public_metrics,created_at,author_id"
        }
        resp = await self.client.get(self.SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
