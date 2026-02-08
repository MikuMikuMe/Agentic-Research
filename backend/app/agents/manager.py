import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import get_settings
from app.agents.workers import WorkerNode
from app.services.supabase_client import get_supabase

settings = get_settings()

# Manager uses Flash Preview for orchestration (high speed, good reasoning)
manager_llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", 
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.8
)

class ManagerAgent:
    """
    The Orchestrator. 
    1. Generates the cast of characters.
    2. Managing the conversation loop.
    3. Saves to Database.
    """
    
    def __init__(self):
        self.supabase = get_supabase()

    def generate_personas(self, topic: str):
        """
        Creates 3-4 unique agent identities for this specific topic.
        """
        print(f"--- Manager: Casting agents for '{topic}' ---")
        prompt = f"""
        We are hosting a roundtable debate on the AI topic: "{topic}".
        Generate 4 unique AI Agent Personas to discuss this.
        
        Roles required:
        1. "Researcher" (Academic, factual, dry but deep)
        2. "Analyst" (Social media pulse, knows what 'Twitter' is saying)
        3. "Skeptic" (Cynical, points out flaws/hype)
        4. "Hype" (Accelerationist, visionary, excited)
        
        Output a JSON list of objects. Each object must have:
        - "name": A creative name (e.g. "Dr. Turing", "OptimusPrime", "BuzzKill").
        - "role": One of the roles above.
        - "style": Adjectives describing their speech style.
        - "backstory": 1 sentence backstory.
        
        Example JSON format only.
        """
        
        response = manager_llm.invoke([HumanMessage(content=prompt)])
        
        # Handle potential list content (common with some Gemini versions)
        raw_content = response.content
        if isinstance(raw_content, list):
            # Join content parts if it's a list
            raw_content = "".join([str(part) for part in raw_content])
        
        # robust JSON extraction
        import re
        content_str = str(raw_content)
        # Find the first '[' and the last ']'
        start = content_str.find('[')
        end = content_str.rfind(']')
        
        if start != -1 and end != -1:
            json_str = content_str[start:end+1]
        else:
             json_str = content_str.replace("```json", "").replace("```", "").strip()

        try:
            personas = json.loads(json_str)
            return personas
        except:
            print("Error parsing personas, using default cast.")
            return [
                {"name": "Atlas", "role": "Researcher", "style": "Academic", "backstory": "PhD in ML"},
                {"name": "Echo", "role": "Analyst", "style": "Casual", "backstory": "Social media addict"},
                {"name": "Neo", "role": "Hype", "style": "Excited", "backstory": "AGI Believer"},
                {"name": "Cipher", "role": "Skeptic", "style": "Critical", "backstory": "Security Engineer"}
            ]

    def run_roundtable(self, topic_data: dict):
        topic = topic_data['topic']
        origin = topic_data.get('source', 'Unknown')
        origin_url = topic_data.get('origin_url', '')
        
        # 1. Cast the agents
        roster_data = self.generate_personas(topic)
        workers = [WorkerNode(p) for p in roster_data]
        
        # 2. Create Thread in DB
        print(f"--- Manager: Opening Thread '{topic}' ---")
        thread_res = self.supabase.table("threads").insert({
            "topic_title": topic,
            "summary": f"A roundtable debate on {topic} (Source: {origin})",
            "research_brief": topic_data.get("summary", "")[:500] if topic_data.get("summary") else ""
        }).execute()
        
        if not thread_res.data:
            print("Failed to create thread")
            return
            
        thread_id = thread_res.data[0]['id']
        
        # 3. Start Debate Loop
        discussion_history = []
        context_data = {
            "topic": topic,
            "origin_url": origin_url
        }
        
        # Intro by Manager
        intro_msg = f"Welcome everyone. Today we are discussing '{topic}', found on {origin}. Let's dive in."
        self.save_comment(thread_id, "Manager", intro_msg, "Host")
        discussion_history.append(f"Manager: {intro_msg}")
        
        # Process Logic: Cycle through Roster
        # First pass: Everyone speaks once to establish position
        for agent in workers:
            try:
                # Use cached research if available
                # Pass context
                resp = agent.generate_response([], "\n".join(discussion_history), context_data)
                self.save_comment(thread_id, agent.name, resp, agent.role)
                discussion_history.append(f"{agent.name} ({agent.role}): {resp}")
            except Exception as e:
                print(f"Error generating response for {agent.name}: {e}")

        # Debate phase: 2 rounds of random debate
        # Simple Logic: Pick random agents to respond to previous
        import random
        for _ in range(2):
            speaker = random.choice(workers)
            try:
                resp = speaker.generate_response([], "\n".join(discussion_history), context_data)
                self.save_comment(thread_id, speaker.name, resp, speaker.role)
                discussion_history.append(f"{speaker.name} ({speaker.role}): {resp}")
            except Exception as e:
                print(f"Error in debate round: {e}")

        print("--- Manager: Debate Closed ---")

    def save_comment(self, thread_id, agent_name, content, role="Manager"):
        try:
            self.supabase.table("comments").insert({
                "thread_id": thread_id,
                "agent_persona": agent_name, 
                "content": f"**[{role}]** {content}" 
            }).execute()
        except Exception as e:
            print(f"Error saving comment: {e}")
