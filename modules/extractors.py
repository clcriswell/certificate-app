import asyncio
import trafilatura

class TrafilaturaExtractor:
    """Web content extractor using Trafilatura."""
    async def extract(self, url: str) -> str:
        downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
        return trafilatura.extract(downloaded, output_format="txt") or ""
