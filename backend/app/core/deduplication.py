from app.services.supabase_client import get_supabase
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import get_settings
import hashlib

settings = get_settings()
supabase = get_supabase()

# Initialize embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001", 
    google_api_key=settings.GOOGLE_API_KEY
)

async def check_is_duplicate(url: str, title: str) -> bool:
    """
    Returns True if item is a duplicate (Exact URL or High Semantic Similarity).
    """
    # 1. Exact Match (URL Hash)
    # We should perform a quick check on 'known_items' table
    # This assumes table 'known_items' exists with 'url' column
    try:
        response = supabase.table("known_items").select("id").eq("url", url).execute()
        if response.data and len(response.data) > 0:
            return True
            
        # 2. Semantic Similarity (Vector)
        # Generate embedding for title
        vector = embeddings.embed_query(title)
        
        # RPC call to 'match_documents' (need to define this function in Supabase)
        # params: query_embedding, match_threshold, match_count
        rpc_response = supabase.rpc("match_documents", {
            "query_embedding": vector,
            "match_threshold": 0.85, # Strict threshold
            "match_count": 1
        }).execute()
        
        if rpc_response.data and len(rpc_response.data) > 0:
            return True
            
        return False
        
    except Exception as e:
        print(f"Deduplication check failed: {e}")
        return False # Fail open? Or stricter? Fail open for now to avoid blocking everything on error.

async def mark_as_seen(url: str, title: str):
    """
    Adds item to known_items with embedding.
    """
    try:
        vector = embeddings.embed_query(title)
        supabase.table("known_items").insert({
            "url": url,
            "title": title,
            "embedding": vector
        }).execute()
    except Exception as e:
        print(f"Failed to mark item as seen: {e}")
