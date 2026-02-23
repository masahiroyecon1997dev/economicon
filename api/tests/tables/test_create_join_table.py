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

# JOIN操作に有効な joinType 一覧
VALID_JOIN_TYPES = "inner, left, right, full"

# ベースペイロード（共通フィールド）
_BASE_PAYLOAD: dict = {
    "joinTableName": "JoinTable",
    "leftTableName": "LeftTable",
    "rightTableName": "RightTable",
    "leftKeyColumnNames": ["id"],
    "rightKeyColumnNames": ["id"],
    "joinType": "inner",
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
    """TablesStoreのフィクスチャ（LeftTable・RightTableを事前作成）"""
    manager = TablesStore()
    manager.clear_tables()
    # 左テーブル: id=[1,2,3,4]
    left_df = pl.DataFrame(
        {"id": [1, 2, 3, 4], "val_left": ["A", "B", "C", "D"]}
    )
    manager.store_table("LeftTable", left_df)
    # 右テーブル: id=[3,4,5,6]
    right_df = pl.DataFrame(
        {"id": [3, 4, 5, 6], "val_right": ["X", "Y", "Z", "W"]}
    )
    manager.store_table("RightTable", right_df)
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# 正常系：各結合タイプ
# ─────────────────────────────────────────────────────────────
def test_inner_join(client, tables_store):
    """inner join で一致行のみが結果に含まれる"""
    payload = {**_BASE_PAYLOAD, "joinType": "inner"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (2, 3)
    assert df["id"].to_list() == [3, 4]
    assert df["val_left"].to_list() == ["C", "D"]
    assert df["val_right"].to_list() == ["X", "Y"]


def test_left_join(client, tables_store):
    """left join で左テーブルの全行が結果に含まれる"""
    payload = {**_BASE_PAYLOAD, "joinType": "left"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (4, 3)
    assert df["id"].to_list() == [1, 2, 3, 4]
    assert df["val_left"].to_list() == ["A", "B", "C", "D"]
    assert df["val_right"].to_list() == [None, None, "X", "Y"]


def test_right_join(client, tables_store):
    """right join で右テーブルの全行が結果に含まれる"""
    payload = {**_BASE_PAYLOAD, "joinType": "right"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (4, 3)
    assert df["id"].to_list() == [3, 4, 5, 6]
    assert df["val_left"].to_list() == ["C", "D", None, None]
    assert df["val_right"].to_list() == ["X", "Y", "Z", "W"]


def test_full_join(client, tables_store):
    """full join で両テーブルの全行が結果に含まれる"""
    payload = {**_BASE_PAYLOAD, "joinType": "full"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (6, 3)
    assert df["id"].to_list() == [1, 2, 3, 4, 5, 6]
    assert df["val_left"].to_list() == ["A", "B", "C", "D", None, None]
    assert df["val_right"].to_list() == [None, None, "X", "Y", "Z", "W"]


def test_create_join_table_pydantic_missing_join_type(client, tables_store):
    """joinTypeが省略されたとき、デフォルト（inner）で正常処理される"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "joinType"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    # デフォルトは inner join → 一致行のみ
    assert df.shape == (2, 3)


# ─────────────────────────────────────────────────────────────
# 異常系 400：存在しないリソース / 重複
# ─────────────────────────────────────────────────────────────
def test_left_table_not_found(client, tables_store):
    """左テーブルが存在しない場合は 400 DATA_NOT_FOUND"""
    payload = {**_BASE_PAYLOAD, "leftTableName": "NotExist"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"] == "leftTableName 'NotExist'は存在しません。"
    )
    assert "details" not in response_data


def test_right_table_not_found(client, tables_store):
    """右テーブルが存在しない場合は 400 DATA_NOT_FOUND"""
    payload = {**_BASE_PAYLOAD, "rightTableName": "NotExist"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"] == "rightTableName 'NotExist'は存在しません。"
    )
    assert "details" not in response_data


def test_left_key_column_not_found(client, tables_store):
    """左テーブルのキーカラムが存在しない場合は 400 DATA_NOT_FOUND"""
    payload = {**_BASE_PAYLOAD, "leftKeyColumnNames": ["not_exist_col"]}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "leftKeyColumnNames 'not_exist_col'は存在しません。"
    )
    assert "details" not in response_data


def test_right_key_column_not_found(client, tables_store):
    """右テーブルのキーカラムが存在しない場合は 400 DATA_NOT_FOUND"""
    payload = {**_BASE_PAYLOAD, "rightKeyColumnNames": ["not_exist_col"]}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "rightKeyColumnNames 'not_exist_col'は存在しません。"
    )
    assert "details" not in response_data


def test_create_join_table_duplicate_join_table_name(client, tables_store):
    """
    joinTableNameが既存のテーブル名と重複する場合は 400 DATA_ALREADY_EXISTS
    """
    # "LeftTable" はフィクスチャで既に作成済み
    payload = {**_BASE_PAYLOAD, "joinTableName": "LeftTable"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"]
        == "joinTableName 'LeftTable'は既に存在します。"
    )
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー
# ─────────────────────────────────────────────────────────────
def test_create_join_table_pydantic_empty_join_table_name(
    client, tables_store
):
    """joinTableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "joinTableName": ""}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "joinTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "joinTableNameは1文字以上で入力してください。"
    ]


def test_create_join_table_pydantic_empty_left_table_name(
    client, tables_store
):
    """leftTableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "leftTableName": ""}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "leftTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "leftTableNameは1文字以上で入力してください。"
    ]


def test_create_join_table_pydantic_empty_right_table_name(
    client, tables_store
):
    """rightTableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rightTableName": ""}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "rightTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "rightTableNameは1文字以上で入力してください。"
    ]


def test_create_join_table_pydantic_empty_join_type(client, tables_store):
    """joinTypeが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "joinType": ""}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"joinTypeは次のいずれかである必要があります: {VALID_JOIN_TYPES}"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_create_join_table_pydantic_empty_left_key_column_names(
    client, tables_store
):
    """leftKeyColumnNamesが空リストの場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "leftKeyColumnNames": []}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "leftKeyColumnNamesは1件以上ある必要があります。"
    )
    assert response_data["details"] == [
        "leftKeyColumnNamesは1件以上ある必要があります。"
    ]


