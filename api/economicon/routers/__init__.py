from fastapi import APIRouter, Depends

from economicon.core.auth import verify_token
from economicon.routers import (
    columns,
    data_io,
    regressions,
    settings,
    statistics,
    tables,
)

# verify_token を全エンドポイントの依存関係として一括適用する。
# 個別のルーターに都度 dependencies を指定する必要がなくなる。
api_router = APIRouter(dependencies=[Depends(verify_token)])

api_router.include_router(columns.router)
api_router.include_router(tables.router)
api_router.include_router(regressions.router)
api_router.include_router(data_io.router)
api_router.include_router(statistics.router)
api_router.include_router(settings.router)
