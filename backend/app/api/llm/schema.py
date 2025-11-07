from pydantic import BaseModel, Field, constr
from typing import Literal, List, Optional


class ChatMessage(BaseModel):
    """Represents a single message in the chat history (System, User, or Assistant)."""
    
    role: Literal['user', 'assistant'] = Field(description="The role of the sender.")
    
    content: constr(min_length=1, strict=True) = Field(description="The text content of the message.")

class TextChatModel(BaseModel):
    """Model for accepting an array of chat history messages."""
    
    chat_history: List[ChatMessage] = Field(
        ..., 
        description="The complete list of preceding messages in the OpenAI format.",
        min_items=1
    )