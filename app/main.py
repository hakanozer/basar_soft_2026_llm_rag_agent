# routes.py içindeki API rotalarını ana uygulamaya dahil etmek için kullanılan modül
from fastapi import FastAPI

from .api.agentRoutes import agentRoutes
from .api.chatRoutes import chatRoutes

app = FastAPI()

# api bağlantılarına api/v1 prefix'i eklemek için router'ı uygulamaya dahil ediyoruz
app.include_router(chatRoutes, prefix="/api/v1")
app.include_router(agentRoutes, prefix="/api/v1")