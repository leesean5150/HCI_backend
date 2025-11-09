from pydantic import BaseModel, Field, conlist
from typing import Literal, List, Union


class ImageURL(BaseModel):
    """Specifies an image via a URL (Base64)."""
    url: str = Field(description="The image URL as a Base64 encoded string with a data URI prefix.")

class ImageContentPart(BaseModel):
    """A content part containing an image."""
    type: Literal['image_url'] = 'image_url'
    image_url: ImageURL

class TextContentPart(BaseModel):
    """A content part containing text."""
    type: Literal['text'] = 'text'
    text: str

class ChatMessage(BaseModel):
    """Represents a single message in the chat history (User or Assistant).""" 

    role: Literal['user', 'assistant'] = Field(description="The role of the sender.")
    content: conlist(
        Union[TextContentPart, ImageContentPart], 
        min_length=1 
    ) = Field(
        description="A list of content parts (must contain at least one text or image part or audio part)."
    )

class TextChatModel(BaseModel):
    """Model for accepting an array of chat history messages."""
    
    chat_history: List[ChatMessage] = Field(
        ..., 
        description="The complete list of preceding messages in the OpenAI format.",
        min_items=1
    )