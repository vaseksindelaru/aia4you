# main.py
from fastapi import FastAPI
from apis.routes.clusterRoute import router as cluster_router
from apis.routes.detect_candleRoute import router as detect_candle_router
from apis.routes.detect_reboundRoute import router as detect_rebound_router
from apis.routes.gbRoute import router as gb_router
from apis.routes.vwapRoute import router as vwap_router
from apis.routes.gridCandleReboundRoute import router as gridCandleRebound_router

app = FastAPI()

app.include_router(vwap_router)
app.include_router(detect_candle_router)
app.include_router(detect_rebound_router)
app.include_router(gb_router)
app.include_router(cluster_router)
app.include_router(gridCandleRebound_router)