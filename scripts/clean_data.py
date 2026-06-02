# data/raw/products.csv okur ve temizler, ardından data/processed/clean_products.csv olarak kaydeder.
import locale

import pandas as pd
import numpy as np
import json
import pathlib

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

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Veri setini temizler."""
    
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

