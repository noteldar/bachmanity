from typing import Dict, Any
import os
from firecrawl import FirecrawlApp
import logging

logger = logging.getLogger(__name__)


def tool_deep_research(
    query: str,
    max_depth: int = 7,
    time_limit: int = 180,
    max_urls: int = 25,
) -> Dict[str, Any]:
    """
    Perform deep research on a query.

    Args:
        query: Research query to investigate
        max_depth: Number of research iterations (default: 7)
        time_limit: Time limit in seconds (default: 180)
        max_urls: Maximum URLs to analyze (default: 25)

    Returns:
        Dictionary with research results including final analysis and sources
    """
    try:
        api_key = os.getenv("FIRECRAWL_API_KEY")
        firecrawl = FirecrawlApp(api_key=api_key)

        params = {"maxDepth": max_depth, "timeLimit": time_limit, "maxUrls": max_urls}

        results = firecrawl.deep_research(
            query=query,
            params=params,
        )

        return results

    except Exception as e:
        logger.error(f"Error performing deep research: {e}")
        return {"error": f"Error performing deep research: {e}"}


def summarize_firecrawl_results(results: Dict[str, Any]) -> str:
    """
    Summarize the results of the deep research.
    """
    return results
