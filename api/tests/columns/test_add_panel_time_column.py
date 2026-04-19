"""パネル時間カラム追加テスト"""

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ========================================
# 定数
# ========================================

_URL = "/api/column/add-panel-time"

_TABLE_NAME = "PanelTable"
_ID_COL = "entity_id"
_VALUE_COL = "value"
_NEW_COL = "time_id"

# テスト用の entity_id と value（2 グループ×3 行）
_ENTITY_IDS = [1, 1, 1, 2, 2, 2]
_VALUES = [10, 20, 30, 40, 50, 60]
_N_ROWS = len(_ENTITY_IDS)  # 6
_ENTITY_ID_2 = 2  # entity_id の2番目グループ


# ========================================
# フィクスチャ
# ========================================


@pytest.fixture
def client():
    """TestClient のフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """パネルデータを持つ TablesStore フィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame({_ID_COL: _ENTITY_IDS, _VALUE_COL: _VALUES}).cast(
        {_ID_COL: pl.Float64, _VALUE_COL: pl.Float64}
    )
    manager.store_table(_TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_add_panel_time_column_success(client, tables_store):
    """デフォルト (start=1, step=1) でグループ内連番が付与される"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == "OK"

    df = tables_store.get_table(_TABLE_NAME).table
    # entity_id=1 の行は time_id = [1, 2, 3]
    g1 = df.filter(pl.col(_ID_COL) == 1)[_NEW_COL].to_list()
    assert g1 == [1, 2, 3]
    # entity_id=2 の行は time_id = [1, 2, 3]
    g2 = df.filter(pl.col(_ID_COL) == _ENTITY_ID_2)[_NEW_COL].to_list()
    assert g2 == [1, 2, 3]


def test_add_panel_time_column_result_structure(client, tables_store):
    """レスポンス result に tableName と columnName が含まれる"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()["result"]
    assert result["tableName"] == _TABLE_NAME
    assert result["columnName"] == _NEW_COL


def test_add_panel_time_column_custom_start(client, tables_store):
    """startValue=2000 で 2000 始まりの連番になる"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
            "startValue": 2000,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(_TABLE_NAME).table
    g1 = df.filter(pl.col(_ID_COL) == 1)[_NEW_COL].to_list()
    assert g1 == [2000, 2001, 2002]


def test_add_panel_time_column_descending(client, tables_store):
    """step=-1 でグループ内降順連番になる"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
            "step": -1,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(_TABLE_NAME).table
    g1 = df.filter(pl.col(_ID_COL) == 1)[_NEW_COL].to_list()
    # start=1, step=-1 → [1, 0, -1]
    assert g1 == [1, 0, -1]


def test_add_panel_time_column_position(client, tables_store):
    """新しいカラムが addPositionColumn の右隣に挿入される"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(_TABLE_NAME).table
    # entity_id の右隣に time_id が来ること
    cols = df.columns
    assert cols.index(_NEW_COL) == cols.index(_ID_COL) + 1


# ========================================
# 異常系テスト（Pydantic バリデーション: 422）
# ========================================


def test_add_panel_time_column_missing_table_name(client, tables_store):
    """tableName 未指定で 422 が返る"""
    response = client.post(
        _URL,
        json={
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["code"] == ErrorCode.VALIDATION_ERROR


def test_add_panel_time_column_step_zero(client, tables_store):
    """step=0 で 422 が返り、メッセージが正しい"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
            "step": 0,
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["code"] == ErrorCode.VALIDATION_ERROR
    assert data["message"] == "step must not be 0."


def test_add_panel_time_column_missing_id_column(client, tables_store):
    """idColumn が空文字列で 422 が返る"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": "",
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["code"] == ErrorCode.VALIDATION_ERROR


# ========================================
# 異常系テスト（ビジネスロジック: 400）
# ========================================


def test_add_panel_time_column_table_not_found(client, tables_store):
    """存在しないテーブル名で 400 DATA_NOT_FOUND が返る"""
    response = client.post(
        _URL,
        json={
            "tableName": "NonExistentTable",
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == ErrorCode.DATA_NOT_FOUND
    assert data["message"] == "tableName 'NonExistentTable'は存在しません。"


def test_add_panel_time_column_id_column_not_found(client, tables_store):
    """存在しない idColumn で 400 DATA_NOT_FOUND が返る"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": "no_such_col",
            "newColumnName": _NEW_COL,
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == ErrorCode.DATA_NOT_FOUND
    assert data["message"] == "idColumn 'no_such_col'は存在しません。"


def test_add_panel_time_column_new_column_exists(client, tables_store):
    """新規カラム名に既存名を指定すると 400 DATA_ALREADY_EXISTS が返る"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _VALUE_COL,  # 既存カラム名
            "addPositionColumn": _ID_COL,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert data["message"] == (
        f"newColumnName '{_VALUE_COL}'"
        "\u306f\u65e2\u306b\u5b58\u5728\u3057\u307e\u3059\u3002"
    )


def test_add_panel_time_column_position_column_not_found(client, tables_store):
    """存在しない addPositionColumn で 400 DATA_NOT_FOUND が返る"""
    response = client.post(
        _URL,
        json={
            "tableName": _TABLE_NAME,
            "idColumn": _ID_COL,
            "newColumnName": _NEW_COL,
            "addPositionColumn": "no_position_col",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == ErrorCode.DATA_NOT_FOUND
    assert data["message"] == (
        "addPositionColumn 'no_position_col'"
        "\u306f\u5b58\u5728\u3057\u307e\u305b\u3093\u3002"
    )
