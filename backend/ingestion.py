import requests
from bs4 import BeautifulSoup
import time
import os
from app.core.config import get_settings

settings = get_settings()
API_URL = os.getenv("API_URL", "http://localhost:8000/research")

def fetch_daily_papers():
    """
    Scrapes Hugging Face Daily Papers for trending AI research.
    """
    print("Fetching today's papers...")
    url = "https://huggingface.co/papers"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Select paper titles (simple selector based on structure)
        # Note: Selectors change, this targets the main h3 links usually present
        articles = soup.select('article h3 a') 
        
        papers = []
        for a in articles[:5]: # Top 5 papers
            title = a.get_text(strip=True)
            link = "https://huggingface.co" + a['href']
            papers.append({"title": title, "url": link})
            
        print(f"Found {len(papers)} papers.")
        return papers
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return []

def trigger_research_for_papers():
    papers = fetch_daily_papers()
    
    for paper in papers:
        print(f"Triggering research for: {paper['title']}")
        try:
            payload = {
                "topic": paper['title'],
                "url": paper['url'] 
            }
            # Add simple auth if needed later
            res = requests.post(API_URL, json=payload)
            if res.status_code == 200:
                data = res.json()
                print(f"Result: {data['status']} - {data.get('message', 'Success')}")
            else:
                print(f"Failed: {res.text}")
        except Exception as e:
            print(f"Request failed: {e}")
        
        time.sleep(2) # Be nice to the API

if __name__ == "__main__":
    print("Starting Ingestion Service (Polling every 12 hours)...")
    while True:
        trigger_research_for_papers()
        print("Sleeping for 12 hours...")
        time.sleep(43200) # 12 hours
