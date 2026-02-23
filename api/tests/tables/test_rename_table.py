import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# テスト用定数
_OLD_TABLE = "OldTable"
_NEW_TABLE = "NewTable"
_BASE_PAYLOAD = {"oldTableName": _OLD_TABLE, "newTableName": _NEW_TABLE}


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
    manager.store_table(_OLD_TABLE, df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------


def test_rename_table_success(client, tables_store):
    """正常系: テーブル名を変更できる"""
    response = client.post(
        "/api/table/rename",
        json=_BASE_PAYLOAD,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    table_info = tables_store.get_table(_NEW_TABLE)
    assert table_info.table_name == _NEW_TABLE
    assert _OLD_TABLE not in tables_store.get_table_name_list()
    df = table_info.table
    assert df["A"].to_list() == [1, 2]
    assert df["B"].to_list() == [3, 4]


# ---------------------------------------------------------------------------
# 異常系（サービス層）
# ---------------------------------------------------------------------------


def test_rename_table_not_found(client, tables_store):
    """異常系: 存在しないテーブル名を指定した場合"""
    payload = {"oldTableName": "NotExist", "newTableName": "AnyName"}
    response = client.post(
        "/api/table/rename",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        "oldTableName 'NotExist'は存在しません。" == response_data["message"]
    )


# ---------------------------------------------------------------------------
# Pydanticバリデーションテスト (422)
# ---------------------------------------------------------------------------


def test_rename_table_empty_old_table_name(client, tables_store):
    """
    oldTableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {"oldTableName": "", "newTableName": _NEW_TABLE}
    response = client.post(
        "/api/table/rename",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "oldTableNameは1文字以上で入力してください。"
        == response_data["message"]
    )
    assert ["oldTableNameは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_rename_table_empty_new_table_name(client, tables_store):
    """
    newTableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {"oldTableName": _OLD_TABLE, "newTableName": ""}
    response = client.post(
        "/api/table/rename",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "newTableNameは1文字以上で入力してください。"
        == response_data["message"]
    )
    assert ["newTableNameは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_rename_table_missing_old_table_name(client, tables_store):
    """
    oldTableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {"newTableName": _NEW_TABLE}
    response = client.post(
        "/api/table/rename",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "oldTableNameは必須項目です。" == response_data["message"]
    assert ["oldTableNameは必須項目です。"] == response_data["details"]


def test_rename_table_missing_new_table_name(client, tables_store):
    """
    newTableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {"oldTableName": _OLD_TABLE}
    response = client.post(
        "/api/table/rename",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "newTableNameは必須項目です。" == response_data["message"]
    assert ["newTableNameは必須項目です。"] == response_data["details"]
