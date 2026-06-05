# "product_search | price_compare | stock_check | product_detail | recommendation | general_question" tools üyerlerini oluşturuyor.

from langchain_community.tools import tool

from app.db.session import get_product_by_id
from app.rag.qdrantClient import QdrantClientWrapper


@tool
def product_search(query: str) -> str:
    """Kullanıcının istediği ürünleri arar ve listeler."""
    print(f"Product search query: {query}")
    # QDrant üzerinden benzer ürünleri getir
    qdrantWrap = QdrantClientWrapper()
    retrieved_products = qdrantWrap.search(
        query_text=query,
        top_k=5,
        score_threshold=0.3,
    )
    if not retrieved_products:
        return "Üzgünüm, arama kriterlerinize uygun ürün bulunamadı. Filtreleri genişleterek tekrar deneyebilirsiniz."
    
    # Ürün bilgilerini formatla
    response = "Arama sonuçları:\n\n"
    for prod in retrieved_products:
        response += (
            f"Ürün: {prod['name']}\n"
            f"Detay: {prod['description']}\n"
            f"Fiyat: {prod['price']} TL\n"
            f"---\n"
        )
    return response


@tool
def price_compare(query: str) -> str:
    """Kullanıcının istediği ürünlerin fiyat karşılaştırmasını yapar."""
    print(f"Price compare query: {query}")
    # QDrant üzerinden benzer ürünleri getir
    qdrantWrap = QdrantClientWrapper()
    retrieved_products = qdrantWrap.search(
        query_text=query,
        top_k=5,
        score_threshold=0.3,
    )
    if not retrieved_products:
        return "Üzgünüm, arama kriterlerinize uygun ürün bulunamadı. Filtreleri genişleterek tekrar deneyebilirsiniz."
    
    # Fiyat karşılaştırması yap
    response = "Fiyat karşılaştırması:\n\n"
    for prod in retrieved_products:
        response += (
            f"Ürün: {prod['name']}\n"
            f"Fiyat: {prod['price']} TL\n"
            f"---\n"
        )
    return response

@tool
def stock_check(query: str) -> str:
    """Kullanıcının istediği ürünlerin stok durumunu kontrol eder."""
    print(f"Stock check query: {query}")
    # QDrant üzerinden benzer ürünleri getir
    qdrantWrap = QdrantClientWrapper()
    retrieved_products = qdrantWrap.search(
        query_text=query,
        top_k=5,
        score_threshold=0.3,
    )
    if not retrieved_products:
        return "Üzgünüm, arama kriterlerinize uygun ürün bulunamadı. Filtreleri genişleterek tekrar deneyebilirsiniz."
    
    # Stok durumunu kontrol et
    response = "Stok durumu:\n\n"
    for prod in retrieved_products:
        stock_status = "Stokta var" if prod.get("stock_quantity", 0) > 0 else "Stokta yok"
        response += (
            f"Ürün: {prod['name']}\n"
            f"Stok Durumu: {stock_status}\n"
            f"---\n"
        )
    return response

@tool
async def product_detail(query: str) -> str:
    """Kullanıcının istediği ürünlerin detaylarını gösterir."""
    print(f"Product detail query: {query}")
    # QDrant üzerinden benzer ürünleri getir
    qdrantWrap = QdrantClientWrapper()
    retrieved_products = qdrantWrap.search(
        query_text=query,
        top_k=5,
        score_threshold=0.3,
    )
    if not retrieved_products:
        return "Üzgünüm, arama kriterlerinize uygun ürün bulunamadı. Filtreleri genişleterek tekrar deneyebilirsiniz."
    
    # Ürün detaylarını göster
    response = "Ürün detayları:\n\n"
    for prod in retrieved_products:
        proDB = await get_product_by_id(prod["id"])
        print(f"Product detail - DB query result for ID {prod['id']}: name = {proDB.name}")
        if proDB is None:
            continue
        response += (
            f"Ürün ID: {proDB.id}\n"
            f"Ürün Adı: {proDB.name}\n"
            f"Marka: {proDB.brand}\n"
            f"Kategori: {proDB.category}\n"
            f"Açıklama: {proDB.description}\n"
            f"Fiyat: {proDB.price} TL\n"
            f"Orijinal Fiyat: {proDB.original_price} TL\n"
            f"Stok Miktarı: {proDB.stock_quantity}\n"
            f"Cinsiyet: {proDB.gender}\n"
            f"Sezon: {proDB.season}\n"
            f"Renk: {proDB.color}\n"
            f"Bedenler: {proDB.sizes}\n"
            f"Özellikler: {proDB.features}\n"
            f"Puan: {proDB.rating}\n"
            f"Yorum Sayısı: {proDB.review_count}\n"
            f"Aktif Mi: {'Evet' if proDB.is_active else 'Hayır'}\n"
            f"İndirim Oranı: {proDB.discount_rate}%\n"
            f"---\n"
        )
    return response




# Tüm araçlar listesi (agent'a verilecek)
ALL_TOOLS = [product_search, price_compare, stock_check, product_detail]