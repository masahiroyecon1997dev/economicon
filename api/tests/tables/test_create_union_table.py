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
MAX_TABLE_NAME_LENGTH = 128

# ベースペイロード（正常系共通）
_BASE_PAYLOAD: dict = {
    "unionTableName": "UnionTable",
    "tableNames": ["Table1", "Table2"],
    "columnNames": ["id", "name"],
}


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
    # 第1テーブル（3行・id/name/age/city）
    manager.store_table(
        "Table1",
        pl.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "city": ["Tokyo", "Osaka", "Kyoto"],
            }
        ),
    )
    # 第2テーブル（3行・id/name/age/city）
    manager.store_table(
        "Table2",
        pl.DataFrame(
            {
                "id": [4, 5, 6],
                "name": ["David", "Eve", "Frank"],
                "age": [28, 32, 40],
                "city": ["Nagoya", "Kobe", "Sendai"],
            }
        ),
    )
    # 第3テーブル（2行・id/name/age/city）
    manager.store_table(
        "Table3",
        pl.DataFrame(
            {
                "id": [7, 8],
                "name": ["Grace", "Henry"],
                "age": [27, 33],
                "city": ["Hiroshima", "Fukuoka"],
            }
        ),
    )
    # 列構成が異なるテーブル（id/username/score）
    manager.store_table(
        "DifferentTable",
        pl.DataFrame(
            {
                "id": [9, 10],
                "username": ["user1", "user2"],
                "score": [100, 200],
            }
        ),
    )
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────────────────────
def test_union_two_tables_all_columns(client, tables_store):
    """2テーブルの全カラムをUNIONして正常に作成できる"""
    payload = {
        **_BASE_PAYLOAD,
        "columnNames": ["id", "name", "age", "city"],
    }
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("UnionTable").table
    assert df.shape == (6, 4)
    assert df["id"].to_list() == [1, 2, 3, 4, 5, 6]
    assert df["name"].to_list() == [
        "Alice",
        "Bob",
        "Charlie",
        "David",
        "Eve",
        "Frank",
    ]


def test_union_three_tables_selected_columns(client, tables_store):
    """3テーブルの選択カラムをUNIONして正常に作成できる"""
    payload = {
        **_BASE_PAYLOAD,
        "tableNames": ["Table1", "Table2", "Table3"],
        "columnNames": ["id", "name"],
    }
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("UnionTable").table
    assert df.shape == (8, 2)
    assert df["id"].to_list() == [1, 2, 3, 4, 5, 6, 7, 8]
    assert df["name"].to_list() == [
        "Alice",
        "Bob",
        "Charlie",
        "David",
        "Eve",
        "Frank",
        "Grace",
        "Henry",
    ]


def test_union_preserves_column_order(client, tables_store):
    """指定した順序でカラムが並ぶ"""
    payload = {
        **_BASE_PAYLOAD,
        "columnNames": ["name", "id", "age"],
    }
    response = client.post("/api/table/create-union", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"
    df = tables_store.get_table("UnionTable").table
    assert list(df.columns) == ["name", "id", "age"]


# ─────────────────────────────────────────────────────────────
# 異常系 400：重複テーブル名
# ─────────────────────────────────────────────────────────────
def test_union_table_name_already_exists(client, tables_store):
    """既存テーブル名と重複する場合は 400 DATA_ALREADY_EXISTS"""
    payload = {
        **_BASE_PAYLOAD,
        "unionTableName": "Table1",
    }
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"] == "unionTableName 'Table1'は既に存在します。"
    )
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 400：存在しないテーブル・カラム
# ─────────────────────────────────────────────────────────────
def test_nonexistent_table(client, tables_store):
    """存在しないテーブル名を指定すると 400 DATA_NOT_FOUND"""
    payload = {
        **_BASE_PAYLOAD,
        "tableNames": ["Table1", "NonExistentTable"],
    }
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "tableNames 'NonExistentTable'は存在しません。"
    )
    assert "details" not in response_data


def test_nonexistent_column_in_first_table(client, tables_store):
    """存在しないカラム名を指定すると 400 DATA_NOT_FOUND"""
    payload = {
        **_BASE_PAYLOAD,
        "columnNames": ["id", "nonexistent_column"],
    }
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "columnNames 'nonexistent_column'は存在しません。"
    )
    assert "details" not in response_data


