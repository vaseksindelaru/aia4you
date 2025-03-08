from fastapi import APIRouter
from pydantic import BaseModel
from apis.detect_rebound import evaluar_rebote

router = APIRouter()

class ReboundRequest(BaseModel):
    data: list
    index: int

@router.post("/evaluation/rebound")
def eval_rebound(request: ReboundRequest):
    result = evaluar_rebote(request.data, request.index)
    return {"result": result}