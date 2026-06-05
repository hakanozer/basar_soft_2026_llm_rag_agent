# planner.py
"""
Basit Intent → Tool → LLM pipeline.
ReAct agent yerine deterministik akış.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

from app.agent.tools import product_search, price_compare, stock_check, product_detail
from app.core.config import config

logger = logging.getLogger(__name__)

# 1. Intent tespiti için basit prompt
INTENT_PROMPT = PromptTemplate.from_template(
"""Kullanıcı mesajını analiz et ve SADECE aşağıdaki seçeneklerden birini yaz:

SEÇENEKLER:
- product_search   (ürün arama, listeleme)
- price_compare    (fiyat karşılaştırma)
- stock_check      (stok sorgulama)
- product_detail   (ürün detay)
- general          (genel soru, selamlama vb.)

Kullanıcı mesajı: {message}

Sadece seçenek adını yaz, başka hiçbir şey yazma:"""
)

# 2. Son cevap oluşturma promptu
ANSWER_PROMPT = PromptTemplate.from_template(
"""Sen bir e-ticaret asistanısın. Türkçe, samimi ve yardımsever cevap ver.

Kullanıcı sorusu: {user_input}

Sistem verisi:
{tool_result}

Sohbet geçmişi:
{chat_history}

Kullanıcıya yukarıdaki veriyi kullanarak kısa ve anlaşılır bir cevap ver:"""
)


@dataclass
class AgentResponse:
    answer: str
    steps: list[dict] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)


# Tool map — intent string → fonksiyon
TOOL_MAP = {
    "product_search": product_search,
    "price_compare": price_compare,
    "stock_check": stock_check,
    "product_detail": product_detail,
}


class CommerceAgent:

    def __init__(self) -> None:
        self._llm: Ollama | None = None

    def _get_llm(self) -> Ollama:
        if self._llm is None:
            self._llm = Ollama(
                base_url=config.OLLAMA_BASE_URL,
                model=config.OLLAMA_MODEL,
                temperature=0.1,
                num_predict=1024,
            )
        return self._llm

    def _detect_intent(self, message: str) -> str:
        """LLM ile intent tespiti. Hata durumunda product_search döner."""
        try:
            llm = self._get_llm()
            prompt = INTENT_PROMPT.format(message=message)
            raw = llm.invoke(prompt).strip().lower()

            # Çıktıyı güvenli parse et
            for key in TOOL_MAP:
                if key in raw:
                    return key

            if "genel" in raw or "general" in raw:
                return "general"

        except Exception as e:
            logger.warning("Intent tespiti başarısız: %s", e)

        # Fallback — kelime bazlı kural
        return self._rule_based_intent(message)

    def _rule_based_intent(self, message: str) -> str:
        """LLM başarısız olursa basit kural tabanlı intent."""
        msg = message.lower()

        if any(w in msg for w in ["fiyat", "ucuz", "pahalı", "karşılaştır", "kaç tl"]):
            return "price_compare"
        if any(w in msg for w in ["stok", "var mı", "mevcut", "tükendi"]):
            return "stock_check"
        if any(w in msg for w in ["detay", "özellik", "hakkında", "açıkla"]):
            return "product_detail"
        if any(w in msg for w in ["getir", "ara", "bul", "listele", "göster", "öneri", "öner"]):
            return "product_search"

        return "product_search"  # varsayılan

    def _run_tool(self, intent: str, message: str) -> str:
        """Tespit edilen intent'e göre tool'u çalıştırır."""
        tool_fn = TOOL_MAP.get(intent)
        if tool_fn is None:
            return ""

        try:
            # LangChain tool'ları .invoke() ile çağrılır
            return tool_fn.invoke(message)
        except Exception as e:
            logger.exception("Tool hatası (%s): %s", intent, e)
            return "Araç çalıştırılamadı."

    def _generate_answer(
        self,
        user_input: str,
        tool_result: str,
        chat_history: str,
    ) -> str:
        """Tool sonucunu LLM ile kullanıcı dostu cevaba dönüştürür."""
        try:
            llm = self._get_llm()
            prompt = ANSWER_PROMPT.format(
                user_input=user_input,
                tool_result=tool_result,
                chat_history=chat_history,
            )
            return llm.invoke(prompt).strip()
        except Exception as e:
            logger.exception("Cevap üretme hatası: %s", e)
            # LLM başarısız olursa ham tool sonucunu döndür
            return tool_result

    async def run(self, user_input: str, chat_history: str = "") -> AgentResponse:
        llm = self._get_llm()

        # 1. Intent tespit et
        intent = self._detect_intent(user_input)
        logger.info("Tespit edilen intent: %s", intent)

        # 2. Genel soru ise direkt LLM cevabı
        if intent == "general":
            try:
                answer = llm.invoke(
                    f"Kullanıcı: {user_input}\nTürkçe, kısa cevap ver:"
                ).strip()
            except Exception as e:
                logger.exception("LLM hatası: %s", e)
                answer = "Merhaba! Size nasıl yardımcı olabilirim?"

            return AgentResponse(answer=answer)

        # 3. Tool çalıştır
        tool_result = self._run_tool(intent, user_input)

        # 4. Tool sonucunu LLM ile formatla
        answer = self._generate_answer(user_input, tool_result, chat_history)

        return AgentResponse(
            answer=answer,
            steps=[{"tool": intent, "input": user_input, "output": tool_result[:300]}],
            tools_used=[intent],
        )

    def clear_memory(self) -> None:
        pass  # Memory agentRoutes'ta yönetiliyor


# Singleton
commerce_agent = CommerceAgent()