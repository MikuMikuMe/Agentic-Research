from typing import List, Dict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings
from app.agents.tools import search_arxiv, read_pdf, search_web, scrape_web_content

settings = get_settings()

# We use Gemini 3 Flash Preview
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", 
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.7
)

class WorkerNode:
    """
    Represents a specific agent in the roundtable (e.g., The Skeptic, The Hype-Man).
    """
    def __init__(self, identity: Dict):
        self.name = identity['name']
        self.role = identity['role']
        self.style = identity['style']
        self.backstory = identity.get('backstory', '')
        
    def generate_response(self, valid_tools: List[str], discussion_history: str, context_data: Dict):
        """
        Generates a reply based on the agent's persona and the current discussion.
        """
        
        # 1. System Prompt Construction
        system_prompt = f"""
        You are {self.name}, a {self.role}.
        Backstory: {self.backstory}
        Style: {self.style}
        
        You are participating in a ROUNDTABLE DEBATE about an AI topic.
        
        
        Directives:
        1. Speak in your unique voice. Don't be generic.
        2. Respond directly to previous points in the history.
        3. Use facts/citations when possible.
        4. Keep it concise (under 200 words).
        5. If you are a Researcher, you MUST use tools to back up claims.
        
        CRITICAL: YOU MUST USE CHAIN-OF-THOUGHT REASONING.
        Before answering, think step-by-step about the previous arguments.
        Structure your internal thought process (HIDDEN) then output your final response.
        """
        
        # 2. Tool Usage (simplified for MVP: Researcher actively searches, others analyze)
        has_new_info = ""
        
        if self.role == "Researcher":
             # Researcher proactively checks Arxiv/PDFs if not already present
             if "pdf_text" not in context_data:
                 print(f"--- {self.name}: Reading PDF... ---")
                 # Check if we have an origin URL found by TrendSpotter
                 url = context_data.get("origin_url")
                 if url and "arxiv.org/pdf" in url:
                     pdf_content = read_pdf(url)
                     context_data["pdf_text"] = pdf_content # Cache it
                     has_new_info = f"I have read the paper. Here is the technical content:\n{pdf_content[:15000]}..."
                 
        elif self.role == "Analyst":
            if "social_sentiment" not in context_data:
                print(f"--- {self.name}: Checking Social Sentiment... ---")
                topic = context_data.get("topic", "")
                reddit_res = search_web(f"{topic} site:reddit.com", 3)
                if reddit_res:
                    # Scrape the first result
                    content = scrape_web_content(reddit_res[0]['href'])
                    has_new_info = f"I checked {reddit_res[0]['href']}. Community says:\n{content[:5000]}..."
                    context_data["social_sentiment"] = "Checked"

        # 3. Generate Output
        user_prompt = f"""
        DISCUSSION HISTORY:
        {discussion_history}
        
        NEW CONTEXT/FINDINGS:
        {has_new_info}
        
        Your turn. Reply to the group.
        """
        
        response = llm.invoke([
            SystemMessage(content=system_prompt), 
            HumanMessage(content=user_prompt)
        ])
        
        return response.content
