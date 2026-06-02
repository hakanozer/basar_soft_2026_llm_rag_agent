# fastapi ile API rotaları tanımlamak için kullanılan bir modül
from fastapi import APIRouter, Request
from app.core.config import config
from pydantic import BaseModel
import httpx

# Request ve Response Şemaları
class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

router = APIRouter()

# chat endpoint'i, Ollama API'sine istek yaparak yanıt döndürüyor
# chat içerisine { "prompt": "Fenerbahçe ne zaman şampiyon olur" } şeklinde bir json datası geliyor.
@router.get("/chat")
async def chat(request: ChatRequest):
    url =  f"{config.OLLAMA_BASE_URL}/api/generate"
    payload: dict = {
            "model": config.OLLAMA_MODEL,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 512,    # Maksimum üretilecek token sayısı
                "top_p": 0.9,
                "top_k": 40,
            },
        }
    payload["system"] = "Türkçe olarak, kısa ve öz bir şekilde yanıt ver."
    client = httpx.AsyncClient(timeout=120.0)
    response = await client.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return ChatResponse(response=data.get("response", ""))