import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import ResearchRequest, ResearchResponse
from app.agents.graph import app as agent_app
from app.core.deduplication import check_is_duplicate, mark_as_seen
from app.services.supabase_client import get_supabase
import uuid
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run Autonomous Loop
    import asyncio
    from app.agents.trend_spotter import TrendSpotter
    from app.agents.manager import ManagerAgent
    
    print("--- Starting Autonomous Research Loop ---", flush=True)
    
    async def run_loop():
        try:
            spotter = TrendSpotter()
            manager = ManagerAgent()
            print("--- Loop Agents Initialized ---", flush=True)
            
            MAX_THREADS = int(os.getenv("MAX_THREADS", "10"))  # Configurable limit
            
            while True:
                # 0. Check thread limit
                try:
                    thread_count_resp = get_supabase().table("threads").select("id", count="exact").execute()
                    current_count = thread_count_resp.count or 0
                    
                    if current_count >= MAX_THREADS:
                        print(f"--- Thread limit reached ({current_count}/{MAX_THREADS}). Pausing new content generation. ---", flush=True)
                        await asyncio.sleep(3600)  # Check again in 1 hour
                        continue
                except Exception as count_error:
                    print(f"Thread count check failed: {count_error}", flush=True)
                
                # 1. Find a topic
                try:
                    topic_data = spotter.find_trending_topic()
                    if topic_data:
                        # 2. Check for Duplicates
                        url = topic_data.get("origin_url", "")
                        title = topic_data.get("topic", "")
                        
                        is_dup = await check_is_duplicate(url, title)
                        if is_dup:
                            print(f"--- Skipping Duplicate: {title} ---", flush=True)
                            continue
                        
                        # 3. Mark as seen to prevent future duplicates
                        await mark_as_seen(url, title)
                         
                        # 4. Trigger Manager
                        manager.run_roundtable(topic_data)
                except Exception as e:
                    print(f"Loop Error: {e}", flush=True)
                    
                # Wait for next cycle (e.g., 4 hours)
                # For DEMO purposes, we wait 5 minutes to generate content more frequently
                print("Sleeping for 5 minutes...", flush=True)
                await asyncio.sleep(300) 
        except Exception as startup_error:
             print(f"CRITICAL: Loop Startup Failed: {startup_error}", flush=True)

    # Create Task
    loop_task = asyncio.create_task(run_loop())
    
    yield
    
    # Shutdown: Cancel Loop
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        print("--- Autonomous Research Loop Stopped ---", flush=True)

app = FastAPI(title="Agentic Research API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
