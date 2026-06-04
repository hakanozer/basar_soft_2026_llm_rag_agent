# fastapi ile API rotaları tanımlamak için kullanılan bir modül
from fastapi import APIRouter, HTTPException, Request
import httpx
from pydantic import BaseModel
import app.rag.pipeline as rag_pipeline

from app.llm.intent_detector import intent_detector
from app.llm.ollama_client import ollama_client

# Request ve Response Şemaları
class ChatRequest(BaseModel):
    prompt: str


chatRoutes = APIRouter()

# chat endpoint'i, Ollama API'sine istek yaparak yanıt döndürüyor
# chat içerisine { "prompt": "Fenerbahçe ne zaman şampiyon olur" } şeklinde bir json datası geliyor.
@chatRoutes.get("/chat")
async def chat(request: ChatRequest):
    rag_query = await rag_pipeline.rag_pipeline.run(request.prompt)
    return rag_query