def test_create_join_table_pydantic_empty_right_key_column_names(
    client, tables_store
):
    """rightKeyColumnNamesが空リストの場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rightKeyColumnNames": []}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "rightKeyColumnNamesは1件以上ある必要があります。"
    )
    assert response_data["details"] == [
        "rightKeyColumnNamesは1件以上ある必要があります。"
    ]


def test_create_join_table_pydantic_missing_join_table_name(
    client, tables_store
):
    """joinTableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "joinTableName"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "joinTableNameは必須項目です。"
    assert response_data["details"] == ["joinTableNameは必須項目です。"]


def test_create_join_table_pydantic_missing_left_table_name(
    client, tables_store
):
    """leftTableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "leftTableName"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "leftTableNameは必須項目です。"
    assert response_data["details"] == ["leftTableNameは必須項目です。"]


def test_create_join_table_pydantic_missing_right_table_name(
    client, tables_store
):
    """rightTableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "rightTableName"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rightTableNameは必須項目です。"
    assert response_data["details"] == ["rightTableNameは必須項目です。"]


def test_create_join_table_pydantic_missing_left_key_column_names(
    client, tables_store
):
    """leftKeyColumnNamesが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {
        k: v for k, v in _BASE_PAYLOAD.items() if k != "leftKeyColumnNames"
    }
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "leftKeyColumnNamesは必須項目です。"
    assert response_data["details"] == ["leftKeyColumnNamesは必須項目です。"]


def test_create_join_table_pydantic_missing_right_key_column_names(
    client, tables_store
):
    """rightKeyColumnNamesが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {
        k: v for k, v in _BASE_PAYLOAD.items() if k != "rightKeyColumnNames"
    }
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rightKeyColumnNamesは必須項目です。"
    assert response_data["details"] == ["rightKeyColumnNamesは必須項目です。"]


def test_invalid_join_type(client, tables_store):
    """無効な joinType の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "joinType": "diagonal"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"joinTypeは次のいずれかである必要があります: {VALID_JOIN_TYPES}"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N7）
# ─────────────────────────────────────────────────────────────
def test_n1_join_table_name_japanese(client, tables_store):
    """N1: joinTableName に日本語を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "joinTableName": "結合テーブル"}
    response = client.post("/api/table/create-join", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n2_join_table_name_emoji(client, tables_store):
    """N2: joinTableName に絵文字を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "joinTableName": "JoinTable🎉"}
    response = client.post("/api/table/create-join", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n3_join_table_name_surrounding_spaces(client, tables_store):
    """N3: joinTableName の前後スペースはトリムされ正常処理される"""
    payload = {**_BASE_PAYLOAD, "joinTableName": "  JoinTable  "}
    response = client.post("/api/table/create-join", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n4_join_table_name_max_length(client, tables_store):
    """N4: joinTableName が最大文字数（128文字）でも正常処理される"""
    payload = {**_BASE_PAYLOAD, "joinTableName": "a" * MAX_TABLE_NAME_LENGTH}
    response = client.post("/api/table/create-join", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n5_join_table_name_exceeds_max_length(client, tables_store):
    """N5: joinTableName が最大文字数を超えると 422 VALIDATION_ERROR"""
    payload = {
        **_BASE_PAYLOAD,
        "joinTableName": "a" * (MAX_TABLE_NAME_LENGTH + 1),
    }
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"joinTableNameは{MAX_TABLE_NAME_LENGTH}文字以内で入力してください。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_n6_join_table_name_with_tab(client, tables_store):
    """N6: joinTableName にタブ文字が含まれると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "joinTableName": "Join\tTable"}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "joinTableNameに使用できない文字が含まれています。"
    )
    assert response_data["details"] == [
        "joinTableNameに使用できない文字が含まれています。"
    ]


def test_n7_join_table_name_only_spaces(client, tables_store):
    """
    N7:
        joinTableName がスペースのみの場合、トリム後に空になり
        422 VALIDATION_ERROR
    """
    payload = {**_BASE_PAYLOAD, "joinTableName": "   "}
    response = client.post("/api/table/create-join", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "joinTableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "joinTableNameは1文字以上で入力してください。"
    ]
