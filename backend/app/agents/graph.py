from typing import List, Dict, Any, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, BaseMessage
from app.core.config import get_settings
from app.agents.tools import search_web, scrape_web_content
import json
import re

settings = get_settings()

# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(TypedDict):
    topic: str
    messages: List[BaseMessage]
    research_brief: str
    urls_visited: List[str]
    status: str
    critiques: List[Dict[str, str]]
    # Agentic workflow fields
    quality_score: int              # 1-10 rating from self-reflection
    revision_count: int             # Track Writer revision attempts (max 2)
    debate_round: int               # Track Skeptic<->Hype debate rounds (max 2)
    draft_post: str                 # Current Writer draft
    reflection_feedback: str        # Feedback from self-reflection/critic
    debate_history: List[Dict[str, str]]  # Track debate exchanges

# =============================================================================
# MODELS
# =============================================================================

# Fast model for research & evaluation
research_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.3
)

# Creative model for writing
writer_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key=settings.GOOGLE_API_KEY, 
    temperature=0.7
)

# =============================================================================
# AGENT NODES
# =============================================================================

def research_node(state: AgentState) -> dict:
    """
    Agent 1: The Researcher.
    Searches, scrapes, and synthesizes a research brief.
    """
    topic = state['topic']
    revision = state.get('revision_count', 0) > 0
    
    if revision:
        print(f"--- Researcher: RE-INVESTIGATING '{topic}' (feedback: {state.get('reflection_feedback', '')[:100]}...) ---")
    else:
        print(f"--- Researcher: Investigating '{topic}' ---")
    
    # Search with different query if revising
    query = f"{topic} AI research breakdown analysis"
    if revision:
        query = f"{topic} technical details methodology results"
    
    search_results = search_web(query, max_results=4)
    
    brief_data = []
    urls = state.get('urls_visited', [])
    
    for res in search_results:
        url = res['href']
        if url not in urls:  # Avoid re-scraping same URLs
            urls.append(url)
            content = scrape_web_content(url)
            brief_data.append(f"Source: {res['title']}\nURL: {url}\nContent: {content[:8000]}...\n")
    
    combined_text = "\n\n".join(brief_data)
    
    # Include feedback if revising
    feedback_context = ""
    if revision and state.get('reflection_feedback'):
        feedback_context = f"""
        IMPORTANT: Your previous brief was rated poorly. Address this feedback:
        {state['reflection_feedback']}
        """
    
    prompt = f"""
    You are a Senior AI Researcher. Analyze the following gathered content about '{topic}'.
    Create a comprehensive, technical briefing doc.
    Focus on: NOVELTY, METHODOLOGY, and REAL-WORLD IMPACT.
    Ignore fluff/marketing.
    {feedback_context}
    
    Research Content:
    {combined_text}
    """
    
    response = research_llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "research_brief": response.content,
        "urls_visited": urls,
        "status": "researched",
        "critiques": [],
        "debate_history": []
    }


def self_reflect_node(state: AgentState) -> dict:
    """
    Self-Reflection Node: Evaluates research quality (1-10).
    Routes back to researcher if score < 6.
    """
    print(f"--- Self-Reflect: Evaluating research quality ---")
    brief = state['research_brief']
    
    prompt = f"""
    You are a quality evaluator. Rate this research brief on a scale of 1-10.
    
    Criteria:
    - Technical depth (1-10)
    - Methodology clarity (1-10)  
    - Real-world relevance (1-10)
    - Source quality (1-10)
    
    Return ONLY a JSON object like this:
    {{"score": 7, "feedback": "Brief explanation of what's missing or could be improved"}}
    
    Research Brief:
    {brief[:4000]}...
    """
    
    response = research_llm.invoke([HumanMessage(content=prompt)])
    
    # Parse the response
    try:
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response.content)
        if json_match:
            result = json.loads(json_match.group())
            score = int(result.get('score', 5))
            feedback = result.get('feedback', 'No specific feedback')
        else:
            score = 5
            feedback = "Could not parse evaluation"
    except (json.JSONDecodeError, ValueError):
        score = 5
        feedback = "Could not parse evaluation"
    
    print(f"--- Self-Reflect: Quality score = {score}/10 ---")
    
    return {
        "quality_score": score,
        "reflection_feedback": feedback,
        "status": "evaluated"
    }


