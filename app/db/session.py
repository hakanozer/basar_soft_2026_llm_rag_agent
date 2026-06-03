"""
SQLAlchemy async veritabanı oturumu yönetimi.
Her HTTP isteği için bağımsız oturum sağlar.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.dialects.postgresql import insert

import pandas as pd

try:
    from app.core.config import config
    from app.db.models import Base, ProductDBModel
except ModuleNotFoundError:
    # Allows direct execution: python app/db/session.py
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app.core.config import config
    from app.db.models import Base, ProductDBModel

# Senkron DATABASE_URL'i async uyumlu hale getir
# postgresql:// → postgresql+asyncpg://
ASYNC_DATABASE_URL = config.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace("postgres://", "postgresql+asyncpg://")

# Async engine oluştur
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=config.DEBUG,      # SQL sorgularını logla (sadece dev'de)
    pool_size=10,              # Bağlantı havuzu boyutu
    max_overflow=20,           # Havuz dolunca ek bağlantı sayısı
    pool_pre_ping=True,        # Bağlantı kopukluğunu otomatik tespit et
)

# Session fabrikası
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Commit sonrası attribute'lara erişimi koru
)


# data/processed/clean_products.csv dosyasındaki ürün verilerini PostgreSQL veritabanına ekleyecek fonksiyon
async def init_db_with_products():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    df = await asyncio.to_thread(
        pd.read_csv,
        "data/processed/clean_products.csv"
    )
    df = df.fillna("")
    records = df.to_dict(orient="records")

    async with AsyncSessionLocal() as session:
        try:
            stmt = insert(ProductDBModel).values(records)
            stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)
            await session.commit()

        except Exception:
            await session.rollback()
            raise
        
# id değerine göre ürün getirme fonksiyonu
async def get_product_by_id(product_id: int) -> ProductDBModel | None:
    async with AsyncSessionLocal() as session:
        result = await session.get(ProductDBModel, product_id)
        # result yanıtı kontrol ettikten sonra json formatı ile geri döndürülür
        if result:
            return result
        return None

# main
if __name__ == "__main__":
    """Veritabanını ürün verileriyle başlatmak için doğrudan çalıştırılabilir."""
    # asyncio.run(init_db_with_products())
    test_product = asyncio.run(get_product_by_id(2))
    json_result = json.dumps(test_product.__dict__, default=str, indent=4)
    print(json_result)