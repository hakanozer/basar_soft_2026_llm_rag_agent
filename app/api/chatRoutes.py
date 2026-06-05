# fastapi ile API rotaları tanımlamak için kullanılan bir modül
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

import app.rag.pipeline as rag_pipeline

# Request ve Response Şemaları
class ChatRequest(BaseModel):
    prompt: str


chatRoutes = APIRouter()

# chat endpoint'i, Ollama API'sine istek yaparak yanıt döndürüyor
# chat içerisine { "prompt": "Fenerbahçe ne zaman şampiyon olur" } şeklinde bir json datası geliyor.
@chatRoutes.get("/chat")
async def chat(
    prompt: Optional[str] = Query(default=None),
    request: Optional[ChatRequest] = Body(default=None),
):
    resolved_prompt = prompt or (request.prompt if request else None)

    if not resolved_prompt:
        raise HTTPException(status_code=422, detail="prompt alanı zorunludur")

    rag_query = await rag_pipeline.rag_pipeline.run(resolved_prompt)
    return rag_query