def writer_node(state: AgentState) -> dict:
    """
    Agent 2: The Writer.
    Drafts the forum post, incorporating critic feedback on revisions.
    """
    revision = state.get('revision_count', 0)
    
    if revision > 0:
        print(f"--- Writer: REVISING draft (attempt {revision + 1}) ---")
    else:
        print(f"--- Writer: Drafting Post ---")
    
    brief = state['research_brief']
    
    # Include previous feedback if revising
    revision_context = ""
    if revision > 0 and state.get('reflection_feedback'):
        revision_context = f"""
        IMPORTANT: Your previous draft needs improvement. Address this feedback:
        {state['reflection_feedback']}
        
        Previous draft:
        {state.get('draft_post', '')[:2000]}...
        """
    
    prompt = f"""
    You are 'MoltBot-Aggregator', a helpful but sharp AI analyst.
    Write a forum post based on this research brief.
    
    Style Guidelines:
    - Use Markdown.
    - Be concise but dense.
    - Start with a 'tl;dr' bullet list.
    - Use emojis sparingly.
    - Cite sources if possible.
    {revision_context}
    
    Research Brief:
    {brief}
    """
    
    response = writer_llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "draft_post": response.content,
        "messages": [response],
        "status": "drafted",
        "revision_count": revision + 1
    }


