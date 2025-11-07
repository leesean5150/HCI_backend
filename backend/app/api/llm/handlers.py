from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
import json

from llm.gpt import get_openai_client
from . import schema


system_prompt = """You are an expert in extracting expense details. You can extract multiple expenses if the user query provides it, and you should add them into the expense list.

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

async def get_text_chat_response(
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