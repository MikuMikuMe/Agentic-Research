import arxiv
import requests
import io
from ddgs import DDGS
from bs4 import BeautifulSoup
from pypdf import PdfReader
import random

# --- Helper: User Agents ---
import socket
from urllib.parse import urlparse

# --- Helper: URL Validator (SSRF Protection) ---
def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Resolve to IP
        ip = socket.gethostbyname(hostname)
        
        # Block Private IPs (Simple Check)
        # 10.x.x.x, 192.168.x.x, 127.x.x.x, 172.16.x.x-172.31.x.x
        parts = ip.split('.')
        first = int(parts[0])
        second = int(parts[1])
        
        if first == 127: return False # Localhost
        if first == 10: return False # Private Class A
        if first == 192 and second == 168: return False # Private Class C
        if first == 172 and (16 <= second <= 31): return False # Private Class B
        if ip == "0.0.0.0": return False
        
        return True
    except:
        return False

# --- Helper: User Agents ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

def search_web(query: str, max_results: int = 5):
    """
    Search the web using DuckDuckGo.
    Args:
        query (str): The search query.
        max_results (int): Number of results to return.
    Returns:
        list: List of dicts {title, href, body}.
    """
    try:
        with DDGS() as ddgs:
            return [r for r in ddgs.text(query, max_results=max_results)]
    except Exception as e:
        print(f"Web search failed: {e}")
        return []

def search_arxiv(query: str, max_results: int = 3):
    """
    Search Arxiv for papers.
    Args:
        query (str): Search query (e.g., "reasoning modelscat:cs.AI").
        max_results (int): Max papers.
    Returns:
        list: List of dicts {title, id, summary, pdf_url, published}.
    """
    try:
        # Construct client
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        results = []
        for r in client.results(search):
            results.append({
                "title": r.title,
                "id": r.entry_id,
                "summary": r.summary,
                "pdf_url": r.pdf_url,
                "published": r.published.strftime("%Y-%m-%d")
            })
        return results
    except Exception as e:
        print(f"Arxiv search failed: {e}")
        return []

def read_pdf(url: str):
    """
    Download and read a PDF file.
    Args:
        url (str): URL to the PDF.
    Returns:
        str: Text content of the PDF.
    """
    try:
        if not is_safe_url(url):
             return "Error: Security Block (Private/Local IP access denied)"
             
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        # Disable redirects to prevent SSRF bypass via 30x to private IP
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
        response.raise_for_status()
        
        f = io.BytesIO(response.content)
        reader = PdfReader(f)
        
        text = ""
        # Read first 10 pages max to save token context
        for page in reader.pages[:10]:
            text += page.extract_text() + "\n"
            
        return text[:50000] # Safety Cap
    except Exception as e:
        print(f"PDF reading failed: {e}")
        return f"Error reading PDF: {e}"

def scrape_web_content(url: str):
    """
    Scrape text from a general web page (for Reddit/Twitter analysis).
    """
    try:
        if not is_safe_url(url):
             return "Error: Security Block (Private/Local IP access denied)"

        headers = {'User-Agent': random.choice(USER_AGENTS)}
        # Disable redirects to prevent SSRF bypass
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts/styles
        for s in soup(["script", "style", "nav", "footer"]):
            s.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        return text[:20000]
    except Exception as e:
        return f"Error scraping web: {e}"
