# fastapi ile API rotaları tanımlamak için kullanılan bir modül
from fastapi import APIRouter, HTTPException, Request
import httpx
from pydantic import BaseModel
import app.rag.pipeline as rag_pipeline

from app.llm.intent_detector import intent_detector
from app.llm.ollama_client import ollama_client

from app.agent.planner import commerce_agent

from typing import Dict, List
from collections import defaultdict


agentRoutes = APIRouter()

# Her kullanıcı için sohbet geçmişi
conversation_history: Dict[str, List[dict]] = defaultdict(list)

MAX_HISTORY = 12  # Her kullanıcı için maksimum sohbet geçmişi sayısı

class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    prompt: str
    user_id: str = None


async def run_agent(messages: List[dict]) -> str:
    """
    Buraya kendi commerce_agent entegrasyonunu koy.
    """
    prompt = "\n".join(
        [
            f"{m['role']}: {m['content']}"
            for m in messages
        ]
    )
    response = await commerce_agent.run(prompt)
    return response.answer



@agentRoutes.post("/agent", response_model=ChatResponse)
async def chat(request: ChatRequest):

    user_id = request.user_id

    # Kullanıcı mesajını geçmişe ekle
    conversation_history[user_id].append(
        {
            "role": "user",
            "content": request.message
        }
    )

    # Son N mesajı gönder
    history = conversation_history[user_id][-MAX_HISTORY:]

    answer = await run_agent(history)

    # Agent cevabını hafızaya ekle
    conversation_history[user_id].append(
        {
            "role": "assistant",
            "content": answer
        }
    )
    # historyi yazdır
    print(f"User {user_id} history:")
    for msg in conversation_history[user_id]:
        print(f"  {msg['role']}: {msg['content']}")
        
    return ChatResponse(prompt=answer, user_id=user_id)


@agentRoutes.delete("/agent/{user_id}")
async def clear_chat(user_id: str):

    if user_id in conversation_history:
        del conversation_history[user_id]

    return {
        "success": True
    }


@agentRoutes.get("/agent/{user_id}")
async def get_history(user_id: str):

    return {
        "user_id": user_id,
        "history": conversation_history.get(user_id, [])
    }