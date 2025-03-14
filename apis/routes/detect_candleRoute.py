from fastapi import APIRouter
from pydantic import BaseModel
from apis.detect_candle import detect_candlesticks

router = APIRouter()

class CandleRequest(BaseModel):
    open: float
    close: float
    high: float
    low: float
    volume: float

@router.post("/detect_candlesticks/")
def detect_candles(data: list[CandleRequest]):
    return detect_candlesticks([item.model_dump() for item in data])  # Cambio de dict() a model_dump()