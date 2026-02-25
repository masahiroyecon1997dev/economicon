import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame(
        {
            "gender": ["male", "female", "female", "male", "other"],
            "age": [25, 30, 35, 40, 28],
        }
    )
    manager.store_table("TestTable", df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_add_dummy_column_success(client, tables_store):
    """正常にダミー変数列を追加できる"""
    payload = {
        "tableName": "TestTable",
        "sourceColumnName": "gender",
        "dummyColumnName": "is_female",
        "addPositionColumn": "gender",
        "targetValue": "female",
    }
    response = client.post(
        "/api/column/add-dummy",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "TestTable"
    assert response_data["result"]["dummyColumnName"] == "is_female"

    df = tables_store.get_table("TestTable").table
    # gender の後に is_female が挿入されている
    assert df.columns == ["gender", "is_female", "age"]
    # female の値が1、それ以外が0になっている
    assert df["is_female"].to_list() == [0, 1, 1, 0, 0]
    # 既存データが保持されている
    assert df["gender"].to_list() == [
        "male",
        "female",
        "female",
        "male",
        "other",
    ]
    assert df["age"].to_list() == [25, 30, 35, 40, 28]


# ========================================
# 異常系テスト（Pydanticバリデーション: 422）
# ========================================


def test_add_dummy_column_missing_table_name(client, tables_store):
    """tableName が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    expected_msg = "tableNameは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_missing_source_column_name(client, tables_store):
    """sourceColumnName が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    expected_msg = "sourceColumnNameは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_missing_dummy_column_name(client, tables_store):
    """dummyColumnName が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    expected_msg = "dummyColumnNameは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_missing_add_position_column(client, tables_store):
    """addPositionColumn が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "targetValue": "female",
        },
    )

    expected_msg = "addPositionColumnは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_missing_target_value(client, tables_store):
    """targetValue が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
        },
    )

    expected_msg = "targetValueは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_empty_table_name(client, tables_store):
    """tableName がスペースのみ（strip後に空文字）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "   ",
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    expected_msg = "tableNameは1文字以上で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_empty_target_value(client, tables_store):
    """targetValue が空文字の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "",
        },
    )

    expected_msg = "targetValueは1文字以上で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_table_name_is_number(client, tables_store):
    """tableName が数値の場合（strict=True なので型エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": 123,
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    expected_msg = "tableNameは文字列で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_dummy_column_name_too_long(client, tables_store):
    """dummyColumnName が129文字（最大128文字を超過）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "a" * 129,
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    expected_msg = "dummyColumnNameは128文字以内で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_dummy_column_name_with_control_char(
    client, tables_store
):
    """dummyColumnName に制御文字（\\x00）が含まれる場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "col\x00name",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    expected_msg = "dummyColumnNameに使用できない文字が含まれています。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


# ========================================
# 異常系テスト（内部バリデーション: 400）
# ========================================


def test_add_dummy_column_invalid_table(client, tables_store):
    """存在しないテーブル名"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "NoTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert response_data["message"] == "tableName 'NoTable'は存在しません。"

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_invalid_source_column(client, tables_store):
    """存在しないソース列名を指定"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "invalid_column",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "sourceColumnName 'invalid_column'は存在しません。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_duplicate_column_name(client, tables_store):
    """既存の列名をダミー列名として指定"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "age",  # 既存の列名
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"] == "dummyColumnName 'age'は既に存在します。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_invalid_position_column(client, tables_store):
    """追加位置指定カラムが存在しない"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "is_female",
            "addPositionColumn": "no_such_column",
            "targetValue": "female",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "addPositionColumn 'no_such_column'は存在しません。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_column_with_numeric_target(client, tables_store):
    """数値のターゲット値でダミー変数を作成"""
    df_numeric = pl.DataFrame(
        {"score": [85, 90, 75, 90, 88], "name": ["A", "B", "C", "D", "E"]}
    )
    tables_store.store_table("NumericTable", df_numeric)

    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "NumericTable",
            "sourceColumnName": "score",
            "dummyColumnName": "is_excellent",
            "addPositionColumn": "score",
            "targetValue": "90",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("NumericTable").table
    # score の後に is_excellent が挿入されている
    assert df.columns == ["score", "is_excellent", "name"]
    # 90 の位置のみ 1
    assert df["is_excellent"].to_list() == [0, 1, 0, 1, 0]


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_add_dummy_column_japanese_dummy_column_name(client, tables_store):
    """N1: 日本語のダミー列名でも正常に追加される"""
    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "女性フラグ",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["dummyColumnName"] == "女性フラグ"

    df = tables_store.get_table("TestTable").table
    assert "女性フラグ" in df.columns
    assert df["女性フラグ"].to_list() == [0, 1, 1, 0, 0]


def test_add_dummy_column_japanese_source_column_name(client, tables_store):
    """N2: sourceColumnName に日本語列名を指定しても正常に処理される"""
    tables_store.update_table(
        "TestTable",
        pl.DataFrame(
            {"性別": ["male", "female", "female"], "age": [25, 30, 35]}
        ),
    )
    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "性別",
            "dummyColumnName": "is_female",
            "addPositionColumn": "性別",
            "targetValue": "female",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    assert "is_female" in df.columns
    assert df["is_female"].to_list() == [0, 1, 1]


def test_add_dummy_column_emoji_dummy_column_name(client, tables_store):
    """N3: 絵文字のみのダミー列名でも正常に追加される"""
    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "👩",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["dummyColumnName"] == "👩"


def test_add_dummy_column_strip_whitespace_source_column(client, tables_store):
    """N4: sourceColumnName の前後スペースは除去されて正常に処理される"""
    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "  gender  ",
            "dummyColumnName": "is_female",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    assert "is_female" in df.columns
    assert df["is_female"].to_list() == [0, 1, 1, 0, 0]


def test_add_dummy_column_max_length_dummy_column_name(client, tables_store):
    """N5: 128文字（最大長境界値）のダミー列名は正常に追加される"""
    long_name = "x" * 128
    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": long_name,
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["dummyColumnName"] == long_name


def test_add_dummy_column_too_long_dummy_column_name(client, tables_store):
    """N6: 129文字（最大長超過）のダミー列名は422エラーになる"""
    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "x" * 129,
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "dummyColumnNameは128文字以内で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_add_dummy_column_tab_char_dummy_column_name(client, tables_store):
    """N7: タブ文字を含むダミー列名は422エラーになる"""
    response = client.post(
        "/api/column/add-dummy",
        json={
            "tableName": "TestTable",
            "sourceColumnName": "gender",
            "dummyColumnName": "col	A",
            "addPositionColumn": "gender",
            "targetValue": "female",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "dummyColumnNameに使用できない文字が含まれています。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]
