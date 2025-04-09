from fastapi import APIRouter

router = APIRouter()

# Import and include routers from indicator modules
from .atr import atr_router

router.include_router(atr_router, tags=["indicators"])
