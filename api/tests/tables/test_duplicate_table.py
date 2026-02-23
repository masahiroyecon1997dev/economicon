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
_TABLE_NAME = "TestTable"
_NEW_TABLE_NAME = "DuplicatedTable"
MAX_NEW_TABLE_NAME_LENGTH = 128

_BASE_PAYLOAD: dict = {
    "tableName": _TABLE_NAME,
    "newTableName": _NEW_TABLE_NAME,
}

_SOURCE_DF = pl.DataFrame(
    {"A": [1, 2, 3], "B": [4, 5, 6], "C": ["x", "y", "z"]}
)


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
    manager.store_table(_TABLE_NAME, _SOURCE_DF)
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────────────────────
def test_duplicate_table_success(client, tables_store):
    """テーブルを正常に複製できる"""
    response = client.post("/api/table/duplicate", json=_BASE_PAYLOAD)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == _NEW_TABLE_NAME
    assert _NEW_TABLE_NAME in tables_store.get_table_name_list()
    original_df = tables_store.get_table(_TABLE_NAME).table
    duplicated_df = tables_store.get_table(_NEW_TABLE_NAME).table
    assert original_df.equals(duplicated_df)


def test_duplicate_table_success_empty_table(client, tables_store):
    """空テーブルも正常に複製できる"""
    empty_df = pl.DataFrame({"Col1": [], "Col2": []})
    tables_store.store_table("EmptyTable", empty_df)
    payload = {"tableName": "EmptyTable", "newTableName": "DuplicatedEmpty"}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "DuplicatedEmpty"
    duplicated_df = tables_store.get_table("DuplicatedEmpty").table
    assert duplicated_df.height == 0
    assert duplicated_df.columns == ["Col1", "Col2"]


# ─────────────────────────────────────────────────────────────
# 異常系 400：存在しないテーブル名 / 重複する新テーブル名
# ─────────────────────────────────────────────────────────────
def test_duplicate_table_not_found(client, tables_store):
    """存在しないtableNameを指定すると 400 DATA_NOT_FOUND"""
    payload = {**_BASE_PAYLOAD, "tableName": "NonExistentTable"}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "tableName 'NonExistentTable'は存在しません。"
    )
    assert "details" not in response_data


def test_duplicate_table_already_exists(client, tables_store):
    """既存のテーブル名をnewTableNameに指定すると 400 DATA_ALREADY_EXISTS"""
    payload = {**_BASE_PAYLOAD, "newTableName": _TABLE_NAME}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"]
        == f"newTableName '{_TABLE_NAME}'は既に存在します。"
    )
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（空・欠損）
# ─────────────────────────────────────────────────────────────
def test_duplicate_table_pydantic_empty_table_name(client, tables_store):
    """tableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": ""}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


def test_duplicate_table_pydantic_empty_new_table_name(client, tables_store):
    """newTableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "newTableName": ""}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "newTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "newTableNameは1文字以上で入力してください。"
    ]


def test_duplicate_table_pydantic_missing_table_name(client, tables_store):
    """tableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {"newTableName": _NEW_TABLE_NAME}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "tableNameは必須項目です。"
    assert response_data["details"] == ["tableNameは必須項目です。"]


def test_duplicate_table_pydantic_missing_new_table_name(client, tables_store):
    """newTableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {"tableName": _TABLE_NAME}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "newTableNameは必須項目です。"
    assert response_data["details"] == ["newTableNameは必須項目です。"]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N7）
# ─────────────────────────────────────────────────────────────
def test_n1_new_table_name_japanese(client, tables_store):
    """N1: newTableNameに日本語を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "newTableName": "日本語テーブル複製"}
    response = client.post("/api/table/duplicate", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n2_new_table_name_emoji(client, tables_store):
    """N2: newTableNameに絵文字を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "newTableName": "Table🎲Copy"}
    response = client.post("/api/table/duplicate", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n3_table_name_surrounding_spaces(client, tables_store):
    """N3: tableNameの前後スペースはトリムされ正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": f"  {_TABLE_NAME}  "}
    response = client.post("/api/table/duplicate", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n3_new_table_name_surrounding_spaces(client, tables_store):
    """N3: newTableNameの前後スペースはトリムされ正常処理される"""
    payload = {**_BASE_PAYLOAD, "newTableName": "  SpacedName  "}
    response = client.post("/api/table/duplicate", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["result"]["tableName"] == "SpacedName"


def test_n4_new_table_name_max_length(client, tables_store):
    """N4: newTableNameが最大文字数（128文字）でも正常処理される"""
    payload = {
        **_BASE_PAYLOAD,
        "newTableName": "a" * MAX_NEW_TABLE_NAME_LENGTH,
    }
    response = client.post("/api/table/duplicate", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n5_new_table_name_exceeds_max_length(client, tables_store):
    """N5: newTableNameが最大文字数を超えると 422 VALIDATION_ERROR"""
    payload = {
        **_BASE_PAYLOAD,
        "newTableName": "a" * (MAX_NEW_TABLE_NAME_LENGTH + 1),
    }
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"newTableNameは{MAX_NEW_TABLE_NAME_LENGTH}"
        "文字以内で入力してください。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_n6_new_table_name_with_tab(client, tables_store):
    """N6: newTableNameにタブ文字が含まれると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "newTableName": "Tab\tName"}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "newTableNameに使用できない文字が含まれています。"
    )
    assert response_data["details"] == [
        "newTableNameに使用できない文字が含まれています。"
    ]


def test_n7_new_table_name_only_spaces(client, tables_store):
    """N7: newTableNameがスペースのみの場合はトリム後に空になり 422"""
    payload = {**_BASE_PAYLOAD, "newTableName": "   "}
    response = client.post("/api/table/duplicate", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "newTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "newTableNameは1文字以上で入力してください。"
    ]
