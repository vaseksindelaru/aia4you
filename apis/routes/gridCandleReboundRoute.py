#gridCandleReboundRoute.py
from fastapi import APIRouter
from pydantic import BaseModel
from apis.gridCandleRebound import grid_search

router = APIRouter()

class GridRequest(BaseModel):
    data: list
    volume_windows: list
    height_windows: list

@router.post("/evaluation/grid-search")
def eval_grid(request: GridRequest):
    return grid_search(request.data, request.volume_windows, request.height_windows)