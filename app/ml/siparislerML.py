import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

"""
siparisler_cleaned.csv dosya içeriği şu şekildedir:
siparis_id,musteri_adi,sehir,fiyat,adet,tarih,kategori,toplam_harcama
10002,Ayşe Kaya,Ankara,2222.45,7,01-01-2024 03:00:00,Elektronik,15557.15
10003,Mehmet Demir,İzmi̇r,4300.06,6,03-06-2024 04:28:30,Giyim,25800.36
10004,Fatma Şahin,Bursa,3501.97,8,01-01-2024 09:00:00,Giyim,28015.76
10005,Ahmet Yılmaz,İstanbul,516.18,2,01-01-2024 12:00:00,Ev,1032.36
"""

class siparislerMl:
    
    def __init__(self):
        """Siparişler ML sınıfı"""
        
    # data/processed/siparisler_cleaned.csv dosyasını okuyarak dataframe oluşturur
    def load_data(self) -> pd.DataFrame:
        df = pd.read_csv("data/processed/siparisler_cleaned.csv")
        return df
    
    # scikit-learn kullanarak makine öğrenmesi ile 30 gün içinde en çok harcama yapan müşterileri tahmin eden fonksiyon
    def predict_top_customers(
        self,
        df,
        top_n=10,
        random_state=42
    ):
        """
        30 gün içinde en çok harcama yapacak müşterileri tahmin eder
        (CLV - Customer Lifetime Value proxy modeli)
        """

        df = df.copy()

        # ---------------------------
        # 1. VERİ TEMİZLEME
        # ---------------------------
        df["tarih"] = pd.to_datetime(df["tarih"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["tarih"])

        # ---------------------------
        # 2. FEATURE ENGINEERING (MÜŞTERİ BAZLI)
        # ---------------------------
        reference_date = df["tarih"].max()

        customer_df = df.groupby("musteri_adi").agg({
            "toplam_harcama": ["sum", "mean"],
            "adet": ["sum", "mean"],
            "fiyat": "mean",
            "siparis_id": "count",
            "tarih": "max"
        })

        customer_df.columns = [
            "total_spent",
            "avg_spent",
            "total_qty",
            "avg_qty",
            "avg_price",
            "order_count",
            "last_order_date"
        ]

        # 🔥 KRİTİK FIX
        customer_df = customer_df.reset_index()

        # Recency (son siparişten geçen gün)
        customer_df["recency_days"] = (
            reference_date - customer_df["last_order_date"]
        ).dt.days

        customer_df = customer_df.drop("last_order_date", axis=1)

        customer_df["target_30d_spent"] = customer_df["total_spent"] * 0.3

        X = customer_df.drop(columns=[
            "target_30d_spent",
            "total_spent",
            "musteri_adi"
        ])
        y = customer_df["target_30d_spent"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state
        )
        
        model = RandomForestRegressor(
            n_estimators=200,
            random_state=random_state
        )

        model.fit(X_train, y_train)
        
        customer_df["predicted_30d_spent"] = model.predict(X)

        result = customer_df.sort_values(
            "predicted_30d_spent",
            ascending=False
        ).head(top_n)
        return result
    
    # scikit-learn kullanarak makine öğrenmesi ile Giyim kategorisinde 30 gün içinde en çok harcama yapan illeri tahmin eden fonksiyon
    def predict_top_cities(
        self,
        df,
        top_n=10,
        random_state=42
    ):
        """
        Giyim kategorisinde 30 gün içinde en çok harcama yapacak şehirleri tahmin eder
        """

        df = df.copy()

        # ---------------------------
        # 1. VERİ TEMİZLEME
        # ---------------------------
        df["tarih"] = pd.to_datetime(df["tarih"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["tarih"])

        # ---------------------------
        # 2. FEATURE ENGINEERING (ŞEHİR BAZLI)
        # ---------------------------
        reference_date = df["tarih"].max()

        city_df = df[df["kategori"] == "Giyim"].groupby("sehir").agg({
            "toplam_harcama": ["sum", "mean"],
            "adet": ["sum", "mean"],
            "fiyat": "mean",
            "siparis_id": "count",
            "tarih": "max"
        })

        city_df.columns = [
            "total_spent",
            "avg_spent",
            "total_qty",
            "avg_qty",
            "avg_price",
            "order_count",
            "last_order_date"
        ]

        city_df = city_df.reset_index()

        city_df["recency_days"] = (
            reference_date - city_df["last_order_date"]
        ).dt.days

        city_df = city_df.drop("last_order_date", axis=1)

        city_df["target_30d_spent"] = city_df["total_spent"] * 0.3

        X = city_df.drop(columns=[
            "target_30d_spent",
            "total_spent",
            "sehir"
        ])
        y = city_df["target_30d_spent"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state
        )
        
        model = RandomForestRegressor(
            n_estimators=200,
            random_state=random_state
        )

        model.fit(X_train, y_train)
        
        city_df["predicted_30d_spent"] = model.predict(X)

        result = city_df.sort_values(
            "predicted_30d_spent",
            ascending=False
        ).head(top_n)
        return result
        
        

siparisler = siparislerMl()

# main fonksiyonu
# if __name__ == "__main__":
    #print("Siparişler ML sınıfı çalıştırıldı.")
    #siparisler = siparislerMl()
    #df = siparisler.load_data()
    #predict_top_customers = siparisler.predict_top_customers(df)
    #print(predict_top_customers)