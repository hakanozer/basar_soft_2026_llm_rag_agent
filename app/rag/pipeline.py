from dataclasses import dataclass, field

from qdrant_client import qdrant_client

from app.db.models import ProductDBModel
from app.db.session import AsyncSessionLocal, get_product_by_id
from app.llm.intent_detector import intent_detector, ollama_client
from app.rag.qdrantClient import QdrantClientWrapper
from app.schemas.intent import IntentResult


@dataclass
class RAGResponse:
    """RAG pipeline yanıtı."""
    answer: str
    intent: IntentResult
    products: list[ProductDBModel]
    total_found: int
    
RAG_SYSTEM_PROMPT = """Kullanıcıya Türkçe yanıt ver, Sen AI Commerce Assistant'sın. Bir e-ticaret platformunun akıllı asistanısın.
Sana kullanıcının sorusu ve veritabanından bulunan ürün bilgileri verilecek.
Kullanıcıya nazik, samimi ve bilgilendirici bir dilde yanıt ver.
Öneri yaparken neden bu ürünü önerdiğini açıkla.
Fiyat avantajı varsa vurgula. Ürünün eksiklerini de dürüstçe belirt.
Yanıtı 3-4 paragraf ile sınırla."""    
    
class RAGPipeline:
    
    async def run(
        self,
        query: str,
        top_k: int = 5,
    ) -> RAGResponse:
        """RAG pipeline'ını çalıştırır."""
        
        # Adım 1: Intent detection
        intent_result = await intent_detector.detect(query)
        
        # 2. Retrieval - QDrant üzerinden benzer ürünleri getir
        qdrantWrap = QdrantClientWrapper()
        retrieved_products = qdrantWrap.search(
            query_text=query,
            top_k=top_k,
            score_threshold=0.3,
        )
        
        # 3. postgresql üzerinden ürün detaylarını çek (opsiyonel, eğer QDrant'taki veriler yeterli değilse)
        products: list[ProductDBModel] = []
        for prod in retrieved_products:
            db_prod = await get_product_by_id(int(prod["id"]))
            if db_prod:
                products.append(db_prod)
        
        # Adım 4: LLM ile yanıt üretimi
        answer = await self._generate_answer(
            query=query,
            products=products,
            intent=intent_result,
        )
        
        # Yanıtı RAGResponse formatında döndür
        return RAGResponse(
            answer=answer,
            intent=intent_result,
            products=products,
            total_found=len(retrieved_products),
        )
        
    async def _generate_answer(
        self,
        query: str,
        products: list[ProductDBModel],
        intent: IntentResult,
    ) -> str:
        """Bulunan ürünleri kullanarak LLM ile doğal dil yanıtı üretir."""
        if not products:
            return (
                "Üzgünüm, arama kriterlerinize uygun ürün bulunamadı. "
                "Filtreleri genişleterek tekrar deneyebilirsiniz."
            )

        # Ürün bilgilerini prompt'a ekle
        products_context = "\n\n".join(
            [
                f"Ürün: {prod.name}\n"
                f"Marka: {prod.brand} | Kategori: {prod.category}\n"
                f"Fiyat: {prod.price} TL\n"
                f"Özellikler: {prod.features}\n"
                f"Sezon: {prod.season or 'Genel'} | Renk: {prod.color or '-'}\n"
                f"Rating: {prod.rating}/5 ({prod.review_count} yorum)\n"
            for prod in products]
        )

        user_message = (
            f"Kullanıcı sorusu: {query}\n\n"
            f"Veritabanında bulunan ürünler:\n{products_context}\n\n"
            f"Bu ürünleri değerlendirerek kullanıcıya öneri sun:"
        )

        answer = await ollama_client.chat(
            messages=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,
        )
        return answer
    

    
# Singleton
rag_pipeline = RAGPipeline()    