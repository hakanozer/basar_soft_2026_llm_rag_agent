# routes.py içindeki API rotalarını ana uygulamaya dahil etmek için kullanılan modül
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import cache

from .api.agentRoutes import agentRoutes
from .api.chatRoutes import chatRoutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.connect()
    yield
    await cache.disconnect()

app = FastAPI(lifespan=lifespan)

# api bağlantılarına api/v1 prefix'i eklemek için router'ı uygulamaya dahil ediyoruz
app.include_router(chatRoutes, prefix="/api/v1")
app.include_router(agentRoutes, prefix="/api/v1")