import re
from app.services.supabase_client import get_supabase
from app.core.config import get_settings

settings = get_settings()
supabase = get_supabase()

def extract_arxiv_id(url: str) -> str | None:
    """
    Extracts Arxiv paper ID from URL.
    Examples:
      - https://arxiv.org/abs/2401.12345 -> 2401.12345
      - https://arxiv.org/pdf/2401.12345.pdf -> 2401.12345
    """
    patterns = [
        r'arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'arxiv\.org/pdf/(\d{4}\.\d{4,5}(?:v\d+)?)\.pdf',
        r'arxiv:(\d{4}\.\d{4,5}(?:v\d+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            # Strip version number (e.g., v1, v2) for dedup
            arxiv_id = match.group(1)
            return re.sub(r'v\d+$', '', arxiv_id)
    return None

def normalize_title(title: str) -> str:
    """
    Normalizes title for fuzzy matching.
    Removes common prefixes like "Paper:" and extra whitespace.
    """
    # Remove common prefixes
    title = re.sub(r'^(Paper:|Research:|Study:|Analysis:)\s*', '', title, flags=re.IGNORECASE)
    # Lowercase and strip
    return title.lower().strip()

async def check_is_duplicate(url: str, title: str) -> bool:
    """
    Returns True if item is a duplicate.
    Checks:
      1. Arxiv ID match (most reliable for papers)
      2. Exact URL match in known_items
      3. Title match in known_items (normalized)
      4. Title match in threads (normalized)
    """
    try:
        # 1. Arxiv ID check (most reliable)
        arxiv_id = extract_arxiv_id(url)
        if arxiv_id:
            response = supabase.table("known_items").select("id").eq("arxiv_id", arxiv_id).execute()
            if response.data and len(response.data) > 0:
                print(f"--- Duplicate found by Arxiv ID: {arxiv_id} ---", flush=True)
                return True
        
        # 2. Check known_items by URL
        response = supabase.table("known_items").select("id").eq("url", url).execute()
        if response.data and len(response.data) > 0:
            print(f"--- Duplicate found by URL in known_items ---", flush=True)
            return True
        
        # 3. Check known_items by normalized title
        normalized = normalize_title(title)
        title_response = supabase.table("known_items").select("id, title").execute()
        for item in title_response.data or []:
            if normalize_title(item.get("title", "")) == normalized:
                print(f"--- Duplicate found by title in known_items: {title} ---", flush=True)
                return True
        
        # 4. Check threads table by normalized title
        thread_response = supabase.table("threads").select("id, topic_title").execute()
        for thread in thread_response.data or []:
            if normalize_title(thread.get("topic_title", "")) == normalized:
                print(f"--- Duplicate found by title in threads: {title} ---", flush=True)
                return True
            
        return False
        
    except Exception as e:
        print(f"Deduplication check failed: {e}", flush=True)
        return False

async def mark_as_seen(url: str, title: str):
    """
    Adds item to known_items for future deduplication.
    Stores URL, title, and Arxiv ID if available.
    """
    try:
        arxiv_id = extract_arxiv_id(url)
        data = {
            "url": url,
            "title": title
        }
        if arxiv_id:
            data["arxiv_id"] = arxiv_id
            
        supabase.table("known_items").insert(data).execute()
        print(f"--- Marked as seen: {title} (arxiv_id: {arxiv_id}) ---", flush=True)
    except Exception as e:
        print(f"Failed to mark item as seen: {e}", flush=True)
