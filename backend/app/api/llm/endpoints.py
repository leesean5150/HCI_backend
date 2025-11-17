from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from openai import OpenAI
from psycopg import AsyncConnection

from llm.gpt import get_openai_client
from db.postgres import get_async_session
from app import auth
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

@router.post(
    "/audio-to-expenditure",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Audio transcribed and expenditures created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request or invalid audio file"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def audio_to_expenditure(
    file: UploadFile = File(...),
    current_user: dict = Depends(auth.get_current_user),
    conn: AsyncConnection = Depends(get_async_session),
    client: OpenAI = Depends(get_openai_client)
):
    """
    Upload an audio file describing expenses. The audio will be:
    1. Transcribed using Whisper
    2. Processed by LLM to extract expense details
    3. Automatically create expenditures in the database
    """
    try:
        response = await handlers.process_audio_to_expenditures(
            audio_file=file,
            current_user=current_user,
            conn=conn,
            client=client
        )
        return response
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server failed to process audio: {str(e)}. Please try again.",
        )