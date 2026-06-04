"""
AI Agent Planner — ReAct döngüsü ile çalışan ana agent.
LLM + Tools + Memory entegrasyonu.
"""
from __future__ import annotations

import logging  # Uygulama loglama
from dataclasses import dataclass, field  # Veri sınıfı tanımı için

from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms import Ollama  # Yerel LLM entegrasyonu
from langchain_core.prompts import PromptTemplate  # Prompt şablonu oluşturmak için
from langchain.memory import ConversationBufferWindowMemory

from app.agent.tools import ALL_TOOLS
from app.core.config import config

logger = logging.getLogger(__name__)

# ReAct Prompt Template
# Agent'a nasıl düşüneceğini, hangi formatı kullanacağını söyler
REACT_PROMPT = PromptTemplate.from_template(
"""Sen AI Commerce Assistant'sın.
Türkçe konuş.

Elindeki araçlar:
{tools}

Araç adları: {tool_names}

Kullanıcı sorusu:
{input}

FORMAT:

Thought: ne yapmalıyım
Action: tool adı
Action Input: tool girdisi
Observation: tool sonucu
Thought: sonuç yeterli mi?

SONLANDIRMA KURALI (ÇOK ÖNEMLİ):
- Eğer Observation kullanıcı isteğini karşılıyorsa
  → Action YAPMA
  → SADECE Final Answer yaz
- Eğer Observation içinde [FINAL_RESULT] varsa
  → DERHAL STOP
- Aynı tool’u 2. kez ardışık çağırma
- 2’den fazla Action yapma

E-Ticaret dışı sorularda:
→ tool kullanma, direkt Final Answer

Başla!

{agent_scratchpad}
"""
)


@dataclass
class AgentResponse:
    """Agent yanıt modeli."""
    answer: str
    steps: list[dict] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    
    
class CommerceAgent:
    """
    E-ticaret asistanı agent'ı.
    ReAct pattern ile çalışır, araçları kullanarak sorulara yanıt verir.
    """

    def __init__(self) -> None:
        self._executor: AgentExecutor | None = None
        self._memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
        )
        
    def _build_executor(self) -> AgentExecutor:
        """AgentExecutor'ı oluşturur."""
        llm = Ollama(
            base_url=config.OLLAMA_BASE_URL,
            model=config.OLLAMA_MODEL,
            temperature=0.1,
            num_predict=1024,
        )
        
        agent = create_react_agent(
            llm=llm,
            tools=ALL_TOOLS,
            prompt=REACT_PROMPT,
        )
        
        return AgentExecutor(
            agent=agent,
            tools=ALL_TOOLS,
            memory=self._memory,
            verbose=True,
            max_iterations=10,
            early_stopping_method="generate"
        )
        
    async def run(self, user_input: str) -> AgentResponse:
        """
        Kullanıcı girdisini agent ile işler.

        Args:
            user_input: Kullanıcının sorusu

        Returns:
            AgentResponse: Yanıt ve kullanılan araçlar
        """
        if self._executor is None:
            self._executor = self._build_executor()
            
        try:
            result = await self._executor.ainvoke({"input": user_input})
        except Exception as e:
            logger.exception("Agent hatası: %s", e)
            return AgentResponse(
                answer="Üzgünüm, isteğinizi işlerken bir hata oluştu. Lütfen tekrar deneyin.",
            )

        # Kullanılan araçları çıkar
        tools_used = []
        steps = []
        for action, observation in result.get("intermediate_steps", []):
            tools_used.append(action.tool)
            steps.append({
                "tool": action.tool,
                "input": action.tool_input,
                "output": str(observation)[:200],
            })

        return AgentResponse(
            answer=result.get("output", ""),
            steps=steps,
            tools_used=list(set(tools_used)),
        )
    
    def clear_memory(self) -> None:
        """Konuşma geçmişini temizler."""
        self._memory.clear() 
                   
# Singleton
commerce_agent = CommerceAgent()        