from fastapi import APIRouter
from pydantic import BaseModel
from apis.cluster import evaluate_clusters

router = APIRouter()

class ClusterRequest(BaseModel):
    data: list
    max_clusters: int = 5

@router.post("/optimize_clusters/")
def optimize_clusters_endpoint(request: ClusterRequest):
    result = evaluate_clusters(request.data, request.max_clusters)
    return result