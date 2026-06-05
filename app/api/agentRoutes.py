from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from collections import defaultdict

from app.agent.planner import commerce_agent

agentRoutes = APIRouter()

# Kullanıcı bazlı sohbet geçmişi — TEK kaynak (planner'daki memory kaldırıldı)
conversation_history: Dict[str, List[dict]] = defaultdict(list)

MAX_HISTORY = 10  # Son 10 mesaj (5 tur)


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    prompt: str
    user_id: str = None


def build_chat_history_string(history: List[dict]) -> str:
    """
    Geçmiş mesajları agent'ın okuyabileceği string formatına çevirir.
    """
    if not history:
        return "Henüz sohbet geçmişi yok."
    
    lines = []
    for msg in history:
        role = "Kullanıcı" if msg["role"] == "user" else "Asistan"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


@agentRoutes.post("/agent", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_id = request.user_id

    # Geçmiş mesajları al (son mesajı eklemeden önce)
    history = conversation_history[user_id][-MAX_HISTORY:]
    chat_history_str = build_chat_history_string(history)

    # Agent'ı çalıştır
    response = await commerce_agent.run(
        user_input=request.message,
        chat_history=chat_history_str,
    )

    # Kullanıcı mesajını kaydet
    conversation_history[user_id].append({
        "role": "user",
        "content": request.message,
    })

    # Agent cevabını kaydet
    conversation_history[user_id].append({
        "role": "assistant",
        "content": response.answer,
    })

    # MAX_HISTORY'yi aş geçince eski mesajları sil
    if len(conversation_history[user_id]) > MAX_HISTORY * 2:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]

    return ChatResponse(prompt=response.answer, user_id=user_id)


@agentRoutes.delete("/agent/{user_id}")
async def clear_chat(user_id: str):
    conversation_history.pop(user_id, None)
    return {"success": True}


@agentRoutes.get("/agent/{user_id}")
async def get_history(user_id: str):
    return {
        "user_id": user_id,
        "history": conversation_history.get(user_id, []),
    }