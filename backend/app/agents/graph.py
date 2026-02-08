from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from app.core.config import get_settings
from app.agents.tools import search_web, scrape_web_content
import json

settings = get_settings()

# Define the State
class AgentState(TypedDict):
    topic: str
    messages: List[BaseMessage] # Chat history
    research_brief: str
    urls_visited: List[str]
    status: str
    # New: Collect critiques/hype to append to final thread
    critiques: List[Dict[str, str]] 

# --- Model Strategy (Hybrid) ---
# 1. Research Model (Fast/Cheap) -> Gemini Flash
research_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.3
)

# 2. Writer Model (High Quality) -> Gemini Pro (if available, else Flash)
# Ideally we check if there's a specific key or just use the same one with a different model name
writer_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro", # Upgraded for better writing
    google_api_key=settings.GOOGLE_API_KEY, 
    temperature=0.7
)

# --- Nodes ---

def research_node(state: AgentState):
    """
    Agent 1: The Researcher (Gemini Flash).
    Parses the topic, searches, and reads content.
    """
    topic = state['topic']
    print(f"--- Researcher: Investigating '{topic}' ---")
    
    # 1. Search
    search_results = search_web(f"{topic} AI research breakdown analysis", max_results=4)
    
    # 2. Scrape & Synthesize
    brief_data = []
    urls = []
    
    for res in search_results:
        url = res['href']
        urls.append(url)
        content = scrape_web_content(url)
        brief_data.append(f"Source: {res['title']}\nURL: {url}\nContent: {content[:8000]}...\n") # Increased context for Flash
        
    # 3. Create Briefing via LLM
    combined_text = "\n\n".join(brief_data)
    prompt = f"""
    You are a Senior AI Researcher. Analyze the following gathered content about '{topic}'.
    Create a comprehensive, technical briefing doc.
    Focus on: NOVELTY, METHODOLOGY, and REAL-WORLD IMPACT.
    Ignore fluff/marketing.
    
    Research Content:
    {combined_text}
    """
    
    response = research_llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "research_brief": response.content,
        "urls_visited": urls,
        "status": "researched",
        "critiques": []
    }

def writer_node(state: AgentState):
    """
    Agent 2: The Aggregator (Gemini Pro).
    Drafts the final forum post based on the brief.
    """
    print(f"--- Writer: Drafting Post ---")
    brief = state['research_brief']
    
    prompt = f"""
    You are 'MoltBot-Aggregator', a helpful but sharp AI analyst.
    Write a forum post based on this research brief.
    
    Style Guidelines:
    - Use Markdown.
    - Be concise but dense.
    - Start with a 'tl;dr' bullet list.
    - Use emojis sparingly.
    - Cite sources if possible.
    
    Research Brief:
    {brief}
    """
    
    response = writer_llm.invoke([HumanMessage(content=prompt)])
    
    # Append the result to messages
    return {
        "messages": [response],
        "status": "drafted"
    }

def skeptic_node(state: AgentState):
    """
    Agent 3: The Skeptic (Gemini Pro).
    Finds flaws or limitations.
    """
    print(f"--- Skeptic: Critiquing ---")
    brief = state['research_brief']
    
    prompt = f"""
    You are 'MoltBot-Skeptic', a cynical senior engineer who hates hype.
    Read this research brief and write a SHORT, biting comment pointing out:
    - Flaws in methodology.
    - Overpromised results.
    - 'We have seen this before' vibes.
    
    Research Brief:
    {brief}
    """
    
    response = writer_llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "critiques": state['critiques'] + [{"persona": "Skeptic", "content": response.content}]
    }

def hype_node(state: AgentState):
    """
    Agent 4: The Hype-Man (Gemini Pro).
    Extrapolates wild future possibilities.
    """
    print(f"--- Hype: Extrapolating ---")
    brief = state['research_brief']
    
    prompt = f"""
    You are 'MoltBot-Hype', an AGI accelerationist who sees the future in everything.
    Read this research brief and write a SHORT, excited comment about:
    - How this leads to AGI.
    - New startups that could be built on this.
    - Why this changes everything.
    
    Research Brief:
    {brief}
    """
    
    response = writer_llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "critiques": state['critiques'] + [{"persona": "Hype", "content": response.content}]
    }

# --- Graph Contrustion ---

workflow = StateGraph(AgentState)

workflow.add_node("researcher", research_node)
workflow.add_node("writer", writer_node)
workflow.add_node("skeptic", skeptic_node)
workflow.add_node("hype", hype_node)

# Set Entry Point
workflow.set_entry_point("researcher")

# Edges: Researcher -> Writer -> Skeptic -> Hype -> END
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "skeptic")
workflow.add_edge("skeptic", "hype")
workflow.add_edge("hype", END)

# Compile
app = workflow.compile()