def test_column_missing_in_one_table(client, tables_store):
    """結合対象テーブルの一方にカラムがない場合は 400 DATA_NOT_FOUND"""
    payload = {
        **_BASE_PAYLOAD,
        "tableNames": ["Table1", "DifferentTable"],
        "columnNames": ["id", "name"],
    }
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert response_data["message"] == "columnNames 'name'は存在しません。"
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（空・件数不足）
# ─────────────────────────────────────────────────────────────
def test_union_table_name_empty(client, tables_store):
    """unionTableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "unionTableName": ""}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "unionTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "unionTableNameは1文字以上で入力してください。"
    ]


def test_single_table_in_list(client, tables_store):
    """tableNamesが1件の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableNames": ["Table1"]}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNamesは2件以上ある必要があります。"
    )
    assert response_data["details"] == [
        "tableNamesは2件以上ある必要があります。"
    ]


def test_empty_table_names(client, tables_store):
    """tableNamesが空リストの場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableNames": []}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNamesは2件以上ある必要があります。"
    )
    assert response_data["details"] == [
        "tableNamesは2件以上ある必要があります。"
    ]


def test_empty_column_names(client, tables_store):
    """columnNamesが空リストの場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "columnNames": []}
    response = client.post("/api/table/create-union", json=payload)
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
def test_pydantic_missing_union_table_name(client, tables_store):
    """unionTableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "unionTableName"}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "unionTableNameは必須です。"
    assert response_data["details"] == ["unionTableNameは必須です。"]


def test_pydantic_missing_table_names(client, tables_store):
    """tableNamesが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "tableNames"}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "tableNamesは必須です。"
    assert response_data["details"] == ["tableNamesは必須です。"]


def test_pydantic_missing_column_names(client, tables_store):
    """columnNamesが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "columnNames"}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "columnNamesは必須です。"
    assert response_data["details"] == ["columnNamesは必須です。"]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N7）
# ─────────────────────────────────────────────────────────────
def test_n1_union_table_name_japanese(client, tables_store):
    """N1: unionTableNameに日本語を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "unionTableName": "結合テーブル"}
    response = client.post("/api/table/create-union", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n2_union_table_name_emoji(client, tables_store):
    """N2: unionTableNameに絵文字を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "unionTableName": "Union🔗"}
    response = client.post("/api/table/create-union", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n3_union_table_name_surrounding_spaces(client, tables_store):
    """N3: unionTableNameの前後スペースはトリムされ正常処理される"""
    payload = {**_BASE_PAYLOAD, "unionTableName": "  UnionTable2  "}
    response = client.post("/api/table/create-union", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n4_union_table_name_max_length(client, tables_store):
    """N4: unionTableNameが最大文字数（128文字）でも正常処理される"""
    payload = {**_BASE_PAYLOAD, "unionTableName": "a" * MAX_TABLE_NAME_LENGTH}
    response = client.post("/api/table/create-union", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n5_union_table_name_exceeds_max_length(client, tables_store):
    """N5: unionTableNameが最大文字数を超えると 422 VALIDATION_ERROR"""
    payload = {
        **_BASE_PAYLOAD,
        "unionTableName": "a" * (MAX_TABLE_NAME_LENGTH + 1),
    }
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"unionTableNameは{MAX_TABLE_NAME_LENGTH}文字以内で入力してください。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_n6_union_table_name_with_tab(client, tables_store):
    """N6: unionTableNameにタブ文字が含まれると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "unionTableName": "Union\tTable"}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "unionTableNameに使用できない文字が含まれています。"
    )
    assert response_data["details"] == [
        "unionTableNameに使用できない文字が含まれています。"
    ]


def test_n7_union_table_name_only_spaces(client, tables_store):
    """
    N7:
    unionTableNameがスペースのみの場合、トリム後に空になり 422 VALIDATION_ERROR
    """
    payload = {**_BASE_PAYLOAD, "unionTableName": "   "}
    response = client.post("/api/table/create-union", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "unionTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "unionTableNameは1文字以上で入力してください。"
    ]
