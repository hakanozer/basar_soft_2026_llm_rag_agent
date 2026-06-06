# .env içindeki değişkenleri okuyarak uygulama yapılandırmasını sağlar.
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    # Veritabanı bağlantı bilgileri    
    # Application
    APP_NAME = os.getenv("APP_NAME", "AI Commerce Assistant")
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    PORT = int(os.getenv("PORT", 8000))
    
    # LLM (Ollama yerel model)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Embedding modeli (sentence-transformers)
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2")
    
    # PostgreSQL (Docker)
    POSTGRES_USER = os.getenv("POSTGRES_USER", "aicommerce")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme123")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "aicommerce_db")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aicommerce:changeme123@localhost:5432/aicommerce_db")
    
    # Cache (Redis)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    
    # ELK log forwarding (local app -> logstash)
    LOGSTASH_HOST = os.getenv("LOGSTASH_HOST", "localhost")
    LOGSTASH_PORT = int(os.getenv("LOGSTASH_PORT", 5514))
    
    # QDrand Vector DB Configuration
    QDRAND_URL = os.getenv("QDRAND_URL", "localhost")
    QDRAND_COLLECTION = os.getenv("QDRAND_COLLECTION", "products")
    QDRAND_PORT = int(os.getenv("QDRAND_PORT", 6333))
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
config = Config()    