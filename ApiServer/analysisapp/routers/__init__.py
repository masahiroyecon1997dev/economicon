from fastapi import APIRouter
from . import columns

api_router = APIRouter()

api_router.include_router(columns.router)
