from fastapi import APIRouter
from . import columns, tables, regressions, data_io, statistics, operations, files, settings

api_router = APIRouter()

api_router.include_router(columns.router)
api_router.include_router(tables.router)
api_router.include_router(regressions.router)
api_router.include_router(data_io.router)
api_router.include_router(statistics.router)
api_router.include_router(operations.router)
api_router.include_router(files.router)
api_router.include_router(settings.router)
