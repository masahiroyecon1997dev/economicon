"""
fetch_plot_data APIのテスト
"""

import io

import polars as pl
import pyarrow as pa
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ─────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────
_TABLE_NAME = "test_table"

_SOURCE_DF = pl.DataFrame(
    {
        "col_int": [1, 2, 3, 4, 5],
        "col_float": [1.1, 2.2, 3.3, 4.4, 5.5],
        "col_str": ["a", "b", "c", "d", "e"],
    }
)

_BASE_PAYLOAD: dict = {
    "tableName": _TABLE_NAME,
    "columnNames": ["col_int", "col_float"],
}


# ─────────────────────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def tables_store():
    store = TablesStore()
    store.clear_tables()
    store.store_table(_TABLE_NAME, _SOURCE_DF)
    yield store
    store.clear_tables()


# ─────────────────────────────────────────────────────────────
# ヘルパー
# ─────────────────────────────────────────────────────────────
def _decode_arrow_table(response) -> pa.Table:
    assert response.status_code == status.HTTP_200_OK
    return pa.ipc.open_file(io.BytesIO(response.content)).read_all()


def _get_schema_meta(response) -> dict:
    table = _decode_arrow_table(response)
    raw = table.schema.metadata or {}
    return {k.decode(): v.decode() for k, v in raw.items()}


# ─────────────────────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────────────────────
def test_fetch_plot_data_success(client, tables_store):
    """正常系: 指定列のみ Arrow 形式で取得できる"""
    response = client.post("/api/table/fetch-plot-data", json=_BASE_PAYLOAD)
    assert response.status_code == status.HTTP_200_OK
    assert (
        "application/vnd.apache.arrow.stream"
        in response.headers["content-type"]
    )

    arrow_table = _decode_arrow_table(response)
    assert arrow_table.num_columns == 2
    assert arrow_table.num_rows == len(_SOURCE_DF)
    assert set(arrow_table.column_names) == {"col_int", "col_float"}


def test_fetch_plot_data_metadata(client, tables_store):
    """正常系: スキーマメタデータに tableName / columnNames / totalRows が含まれる"""
    response = client.post("/api/table/fetch-plot-data", json=_BASE_PAYLOAD)
    meta = _get_schema_meta(response)

    assert meta["tableName"] == _TABLE_NAME
    assert meta["totalRows"] == str(len(_SOURCE_DF))
    assert set(meta["columnNames"].split(",")) == {"col_int", "col_float"}


def test_fetch_plot_data_single_column(client, tables_store):
    """正常系: 1列のみ取得"""
    payload = {**_BASE_PAYLOAD, "columnNames": ["col_str"]}
    response = client.post("/api/table/fetch-plot-data", json=payload)
    assert response.status_code == status.HTTP_200_OK

    arrow_table = _decode_arrow_table(response)
    assert arrow_table.num_columns == 1
    assert arrow_table.column_names == ["col_str"]


def test_fetch_plot_data_deduplication(client, tables_store):
    """正常系: 重複した列名は除去される"""
    payload = {
        **_BASE_PAYLOAD,
        "columnNames": ["col_int", "col_int", "col_float"],
    }
    response = client.post("/api/table/fetch-plot-data", json=payload)
    assert response.status_code == status.HTTP_200_OK

    arrow_table = _decode_arrow_table(response)
    assert arrow_table.num_columns == 2


# ─────────────────────────────────────────────────────────────
# 異常系: バリデーションエラー (400)
# ─────────────────────────────────────────────────────────────
def test_fetch_plot_data_table_not_found(client, tables_store):
    """異常系: 存在しないテーブル名 → 400"""
    payload = {**_BASE_PAYLOAD, "tableName": "no_such_table"}
    response = client.post("/api/table/fetch-plot-data", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_fetch_plot_data_column_not_found(client, tables_store):
    """異常系: 存在しない列名 → 400"""
    payload = {**_BASE_PAYLOAD, "columnNames": ["col_int", "no_such_col"]}
    response = client.post("/api/table/fetch-plot-data", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_fetch_plot_data_empty_column_names(client, tables_store):
    """異常系: columnNames が空リスト → 422"""
    payload = {**_BASE_PAYLOAD, "columnNames": []}
    response = client.post("/api/table/fetch-plot-data", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
