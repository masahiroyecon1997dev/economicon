import polars as pl
import pytest
from economicon.services.data.tables_store import TablesStore
from fastapi import status
from fastapi.testclient import TestClient
from main import app

table_name = "test_table"
# 作成するテーブルは2カラムとする
test_data = pl.DataFrame(
    {"col1": [1, 2, 3], "col2": ["a", "b", "c"], "col3": [1.1, 2.2, 3.3]}
)


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    manager.store_table(table_name, test_data)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_get_column_info_list_success(client, tables_store):
    """正常系テスト：テーブルが存在する場合"""
    response = client.post(
        "/api/column/get-list", json={"tableName": table_name}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert result["tableName"] == table_name
    # カラム名はDataFrameのスキーマ順に返ると想定
    expected_columns = [
        {"name": name, "type": str(dtype)}
        for name, dtype in test_data.schema.items()
    ]
    assert result["columnInfoList"] == expected_columns


def test_get_column_info_list_number_success(client, tables_store):
    """正常系テスト：テーブルが存在する場合（数値型の列のみ）"""
    response = client.post(
        "/api/column/get-list",
        json={"tableName": table_name, "isNumberOnly": "true"},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert result["tableName"] == table_name
    # カラム名はDataFrameのスキーマ順に返ると想定
    expected_columns = [
        {"name": name, "type": str(dtype)}
        for name, dtype in test_data.schema.items()
        if dtype.is_numeric()
    ]
    assert result["columnInfoList"] == expected_columns


def test_get_column_info_list_table_not_found(client, tables_store):
    """異常系テスト：存在しないテーブル名の場合"""
    non_existent_table_name = "non_existent_table"
    response = client.post(
        "/api/column/get-list", json={"tableName": non_existent_table_name}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # エラーメッセージにテーブル名が存在しない旨が含まれることを確認
    expected_message = "tableName 'non_existent_table'は存在しません。"
    assert expected_message == response_data["message"]


def test_get_column_info_list_exception(client, tables_store):
    """例外発生時のテスト"""
    original_method = tables_store.get_column_info_list

    def raise_exception(table_name: str) -> pl.Schema:
        raise Exception("DB error")

    tables_store.get_column_info_list = raise_exception
    response = client.post(
        "/api/column/get-list", json={"tableName": table_name}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data["code"] == "NG"
    expected_message = (
        "カラム情報リストの取得中に予期しないエラーが発生しました。"
    )
    assert expected_message == response_data["message"]
    # 後始末
    tables_store.get_column_info_list = original_method
