from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class PushRequest(BaseModel):
    do_reset: Optional[int] = 0
    

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SearchRequest(BaseModel):
    text: str
    limit: Optional[int] = 5
    chat_history: List[ChatMessage] = Field(default_factory=list)