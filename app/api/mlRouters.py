from fastapi import APIRouter, HTTPException
from app.ml.siparislerML import siparisler

mlRoutes = APIRouter()


@mlRoutes.get("/ml/predict_top_customers")
async def predict_top_customers(top_n: int = 5):
    try:
        df = siparisler.load_data()
        result = siparisler.predict_top_customers(df, top_n)

        return result.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@mlRoutes.get("/ml/predict_top_cities")
async def predict_top_cities(top_n: int = 5):
    try:
        df = siparisler.load_data()
        result = siparisler.predict_top_cities(df, top_n)

        return result.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))