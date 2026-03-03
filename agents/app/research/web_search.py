"""DuckDuckGo web search tool (task 7.1).

Returns top-N search results as ``{title, url, snippet}`` dicts.
"""

from __future__ import annotations

from duckduckgo_search import DDGS


class WebSearchTool:
    """Web search using DuckDuckGo.

    Parameters
    ----------
    default_max_results:
        Default number of results to return when ``max_results`` is not
        specified in :meth:`search`.
    """

    def __init__(self, default_max_results: int = 5) -> None:
        self.default_max_results = default_max_results

    def search(self, query: str, max_results: int | None = None) -> list[dict]:
        """Search the web and return structured results.

        Parameters
        ----------
        query:
            Search query string.
        max_results:
            Maximum number of results.  Defaults to ``self.default_max_results``.

        Returns
        -------
        list[dict]
            Each item has ``title``, ``url``, and ``snippet`` keys.
        """
        n = max_results if max_results is not None else self.default_max_results
        with DDGS() as ddgs:
            raw = ddgs.text(query, max_results=n)

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in (raw or [])
        ]
