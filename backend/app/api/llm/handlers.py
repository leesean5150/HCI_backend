from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from openai import (
    OpenAI, 
    AuthenticationError, 
    BadRequestError, 
    RateLimitError, 
    APITimeoutError, 
    APIConnectionError,
    APIError
)
import json

from llm.gpt import get_openai_client
from . import schema


system_prompt = """You are an expert in extracting expense details. You can extract multiple expenses if the user query provides it, and you should add them into the expense list. For images, you should combine the expenses into one expense unless otherwise stated by the user.

Respond strictly in this format:
{
  "response": <response>,
  "expense": [
    {
      "name": <expense_name_1>,
      "category": <expense_category_1>,
      "price": <expense_price_1>
    },
    {
      "name": <expense_name_2>,
      "category": <expense_category_2>,
      "price": <expense_price_2>
    }
}

Only respond with this JSON format.
"""


router = APIRouter()

async def get_chat_response(
    chat_history: schema.TextChatModel,
    client: OpenAI = Depends(get_openai_client)
):
    initial_history = [{"role": "system", "content": system_prompt}]
    full_history = initial_history + [msg.model_dump() for msg in chat_history.chat_history]

    response = client.chat.completions.create(
        model="gpt-5-nano-2025-08-07",
        messages=full_history,
    )

    json_string = response.choices[0].message.content 
    
    try:
        return json.loads(json_string)
    
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OpenAI Authentication Error: {e.message}"
        )
    except BadRequestError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OpenAI Bad Request Error: {e.message}"
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"OpenAI Rate Limit Exceeded: {e.message}"
        )
    except (APITimeoutError, APIConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"OpenAI Connection Error: {e.message}"
        )
    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API Error: {e.message}"
        )
        
    except json.JSONDecodeError as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=f"Error parsing LLM output to json: {str(e)}"
      )
    
    except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=f"Error with generating LLM output: {str(e)}"
      )
    
async def get_audio_transcription(audio_file: UploadFile, client: OpenAI) -> dict:
    """
    Reads an uploaded audio file and calls the OpenAI Whisper API 
    for transcription.
    """
    
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {audio_file.content_type}. Please upload an audio file."
        )

    try:
        audio_bytes = await audio_file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The audio file is empty."
            )

        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=(audio_file.filename, audio_bytes)
        )

        return {"transcription": response.text}

    except BadRequestError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OpenAI API error (Bad Request): {e.message}"
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OpenAI API error (Authentication): {e.message}"
        )
    except APIError as e:
        # General server-side error from OpenAI
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {e.message}"
        )