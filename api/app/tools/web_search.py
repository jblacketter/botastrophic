"""Wikipedia search tool for bot web search actions."""

import logging
import httpx

logger = logging.getLogger(__name__)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"


USER_AGENT = "Botastrophic/1.0 (https://github.com/botastrophic; bot-forum-search)"


class WikipediaSearchTool:
    """Search Wikipedia and return article summaries."""

    async def search(self, query: str, max_results: int = 3) -> list[dict]:
        """Search Wikipedia and return article summaries."""
        headers = {"User-Agent": USER_AGENT}
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            # Search for articles
            search_resp = await client.get(WIKIPEDIA_API_URL, params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json",
                "origin": "*",
            })
            search_resp.raise_for_status()
            results = search_resp.json().get("query", {}).get("search", [])

            if not results:
                return []

            # Get extracts for each result
            summaries = []
            for r in results:
                title = r["title"]
                extract = await self._get_extract(client, title)
                summaries.append({
                    "title": title,
                    "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "extract": extract,
                })
            return summaries

    async def _get_extract(self, client: httpx.AsyncClient, title: str) -> str:
        """Get article extract (first ~5 sentences)."""
        resp = await client.get(WIKIPEDIA_API_URL, params={
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 5,
            "format": "json",
            "origin": "*",
        })
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        return page.get("extract", "")
