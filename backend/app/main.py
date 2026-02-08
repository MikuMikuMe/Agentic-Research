from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import ResearchRequest, ResearchResponse
from app.agents.graph import app as agent_app
from app.core.deduplication import check_is_duplicate, mark_as_seen
from app.services.supabase_client import get_supabase
import uuid

app = FastAPI(title="Agentic Research API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Agent System Online"}

@app.post("/research", response_model=ResearchResponse)
async def trigger_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Triggers the Deep Research Agent.
    1. Checks uniqueness.
    2. Runs LangGraph (Search -> Read -> Write).
    3. Saves to Supabase.
    """
    topic = request.topic
    url = request.url or f"manual://{uuid.uuid4()}" # Generate dummy URL for manual topics
    
    # 1. Deduplication Check
    is_dupe = await check_is_duplicate(url, topic)
    if is_dupe:
        return ResearchResponse(status="skipped", message="Topic already covered (Duplicate detected).")

    # 2. Run Agent (Synchronous for MVP, can be async/background)
    try:
        # Initial State
        initial_state = {
            "topic": topic,
            "messages": [],
            "research_brief": "",
            "urls_visited": [],
            "status": "start"
        }
        
        # Invoke Graph
        output = agent_app.invoke(initial_state)
        
        # Extract Result (The Writer's message)
        final_message = output['messages'][-1].content
        critiques = output.get('critiques', []) # Get Skeptic/Hype comments
        
        # 3. Save to Supabase
        supabase = get_supabase()
        
        # Create Thread
        thread_data = {
            "topic_title": topic,
            "summary": final_message[:200] + "...", # Simple preview
            "research_brief": output.get('research_brief', ''),
        }
        thread_res = supabase.table("threads").insert(thread_data).execute()
        thread_id = thread_res.data[0]['id']
        
        # Save the Post as the first "comment" (Aggregator)
        comments_to_insert = [
            {
                "thread_id": thread_id,
                "agent_persona": "Aggregator", 
                "content": final_message
            }
        ]
        
        # Add Critiques (Skeptic / Hype)
        for critique in critiques:
            # Depending on graph implementation, critique might be dict or object
            # in our graph.py, it's a dict: {"persona": "Skeptic", "content": "..."}
            if isinstance(critique, dict):
                 comments_to_insert.append({
                    "thread_id": thread_id,
                    "agent_persona": critique.get("persona", "Unknown"),
                    "content": critique.get("content", "")
                })
        
        supabase.table("comments").insert(comments_to_insert).execute()
        
        # Mark as Seen
        await mark_as_seen(url, topic)
        
        return ResearchResponse(
            status="success", 
            thread_id=thread_id, 
            content=final_message
        )
        
    except Exception as e:
        print(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
