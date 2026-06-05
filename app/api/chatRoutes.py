# fastapi ile API rotaları tanımlamak için kullanılan bir modül
import logging  # Uygulama loglama
from typing import Optional

from dataclasses import asdict

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from app.core.cache import cache
import app.rag.pipeline as rag_pipeline

from dataclasses import asdict, is_dataclass
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

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
    
    # Cache kontrolü
    cache_key = f"{prompt or (request.prompt if request else '')}"
    cached = await cache.get("chat_query", cache_key)
    if cached:
        logger.info("Cache HIT: %s", (prompt or (request.prompt if request else ''))[:40])
        # Cached response'u RAGResponse'a dönüştür
        return cached  # dict olarak döner
    
    resolved_prompt = prompt or (request.prompt if request else None)

    if not resolved_prompt:
        raise HTTPException(status_code=422, detail="prompt alanı zorunludur")

    rag_query = await rag_pipeline.rag_pipeline.run(resolved_prompt)

    print("Redis Cache Yazma")
    # Sonucu cache'e kaydet (1 saat TTL)
    await cache.set("chat_query", cache_key, serialize(rag_query), ttl=3600)
    
    return rag_query


def serialize(obj):
    # Pydantic v2
    if isinstance(obj, BaseModel):
        return obj.model_dump()

    # Dataclass
    if is_dataclass(obj):
        return {k: serialize(v) for k, v in asdict(obj).items()}

    # SQLAlchemy model
    if hasattr(obj, "__table__"):
        return {
            c.name: serialize(getattr(obj, c.name))
            for c in obj.__table__.columns
        }

    # list
    if isinstance(obj, list):
        return [serialize(i) for i in obj]

    # dict
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}

    # primitive
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    return str(obj)