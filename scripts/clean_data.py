# data/raw/products.csv okur ve temizler, ardından data/processed/clean_products.csv olarak kaydeder.
import locale

import pandas as pd
import numpy as np
import json
import pathlib
from difflib import SequenceMatcher

# bu programda tarih ve saat türkçe dile uygun olmalıdır.
locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")

def load_raw(path: str = "data/raw/products.csv") -> pd.DataFrame:
    """Veri setini yükler."""
    return pd.read_csv(path, encoding="utf-8")


# Kapsamlı eksik değer raporu
def eksik_raporu(df):
    eksik = df.isnull().sum()
    eksik_oran = df.isnull().mean() * 100
    rapor = pd.DataFrame({
        "Eksik Sayı": eksik,
        "Oran (%)":   eksik_oran.round(2),
        "Veri Tipi":  df.dtypes
    })
    return rapor[rapor["Eksik Sayı"] > 0].sort_values("Oran (%)", ascending=False)


def benzer_gender(gender, gender_list):
    skorlar = [
        SequenceMatcher(None, gender.lower(), g.lower()).ratio()
        for g in gender_list
    ]
    en_benzeyen = gender_list[skorlar.index(max(skorlar))]
    return en_benzeyen

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Veri setini temizler."""
    
    # price değeri olmayanları kaldır
    # df = df.dropna(subset=["price"])
    
    # price değeri olmayanları categorisine göre price ortalaması ile doldur
    df["price"] = df.groupby("category")["price"].transform(lambda x: x.fillna(x.mean()))
    
    # price değeri 0 olanları kategorisine göre price ortalaması ile doldur
    df["price"] = df.groupby("category")["price"].transform(lambda x: x.replace(0, x.mean()))
    
    # price değeri 0 dan küçük olanları pozitif yap
    df["price"] = df["price"].apply(lambda x: abs(x) if x < 0 else x)
    
    # price değeri ondalıklı değerleri virgülden sonra 2 basamak olacak şekilde yuvarla
    df["price"] = df["price"].round(2)
    
    # id, gender,name,description,stock_quantity,stock_quantity,review_count, rating  değeri olmayanları kaldır
    df = df.dropna(subset=["id", "gender", "name", "description", "stock_quantity", "review_count", "rating"])
    
    # id değeri tekrarlayanları kaldır
    df = df.drop_duplicates(subset=["id"])
    
    # name değerleri tekrarlayanları kaldır
    df = df.drop_duplicates(subset=["name"])
    
    # gender değerinde ekek olanları erkek
    # df["gender"] = df["gender"].replace("ekek", "erkek")
    gender_arr = ["erkek", "kadın", "unisex"]
    # er, erk, kek, rkek
    df["gender"] = df["gender"].apply(lambda x: benzer_gender(x, gender_arr))
    
    # name ve description sütunlarında baş ve sondaki boşlukları kaldır
    df["name"] = df["name"].str.strip()
    df["description"] = df["description"].str.strip()
    
    # name sutununda tüm harfleri küçük yap her kelimenin baş harfini büyük yap
    df["name"] = df["name"].str.title()
    
    # stock_quantity değeri negatif olanları pozitif yap
    df["stock_quantity"] = df["stock_quantity"].apply(lambda x: abs(x) if x < 0 else x)
    # stock_quantity ondalıklı değer olanları tam sayıya çevir
    df["stock_quantity"] = df["stock_quantity"].apply(lambda x: int(x) if isinstance(x, float) else x)
    
    # iskonto oranı ekleyelim, price ve original_price sütunları varsa
    if "price" in df.columns and "original_price" in df.columns:
        df["discount_rate"] = ((df["original_price"] - df["price"]) / df["original_price"]) * 100
        df["discount_rate"] = df["discount_rate"].round(2)
    
    
    # original_price < price kontrolü
    df.loc[df["original_price"] < df["price"], "original_price"] = df["price"]
    
    # Rating'in 1-5 aralığında olması gerekir.
    df.loc[df["rating"] < 1, "rating"] = 1
    df.loc[df["rating"] > 5, "rating"] = 5
    # Rating değerlerinin hepsini tam sayı yap
    df["rating"] = df["rating"].apply(lambda x: int(x) if isinstance(x, float) else x)
    
    # json formatında olan sizes ve features sütunlarını json.loads ile dict formatına çevir
    df["sizes"] = df["sizes"].apply(json.loads)
    df["features"] = df["features"].apply(json.loads)
    
    eksik_raporu_df = eksik_raporu(df)
    print("Eksik Değer Raporu:\n", eksik_raporu_df)
    return df


# main fonksiyonu
if __name__ == "__main__":
    # ham veriyi yükle
    raw_df = load_raw()
    
    # veriyi temizle
    clean_df = clean_products(raw_df)
    
    # temizlenmiş veriyi kaydet
    pathlib.Path("data/processed").mkdir(parents=True, exist_ok=True)
    clean_df.to_csv("data/processed/clean_products.csv", index=False, encoding="utf-8")

