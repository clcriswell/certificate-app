import httpx
from typing import List, Dict, Any

class SerpAPISearch:
    """Search client using SerpAPI."""
    BASE_URL = "https://serpapi.com/search.json"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=20.0)

    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": num_results
        }
        resp = await self.client.get(self.BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("organic_results", [])[:num_results]
