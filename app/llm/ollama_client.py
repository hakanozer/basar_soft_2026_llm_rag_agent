"""
Ollama REST API istemcisi.
Async HTTP ile Ollama'ya istek atar, hata yönetimi yapar.
"""

from __future__ import annotations
from app.core.config import config

import json  # JSON okuma/yazma işlemleri
import httpx  # Asenkron HTTP istemcisi

class OllamaClient:
    
    def __init__(self, base_url: str = config.OLLAMA_BASE_URL, model: str = config.OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self,prompt: str, system: str | None = None,temperature: float = 0.7,stream: bool = False) -> str:
        url = f"{self.base_url}/api/generate"
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": 512,    # Maksimum üretilecek token sayısı
                "top_p": 0.9,
                "top_k": 40,
            },
        }

        if system:
            payload["system"] = system

        response = await self.client.post(url,json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "")
    
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> str:
        """
        Ollama /api/chat endpoint'ine istek atar.
        Çok turlu konuşmalar için kullanın.

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
            temperature: Yanıt yaratıcılığı

        Returns:
            Asistan yanıtı
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("message", {}).get("content", "")


    async def is_available(self) -> bool:
        """Ollama servisinin çalışıp çalışmadığını kontrol eder."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/tags",
                timeout=3.0,
            )
            return response.status_code == 200
        except Exception:
            return False


    async def close(self) -> None:
        """HTTP istemcisini kapat (lifespan sonunda çağır)."""
        await self.client.aclose()


ollama_client = OllamaClient()    