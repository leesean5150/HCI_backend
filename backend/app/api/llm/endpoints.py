from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from openai import OpenAI

from llm.gpt import get_openai_client
from . import schema
from . import handlers


router = APIRouter()

@router.post(
    "/chat",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Get chat response"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
    },
    
)
async def get_chat_response(
    chat_history: schema.TextChatModel,
    client: OpenAI = Depends(get_openai_client)
):
    try:
        response = await handlers.get_chat_response(chat_history=chat_history, client=client)
        return response
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_BAD_REQUEST,
            detail=f"Server failed: {str(e)}. Please try again in a while.",
        )

@router.post("/transcribe-audio/")
async def transcribe_audio(
    file: UploadFile = File(...), 
    client: OpenAI = Depends(get_openai_client)
):
    """
    Receives an audio file and transcribes it to text using OpenAI's Whisper model.
    """
    try:
        response = await handlers.get_audio_transcription(audio_file=file, client=client)
        return response
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_BAD_REQUEST,
            detail=f"Server failed: {str(e)}. Please try again in a while.",
        )