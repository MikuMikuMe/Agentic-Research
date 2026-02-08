from app.agents.tools import search_arxiv, search_web
import random

class TrendSpotter:
    """
    The 'Eyes' of the system. Finds trending AI topics from Arxiv, HuggingFace, etc.
    Enforces AI-only constraints.
    """
    
    def find_trending_topic(self):
        """
        Scans mainly Arxiv and Web for fresh AI topics.
        Returns:
            dict: { "topic": str, "source": str, "url": str } or None
        """
        # Strategy 1: Recent Arxiv Papers (High Quality, Pure AI)
        print("--- Trend Spotter: Scanning Arxiv ---")
        papers = search_arxiv("cat:cs.AI OR cat:cs.CL", max_results=5)
        
        if papers:
            # Pick a random one to diversify the feed if running frequently
            paper = random.choice(papers)
            topic = f"Paper: {paper['title']}"
            print(f"--- Trend Spotter: Found Arxiv Paper '{topic}' ---")
            return {
                "topic": topic,
                "source": "Arxiv",
                "origin_url": paper['pdf_url'],
                "summary": paper['summary']
            }
            
        # Strategy 2: Web Search for "AI News" (Fallback)
        print("--- Trend Spotter: Scanning AI News ---")
        news = search_web("trending AI breakthroughs this week site:techcrunch.com OR site:venturebeat.com", max_results=3)
        if news:
            article = random.choice(news)
            print(f"--- Trend Spotter: Found News '{article['title']}' ---")
            return {
                "topic": article['title'],
                "source": "Web News",
                "origin_url": article['href'],
                "summary": article['body']
            }
            
        return None
