from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI

from llm.gpt import get_openai_client
from . import schema
from . import handlers


router = APIRouter()

@router.post(
    "/text",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Get text chat response"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
    },
    
)
async def get_chat_text_response(
    chat_history: schema.TextChatModel,
    client: OpenAI = Depends(get_openai_client)
):
    try:
        response = await handlers.get_text_chat_response(chat_history=chat_history, client=client)
        return response
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_BAD_REQUEST,
            detail=f"Server failed: {str(e)}. Please try again in a while.",
        )