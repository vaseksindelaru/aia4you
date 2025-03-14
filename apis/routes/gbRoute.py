from fastapi import APIRouter
from pydantic import BaseModel
from apis.gb import train_gradient_boosting

router = APIRouter()

class GBRequest(BaseModel):
    Candle_Type: str
    VWAP: float
    Rebound_Success: int

@router.post("/train_GB/")
def train_gb(data: list[GBRequest]):
    result = train_gradient_boosting([item.model_dump() for item in data])  # Cambio de dict() a model_dump()
    return {"accuracy": result["accuracy"]}  # Solo devolvemos accuracy, no el modelo