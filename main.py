# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import importlib.util
import os

# Importar indicadores
from apis.indicators import router as indicators_router

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir solo el router de indicadores que sabemos que existe
app.include_router(indicators_router, prefix="/indicators")