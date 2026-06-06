from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from collections import defaultdict

from google import genai

import structlog

from app.agent.planner import commerce_agent
from app.core.config import config
from app.core.rate_limit import RateLimiter

logger = structlog.get_logger(__name__)

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

rate_limit = RateLimiter(
    max_requests=3,
    window_seconds=60
)


client = genai.Client(api_key=config.GEMINI_API_KEY)

@agentRoutes.post("/agent", response_model=ChatResponse, dependencies=[Depends(rate_limit)])
async def chat(request: ChatRequest):
    user_id = request.user_id
    
    logger.info("agent_request_received", user_id=user_id, message=request.message)
    
    rewrite_prompt = f"""
    Sen bir e-ticaret sisteminde çalışan sorgu sadeleştiricisisin.

    GÖREVİN:

    - Kullanıcının yazım hatalarını düzelt.
    - Gereksiz kelimeleri kaldır.
    - Ürün adlarını koru.
    - Marka adlarını koru.
    - Kullanıcının amacını netleştir.
    - Cevap verme.
    - Açıklama yapma.
    - Olması gereken formatta sadece optimize edilmiş sorguyu döndür.

    Kullanıcı:
    {request.message}

    Çıktı:
    """
    
    geminiResponse = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=rewrite_prompt
    )
    
    logger.info("optimized_query_generated", user_id=user_id, optimized_query=geminiResponse.text.strip())
    

    # Geçmiş mesajları al (son mesajı eklemeden önce)
    history = conversation_history[user_id][-MAX_HISTORY:]
    chat_history_str = build_chat_history_string(history)

    # Agent'ı çalıştır
    response = await commerce_agent.run(
        user_input=geminiResponse.text.strip(),
        chat_history=chat_history_str,
    )

    # Kullanıcı mesajını kaydet
    conversation_history[user_id].append({
        "role": "user",
        "content": response.answer,
    })

    # Agent cevabını kaydet
    conversation_history[user_id].append({
        "role": "assistant",
        "content": response.answer,
    })

    logger.info("agent_response_sent", user_id=user_id, response=response.answer)

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