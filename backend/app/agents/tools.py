from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
import random

# User Agents to avoid simple blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

def perform_search(query: str, max_results: int = 5):
    """
    Executes a search using DuckDuckGo and returns a list of results.
    """
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
            return results
    except Exception as e:
        print(f"Search failed: {e}")
        return []

def scrape_content(url: str) -> str:
    """
    Fetches and parses the main text content of a given URL.
    Refuses to scrape PDFs directly for now (requires different libs), 
    but handles standard HTML.
    """
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Simple limiting to avoid context overflow if not chunked later
        return text[:50000] # Cap at ~50k chars for Gemini Flash context safety
    except Exception as e:
        print(f"Scraping failed for {url}: {e}")
        return f"Error scraping {url}: {str(e)}"
