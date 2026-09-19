import os
import re
from dotenv import load_dotenv
from tavily import TavilyClient

from services.credibility import get_source_score

# ==========================================================
# Load Environment Variables
# ==========================================================

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=api_key) if api_key else None

# ==========================================================
# Helper Functions
# ==========================================================

def remove_duplicate_articles(results):
    """
    Remove duplicate URLs.
    """
    unique = []
    seen = set()

    for article in results:
        url = article.get("url", "").strip()
        if url and url not in seen:
            seen.add(url)
            unique.append(article)

    return unique


def clean_text(text):
    """Clean HTML tags and collapse whitespace."""
    if not text:
        return ""
    cleaned = re.sub(r'<[^>]+>', '', str(text))
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def filter_empty_articles(results):
    """
    Remove articles without sufficient content and clean snippet text.
    """
    filtered = []

    for article in results:
        content = clean_text(article.get("content", ""))
        title = clean_text(article.get("title", ""))
        if content and len(content) > 40:
            article["content"] = content
            article["title"] = title or "Verified News Article"
            filtered.append(article)

    return filtered


def rank_articles(results):
    """
    Rank articles using source credibility score.
    """
    for article in results:
        article["credibility"] = get_source_score(article.get("url", ""))

    results.sort(
        key=lambda x: x["credibility"],
        reverse=True
    )

    return results


# ==========================================================
# Main Search Function (Retrieves top 20 articles)
# ==========================================================

def search_news(query):
    if not client:
        print("Tavily API client not initialized (missing API key).")
        return []

    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=6
        )

        results = response.get("results", [])

        # 1. Remove duplicate URLs
        results = remove_duplicate_articles(results)

        # 2. Filter out weak/empty articles
        results = filter_empty_articles(results)

        # 3. Rank by source credibility
        results = rank_articles(results)

        # Return top 6 retrieved articles for fast, high-quality verification
        return results[:6]
    except Exception as e:
        print(f"Tavily search error: {e}")
        return []