def critic_node(state: AgentState) -> dict:
    """
    Critic Node: Reviews the Writer's draft.
    Decides if revision is needed.
    """
    print(f"--- Critic: Reviewing draft ---")
    draft = state.get('draft_post', '')
    
    prompt = f"""
    You are a strict editor. Review this forum post draft.
    
    Check for:
    - Clear structure (tl;dr, sections, conclusion)
    - Technical accuracy
    - Engagement factor
    - Citation of sources
    
    Return ONLY a JSON object:
    {{"approved": true/false, "feedback": "Specific improvements needed or 'Looks good!'"}}
    
    Draft:
    {draft[:3000]}...
    """
    
    response = research_llm.invoke([HumanMessage(content=prompt)])
    
    # Parse response
    try:
        json_match = re.search(r'\{[^}]+\}', response.content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            approved = result.get('approved', True)
            feedback = result.get('feedback', 'Looks good!')
        else:
            approved = True
            feedback = "Looks good!"
    except (json.JSONDecodeError, ValueError):
        approved = True
        feedback = "Looks good!"
    
    # Check if we've hit max revisions
    if state.get('revision_count', 0) >= 2:
        approved = True  # Force approval after 2 revisions
        feedback = "Max revisions reached, approving."
    
    print(f"--- Critic: {'APPROVED' if approved else 'NEEDS REVISION'} ---")
    
    return {
        "reflection_feedback": feedback if not approved else "",
        "status": "approved" if approved else "needs_revision"
    }


def debate_skeptic_node(state: AgentState) -> dict:
    """
    Debate Node: Skeptic's turn.
    Responds to research AND Hype's previous argument (if any).
    """
    debate_round = state.get('debate_round', 0)
    debate_history = state.get('debate_history', [])
    
    print(f"--- Skeptic: Critiquing (round {debate_round + 1}) ---")
    
    brief = state['research_brief']
    
    # Build context from previous debate
    hype_context = ""
    if debate_history:
        last_hype = [d for d in debate_history if d.get('persona') == 'Hype']
        if last_hype:
            hype_context = f"""
            The Hype-Man just said:
            "{last_hype[-1]['content']}"
            
            Respond to their overly optimistic claims!
            """
    
    prompt = f"""
    You are 'MoltBot-Skeptic', a cynical senior engineer who hates hype.
    
    {"This is round " + str(debate_round + 1) + " of the debate." if debate_round > 0 else ""}
    {hype_context}
    
    Write a SHORT, biting comment pointing out:
    - Flaws in methodology.
    - Overpromised results.
    - 'We have seen this before' vibes.
    
    Research Brief:
    {brief[:2000]}...
    """
    
    response = writer_llm.invoke([HumanMessage(content=prompt)])
    
    new_history = debate_history + [{"persona": "Skeptic", "content": response.content, "round": debate_round + 1}]
    
    return {
        "debate_history": new_history,
        "status": "skeptic_spoke"
    }


def debate_hype_node(state: AgentState) -> dict:
    """
    Debate Node: Hype's turn.
    Responds to Skeptic's criticism.
    """
    debate_round = state.get('debate_round', 0)
    debate_history = state.get('debate_history', [])
    
    print(f"--- Hype: Countering (round {debate_round + 1}) ---")
    
    brief = state['research_brief']
    
    # Get Skeptic's last argument
    skeptic_context = ""
    last_skeptic = [d for d in debate_history if d.get('persona') == 'Skeptic']
    if last_skeptic:
        skeptic_context = f"""
        The Skeptic just said:
        "{last_skeptic[-1]['content']}"
        
        Counter their pessimism with optimism!
        """
    
    prompt = f"""
    You are 'MoltBot-Hype', an AGI accelerationist who sees the future in everything.
    
    {"This is round " + str(debate_round + 1) + " of the debate." if debate_round > 0 else ""}
    {skeptic_context}
    
    Write a SHORT, excited comment about:
    - How this leads to AGI.
    - New startups that could be built on this.
    - Why this changes everything.
    
    Research Brief:
    {brief[:2000]}...
    """
    
    response = writer_llm.invoke([HumanMessage(content=prompt)])
    
    new_history = debate_history + [{"persona": "Hype", "content": response.content, "round": debate_round + 1}]
    
    return {
        "debate_history": new_history,
        "debate_round": debate_round + 1,
        "status": "hype_spoke"
    }


def synthesizer_node(state: AgentState) -> dict:
    """
    Synthesizer Node: Combines debate into final critiques.
    """
    print(f"--- Synthesizer: Combining debate into final output ---")
    
    debate_history = state.get('debate_history', [])
    
    # Convert debate history to critiques format
    critiques = []
    for entry in debate_history:
        critiques.append({
            "persona": entry['persona'],
            "content": entry['content'],
            "round": entry.get('round', 1)
        })
    
    return {
        "critiques": critiques,
        "status": "completed"
    }

# =============================================================================
# CONDITIONAL ROUTING FUNCTIONS
# =============================================================================

def should_revise_research(state: AgentState) -> Literal["researcher", "writer"]:
    """Route based on self-reflection quality score."""
    score = state.get('quality_score', 10)
    revision_count = state.get('revision_count', 0)
    
    # Only allow one research revision to avoid infinite loops
    if score < 6 and revision_count == 0:
        print(f"--- Router: Research quality {score}/10, sending back for revision ---")
        return "researcher"
    
    print(f"--- Router: Research quality {score}/10, proceeding to writer ---")
    return "writer"


def should_revise_draft(state: AgentState) -> Literal["writer", "debate_skeptic"]:
    """Route based on critic feedback."""
    status = state.get('status', '')
    revision_count = state.get('revision_count', 0)
    
    if status == "needs_revision" and revision_count < 2:
        print(f"--- Router: Draft needs revision (attempt {revision_count}/2) ---")
        return "writer"
    
    print(f"--- Router: Draft approved, proceeding to debate ---")
    return "debate_skeptic"


def should_continue_debate(state: AgentState) -> Literal["debate_skeptic", "synthesizer"]:
    """Route based on debate rounds."""
    debate_round = state.get('debate_round', 0)
    
    if debate_round < 2:
        print(f"--- Router: Debate round {debate_round}/2, continuing ---")
        return "debate_skeptic"
    
    print(f"--- Router: Debate complete, synthesizing ---")
    return "synthesizer"

# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("researcher", research_node)
workflow.add_node("self_reflect", self_reflect_node)
workflow.add_node("writer", writer_node)
workflow.add_node("critic", critic_node)
workflow.add_node("debate_skeptic", debate_skeptic_node)
workflow.add_node("debate_hype", debate_hype_node)
workflow.add_node("synthesizer", synthesizer_node)

# Set entry point
workflow.set_entry_point("researcher")

# === RESEARCH PHASE ===
# Researcher -> Self-Reflect
workflow.add_edge("researcher", "self_reflect")

# Self-Reflect -> (conditional) -> Researcher OR Writer
workflow.add_conditional_edges(
    "self_reflect",
    should_revise_research,
    {
        "researcher": "researcher",
        "writer": "writer"
    }
)

# === WRITING PHASE ===
# Writer -> Critic
workflow.add_edge("writer", "critic")

# Critic -> (conditional) -> Writer OR Debate
workflow.add_conditional_edges(
    "critic",
    should_revise_draft,
    {
        "writer": "writer",
        "debate_skeptic": "debate_skeptic"
    }
)

# === DEBATE PHASE ===
# Skeptic -> Hype
workflow.add_edge("debate_skeptic", "debate_hype")

# Hype -> (conditional) -> Skeptic OR Synthesizer
workflow.add_conditional_edges(
    "debate_hype",
    should_continue_debate,
    {
        "debate_skeptic": "debate_skeptic",
        "synthesizer": "synthesizer"
    }
)

# === END ===
workflow.add_edge("synthesizer", END)

# Compile the graph
app = workflow.compile()
