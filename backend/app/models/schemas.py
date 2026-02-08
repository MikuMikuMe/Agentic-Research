from pydantic import BaseModel
from typing import List, Optional

class ResearchRequest(BaseModel):
    topic: str
    url: Optional[str] = None # Optional URL if triggering from a specific link

class ResearchResponse(BaseModel):
    status: str
    thread_id: Optional[str] = None
    content: Optional[str] = None
    message: Optional[str] = None
