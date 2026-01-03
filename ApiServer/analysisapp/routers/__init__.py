from fastapi import APIRouter
from . import columns, clear_tables, confidence_interval

api_router = APIRouter()

api_router.include_router(columns.router)
api_router.include_router(clear_tables.router)
api_router.include_router(confidence_interval.router)
