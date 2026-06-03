# fastapi ile API rotaları tanımlamak için kullanılan bir modül
from fastapi import APIRouter, HTTPException, Request
import httpx
from pydantic import BaseModel

from app.llm.intent_detector import intent_detector
from app.llm.ollama_client import ollama_client

# Request ve Response Şemaları
class ChatRequest(BaseModel):
    prompt: str


router = APIRouter()

# chat endpoint'i, Ollama API'sine istek yaparak yanıt döndürüyor
# chat içerisine { "prompt": "Fenerbahçe ne zaman şampiyon olur" } şeklinde bir json datası geliyor.
@router.get("/chat")
async def chat(request: ChatRequest):
        try:
            result = await intent_detector.detect(request.prompt)
            return result
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="LLM servisi (Ollama) çalışmıyor. 'ollama serve' komutunu çalıştırın.",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))