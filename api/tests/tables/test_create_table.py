import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ─────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────
MAX_TABLE_NAME_LENGTH = 128
DEFAULT_ROW_COUNT = 3
DEFAULT_COLUMN_NAMES = ["A", "B"]

# ベースペイロード（正常系共通）
_BASE_PAYLOAD: dict = {
    "tableName": "NewTable",
    "rowCount": DEFAULT_ROW_COUNT,
    "columnNames": DEFAULT_COLUMN_NAMES,
}

# model_validatorのエラーメッセージ（filePath未指定時にrowCountが必須）
_MSG_ROW_REQUIRED = (
    "Value error, row_count is required when file_path is not specified"
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
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────────────────────
def test_create_table_success(client, tables_store):
    """テーブルを正常に作成できる"""
    response = client.post("/api/table/create", json=_BASE_PAYLOAD)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "NewTable"
    df = tables_store.get_table("NewTable").table
    assert df.shape == (DEFAULT_ROW_COUNT, len(DEFAULT_COLUMN_NAMES))
    assert df.columns == DEFAULT_COLUMN_NAMES
    assert df["A"].to_list() == [None] * DEFAULT_ROW_COUNT


# ─────────────────────────────────────────────────────────────
# 異常系 400：重複テーブル名
# ─────────────────────────────────────────────────────────────
def test_create_table_duplicate_table_name(client, tables_store):
    """既存テーブル名と重複する場合は 400 DATA_ALREADY_EXISTS"""
    client.post("/api/table/create", json=_BASE_PAYLOAD)
    response = client.post("/api/table/create", json=_BASE_PAYLOAD)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert response_data["message"] == "tableName 'NewTable'は既に存在します。"
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（空・0値・型不正）
# ─────────────────────────────────────────────────────────────
def test_create_table_pydantic_empty_table_name(client, tables_store):
    """tableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": ""}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


def test_create_table_pydantic_zero_row_count(client, tables_store):
    """rowCountが0の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": 0}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは1以上で入力してください。"
    assert response_data["details"] == ["rowCountは1以上で入力してください。"]


def test_create_table_pydantic_negative_row_count(client, tables_store):
    """rowCountが負の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": -1}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは1以上で入力してください。"
    assert response_data["details"] == ["rowCountは1以上で入力してください。"]


def test_create_table_pydantic_row_count_string(client, tables_store):
    """rowCountが文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": "A"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは整数で入力してください。"
    assert response_data["details"] == ["rowCountは整数で入力してください。"]


def test_create_table_pydantic_empty_column_names(client, tables_store):
    """columnNamesが空リストの場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "columnNames": []}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "columnNamesは1件以上ある必要があります。"
    )
    assert response_data["details"] == [
        "columnNamesは1件以上ある必要があります。"
    ]


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（必須項目欠損）
# ─────────────────────────────────────────────────────────────
def test_create_table_pydantic_missing_table_name(client, tables_store):
    """tableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "tableName"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "tableNameは必須項目です。"
    assert response_data["details"] == ["tableNameは必須項目です。"]


def test_create_table_pydantic_missing_row_count(client, tables_store):
    """rowCountが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "rowCount"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == _MSG_ROW_REQUIRED
    assert response_data["details"] == [_MSG_ROW_REQUIRED]


def test_create_table_pydantic_missing_column_names(client, tables_store):
    """columnNamesが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "columnNames"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "columnNamesは必須項目です。"
    assert response_data["details"] == ["columnNamesは必須項目です。"]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N7）
# ─────────────────────────────────────────────────────────────
def test_n1_table_name_japanese(client, tables_store):
    """N1: tableNameに日本語を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "日本語テーブル"}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n2_table_name_emoji(client, tables_store):
    """N2: tableNameに絵文字を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "Table🎲"}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n3_table_name_surrounding_spaces(client, tables_store):
    """N3: tableNameの前後スペースはトリムされ正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "  NewTable2  "}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n4_table_name_max_length(client, tables_store):
    """N4: tableNameが最大文字数（128文字）でも正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "a" * MAX_TABLE_NAME_LENGTH}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n5_table_name_exceeds_max_length(client, tables_store):
    """N5: tableNameが最大文字数を超えると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": "a" * (MAX_TABLE_NAME_LENGTH + 1)}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"tableNameは{MAX_TABLE_NAME_LENGTH}文字以内で入力してください。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_n6_table_name_with_tab(client, tables_store):
    """N6: tableNameにタブ文字が含まれると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": "Tab\tTable"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "tableNameに使用できない文字が含まれています。"
    )
    assert response_data["details"] == [
        "tableNameに使用できない文字が含まれています。"
    ]


def test_n7_table_name_only_spaces(client, tables_store):
    """
    N7:
    tableNameがスペースのみの場合、トリム後に空になり 422 VALIDATION_ERROR
    """
    payload = {**_BASE_PAYLOAD, "tableName": "   "}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]
