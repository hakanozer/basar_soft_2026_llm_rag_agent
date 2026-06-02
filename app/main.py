# routes.py içindeki API rotalarını ana uygulamaya dahil etmek için kullanılan modül
from fastapi import FastAPI
from .api.routes import router

app = FastAPI()

# api bağlantılarına api/v1 prefix'i eklemek için router'ı uygulamaya dahil ediyoruz
app.include_router(router, prefix="/api/v1")