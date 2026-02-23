import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ─────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────
_TABLE1_NAME = "TestTable1"
_TABLE2_NAME = "TestTable2"


# ─────────────────────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    manager.store_table(_TABLE1_NAME, pl.DataFrame({"A": [1, 2], "B": [3, 4]}))
    manager.store_table(_TABLE2_NAME, pl.DataFrame({"C": [1, 2], "D": [3, 4]}))
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────────────────────
def test_delete_table_success(client, tables_store):
    """テーブルを正常に削除できる"""
    response = client.post(
        "/api/table/delete", json={"tableName": _TABLE2_NAME}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert _TABLE2_NAME not in tables_store.get_table_name_list()
    assert len(tables_store.get_table_name_list()) == 1


# ─────────────────────────────────────────────────────────────
# 異常系 400：存在しないテーブル名
# ─────────────────────────────────────────────────────────────
def test_delete_table_not_found(client, tables_store):
    """存在しないテーブル名を指定すると 400 DATA_NOT_FOUND"""
    response = client.post(
        "/api/table/delete", json={"tableName": "NotExistTable"}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"] == "tableName 'NotExistTable'は存在しません。"
    )
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（空・欠損）
# ─────────────────────────────────────────────────────────────
def test_delete_table_pydantic_empty_table_name(client, tables_store):
    """tableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    response = client.post("/api/table/delete", json={"tableName": ""})
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


def test_delete_table_pydantic_missing_table_name(client, tables_store):
    """tableNameが欠損している場合は 422 VALIDATION_ERROR"""
    response = client.post("/api/table/delete", json={})
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "tableNameは必須項目です。"
    assert response_data["details"] == ["tableNameは必須項目です。"]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N4）
# ─────────────────────────────────────────────────────────────
def test_n1_delete_table_japanese_name(client, tables_store):
    """N1: 日本語テーブル名でも正常削除できる"""
    manager = tables_store
    manager.store_table("日本語テーブル", pl.DataFrame({"x": [1]}))
    response = client.post(
        "/api/table/delete", json={"tableName": "日本語テーブル"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n2_delete_table_with_surrounding_spaces(client, tables_store):
    """N2: 前後スペースはトリムされ正常削除できる"""
    response = client.post(
        "/api/table/delete", json={"tableName": f"  {_TABLE1_NAME}  "}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"
    assert _TABLE1_NAME not in tables_store.get_table_name_list()


def test_n3_delete_table_only_spaces(client, tables_store):
    """N3: スペースのみはトリム後に空になり 422 VALIDATION_ERROR"""
    response = client.post("/api/table/delete", json={"tableName": "   "})
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


def test_n4_delete_nonexistent_after_delete(client, tables_store):
    """N4: 同じテーブルを2度削除すると2度目は 400 DATA_NOT_FOUND"""
    client.post("/api/table/delete", json={"tableName": _TABLE1_NAME})
    response = client.post(
        "/api/table/delete", json={"tableName": _TABLE1_NAME}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
