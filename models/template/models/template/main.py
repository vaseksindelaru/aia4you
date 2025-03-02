# main.py
from fastapi import FastAPI
from models.template.routes.clusterRoute import router as cluster_router
from models.template.routes.detect_candleRoute import router as detect_candle_router
from models.template.routes.detect_reboundRoute import router as detect_rebound_router
from models.template.routes.gbRoute import router as gb_router
from models.template.routes.vwapRoute import router as vwap_router

app = FastAPI()

app.include_router(vwap_router)
app.include_router(detect_candle_router)
app.include_router(detect_rebound_router)
app.include_router(gb_router)
app.include_router(cluster_router)