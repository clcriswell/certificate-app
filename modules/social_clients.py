import httpx
import asyncio
from typing import List, Dict, Any
import logging

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
        for attempt in range(3):
            try:
                resp = await self.client.get(self.SEARCH_URL, params=params)
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data.get("data", [])
            except httpx.HTTPError as e:
                logging.warning("Twitter API error on attempt %d: %s", attempt + 1, e)
                await asyncio.sleep(2 ** attempt)
        logging.error("Twitter API failed after retries; skipping.")
        return []
