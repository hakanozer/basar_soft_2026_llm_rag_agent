# 1. QDrant Client Configuration env dosyasından alınarak yapılandırılır.
# 2. QDrantClient sınıfı, QDrant ile etkileşimim kurmak için gerekli yöntemleri içerir.
# 3. QDrantClient, ürün verilerini eklemek, sorgulamak ve yönetmek için kullanılacak.
# 4. clean_products.csv dosyasındaki ürün verileri, QDrant'a eklenerek vektör tabanlı arama için kullanılacak.

import os
import sys

import logging  # Uygulama loglama

logger = logging.getLogger(__name__)

try:
    from app.core.config import config
except ModuleNotFoundError:
    # Allows direct execution: python app/rag/qdrantClient.py
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app.core.config import config
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
import requests
import pandas as pd


class QdrantClientWrapper:
    
    def __init__(self):
        self.qDrantClient = QdrantClient(
            url=config.QDRAND_URL,
            port=config.QDRAND_PORT
        )
        self.collection_name = config.QDRAND_COLLECTION
        
    def create_collection(self):
        # QDrant koleksiyonu oluşturma
        if not self.qDrantClient.collection_exists(self.collection_name):
            self.qDrantClient.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768,  # Embedding boyutu (örneğin, sentence-transformers için 768)
                    distance=Distance.COSINE  # Benzerlik ölçütü
                )
            )    
        
    def get_embedding(self, text):
        # Burada embedding alma işlemi yapılır .env dosyası içindeki EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": config.EMBEDDING_MODEL,
                "prompt": text
            }
        )

        # Newer Ollama versions expose /api/embed instead of /api/embeddings.
        if response.status_code == 404:
            response = requests.post(
                f"{config.OLLAMA_BASE_URL}/api/embed",
                json={
                    "model": config.EMBEDDING_MODEL,
                    "input": text
                }
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"Ollama embedding request failed: {response.text}") from exc
        data = response.json()

        # Compatible with different Ollama response shapes.
        if "embedding" in data:
            return data["embedding"]
        if "embeddings" in data and data["embeddings"]:
            return data["embeddings"][0]

        raise ValueError(f"Unexpected embedding response: {data}")

    def load_products_from_csv(self, csv_file: str = "data/processed/clean_products.csv"):
        # CSV dosyasından ürün verilerini okuyarak QDrant'a ekleme
        df = pd.read_csv(csv_file)

        required_columns = {"id", "name", "description", "price"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise ValueError(f"CSV required columns are missing: {sorted(missing_columns)}")

        # başlangıç zamanı
        startTime = pd.Timestamp.now()
        for _, row in df.iterrows():
            raw_id = row["id"]
            
            metadata = {
                "name": row["name"],
                "description": row["description"],
                "price": row["price"]
            }
            embedding = self.get_embedding(f"{metadata['name']} {metadata['description']}")
            self.add_product(raw_id, embedding, metadata)

        # bitiş zamanı
        endTime = pd.Timestamp.now()
        print(f"Products loaded in: {endTime - startTime}")

    def add_product(self, product_id, embedding, metadata):
        # Ürün verisini QDrant'a ekleme
        self.qDrantClient.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=product_id,
                    vector=embedding,
                    payload=metadata
                )
            ]
        )

    def search(self, query_text: str, top_k: int = 5, score_threshold: float = 0.3):
        # Get query embedding and convert to plain Python list (Qdrant expects JSON-serializable vectors)
        query_vector = self.get_embedding(query_text)
        try:
            qvec = query_vector.tolist()
        except Exception:
            # if it's already a list
            qvec = list(query_vector)
        hits = self.qDrantClient.search(
            collection_name=self.collection_name,
            query_vector=qvec,
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold,
        )
        results = []
        for hit in hits:
            meta = hit.payload.copy() if hit.payload is not None else {}
            # normalize types
            if "price" in meta:
                try:
                    meta["price"] = float(meta["price"])
                except Exception:
                    pass

            meta["score"] = float(hit.score)
            meta["id"] = hit.id
            meta["product_id"] = str(hit.id)
            results.append(meta)  
        return results
    
    
    # main
if __name__ == "__main__":
    """QDrantClient sınıfını test etmek için doğrudan çalıştırılabilir."""
    qdrant_client = QdrantClientWrapper()
    # qdrant_client.create_collection()
    # qdrant_client.load_products_from_csv()
    #list = qdrant_client.search("sağlam dağcılık için spor ayakkabı")
    #for item in list:
    # print(item)