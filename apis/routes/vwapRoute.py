from fastapi import APIRouter
from pydantic import BaseModel
from apis.vwap import calculate_vwap

router = APIRouter()

class VWAPRequest(BaseModel):
    open: float
    close: float
    high: float
    low: float
    volume: float

@router.post("/calculate_vwap/")
def calc_vwap(data: list[VWAPRequest]):
    return calculate_vwap([item.model_dump() for item in data])  # Cambio de dict() a model_dump()