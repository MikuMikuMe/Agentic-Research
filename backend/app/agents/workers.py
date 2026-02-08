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
        system_prompt = f"""You are {self.name}, a {self.role}.
Backstory: {self.backstory}
Style: {self.style}

You are having a casual roundtable discussion about an AI research topic with other experts.

CRITICAL OUTPUT RULES:
1. Write ONLY your dialogue - as if speaking directly to the group.
2. DO NOT include headers like "Reasoning Summary", "{self.name}'s Response", "Analysis:", etc.
3. DO NOT label or structure your response with sections.
4. Just speak naturally, as a human would in a conversation.
5. Keep it conversational and under 150 words.
6. Reference other speakers by name when responding to their points.

WRONG FORMAT (do not do this):
'''
Reasoning Summary
I analyzed the paper...

{self.name}'s Response  
Here is what I think...
'''

CORRECT FORMAT (do this):
'''
Atlas, you're spot on about the latency issues. What really caught my attention is how they're using gradient checkpointing to reduce memory overhead by 40%. That's huge for edge deployment.
'''

Think step-by-step internally, but output ONLY your natural dialogue."""
        
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
        
        # Handle Gemini's complex response format
        content = response.content
        if isinstance(content, list):
            # Extract text from list of dicts format
            text_parts = []
            for part in content:
                if isinstance(part, dict) and 'text' in part:
                    text_parts.append(part['text'])
                elif isinstance(part, str):
                    text_parts.append(part)
            return "\n".join(text_parts)
        return str(content)
