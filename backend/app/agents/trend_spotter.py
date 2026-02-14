from app.agents.tools import search_arxiv, search_web, fetch_hf_daily_papers
import random

class TrendSpotter:
    """
    The 'Eyes' of the system. Finds trending AI topics from Arxiv, HuggingFace, etc.
    Enforces AI-only constraints.
    """
    
    def find_trending_topic(self):
        """
        Scans Arxiv, HuggingFace Daily Papers, and Web for fresh AI topics.
        Randomly alternates between HF and Arxiv as primary source.
        Returns:
            dict: { "topic": str, "source": str, "origin_url": str, "summary": str } or None
        """
        # Randomly pick which source to try first (50/50 split)
        strategies = [self._try_huggingface, self._try_arxiv]
        random.shuffle(strategies)
        
        # Try primary source, then fallback
        for strategy in strategies:
            result = strategy()
            if result:
                return result
            
        # Strategy 3: Web Search for "AI News" (Final Fallback)
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

    def _try_huggingface(self):
        """Fetch trending papers from HuggingFace Daily Papers."""
        print("--- Trend Spotter: Scanning HuggingFace Daily Papers ---")
        papers = fetch_hf_daily_papers(max_results=10)
        if papers:
            paper = random.choice(papers)
            topic = f"Paper: {paper['title']}"
            print(f"--- Trend Spotter: Found HF Paper '{topic}' (⬆ {paper['upvotes']}) ---")
            return {
                "topic": topic,
                "source": "HuggingFace",
                "origin_url": paper['pdf_url'],  # ArXiv PDF URL for dedup
                "summary": paper['summary']
            }
        return None

    def _try_arxiv(self):
        """Search ArXiv for recent AI/CL papers."""
        print("--- Trend Spotter: Scanning Arxiv ---")
        papers = search_arxiv("cat:cs.AI OR cat:cs.CL", max_results=5)
        if papers:
            paper = random.choice(papers)
            topic = f"Paper: {paper['title']}"
            print(f"--- Trend Spotter: Found Arxiv Paper '{topic}' ---")
            return {
                "topic": topic,
                "source": "Arxiv",
                "origin_url": paper['pdf_url'],
                "summary": paper['summary']
            }
        return None

