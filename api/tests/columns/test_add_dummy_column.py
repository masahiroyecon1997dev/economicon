from unittest.mock import patch

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
    assert response_data["result"]["addedColumnNames"][0] == "is_female"

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

    expected_msg = "dummyColumnName は mode='single' のとき必須です。"

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

    expected_msg = "targetValue は mode='single' のとき必須です。"

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
    assert response_data["result"]["addedColumnNames"][0] == "女性フラグ"

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
    assert response_data["result"]["addedColumnNames"][0] == "👩"


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
    assert response_data["result"]["addedColumnNames"][0] == long_name


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


# ========================================
# all_except_base モード: 基本動作
# ========================================


@pytest.fixture
def tables_store_prefecture():
    """都道府県テーブルのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "prefecture": [
                "Tokyo",
                "Osaka",
                "Nagoya",
                "Tokyo",
                "Osaka",
            ],
            "value": [10, 20, 30, 40, 50],
        }
    )
    manager.store_table("PrefTable", df)
    yield manager
    manager.clear_tables()


def test_add_dummy_all_except_base_success(client, tables_store_prefecture):
    """all_except_base モードで基準値を除く全カテゴリが展開される"""
    payload = {
        "tableName": "PrefTable",
        "sourceColumnName": "prefecture",
        "addPositionColumn": "prefecture",
        "mode": "all_except_base",
        "dropBaseValue": "Tokyo",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    added = response_data["result"]["addedColumnNames"]
    # Nagoya, Osaka (辞書順; Tokyo は base)
    assert added == ["prefecture_Nagoya", "prefecture_Osaka"]

    df = tables_store_prefecture.get_table("PrefTable").table
    # 挿入位置: prefecture の直後
    assert df.columns == [
        "prefecture",
        "prefecture_Nagoya",
        "prefecture_Osaka",
        "value",
    ]
    assert df["prefecture_Nagoya"].to_list() == [0, 0, 1, 0, 0]
    assert df["prefecture_Osaka"].to_list() == [0, 1, 0, 0, 1]


def test_add_dummy_all_except_base_result_keys(
    client, tables_store_prefecture
):
    """all_except_base モードのレスポンスに tableName と
    addedColumnNames が含まれる"""
    payload = {
        "tableName": "PrefTable",
        "sourceColumnName": "prefecture",
        "addPositionColumn": "prefecture",
        "mode": "all_except_base",
        "dropBaseValue": "Tokyo",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["result"]["tableName"] == "PrefTable"
    assert isinstance(response_data["result"]["addedColumnNames"], list)


# ========================================
# 名前衝突テスト
# ========================================


def test_add_dummy_all_except_base_name_collision(client):
    """prefecture_Tokyo が既に存在するとき、_v2 サフィックスが付く"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "prefecture": ["Tokyo", "Osaka", "Nagoya"],
            "prefecture_Tokyo": [1, 0, 0],  # 衝突するカラム
            "value": [10, 20, 30],
        }
    )
    manager.store_table("ColTable", df)

    payload = {
        "tableName": "ColTable",
        "sourceColumnName": "prefecture",
        "addPositionColumn": "prefecture",
        "mode": "all_except_base",
        "dropBaseValue": "Nagoya",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    added = response_data["result"]["addedColumnNames"]
    # Osaka は衝突なし, Tokyo は既存と衝突 → _v2
    assert "prefecture_Osaka" in added
    assert "prefecture_Tokyo_v2" in added
    assert "prefecture_Tokyo" not in added

    manager.clear_tables()


# ========================================
# auto_most_frequent テスト
# ========================================


def test_add_dummy_auto_most_frequent(client):
    """drop_base_value='auto_most_frequent' で最頻値が除外される"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "gender": [
                "male",
                "male",
                "male",
                "female",
                "other",
            ],
            "age": [25, 30, 35, 40, 28],
        }
    )
    manager.store_table("FreqTable", df)

    payload = {
        "tableName": "FreqTable",
        "sourceColumnName": "gender",
        "addPositionColumn": "gender",
        "mode": "all_except_base",
        "dropBaseValue": "auto_most_frequent",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    added = response_data["result"]["addedColumnNames"]
    # male が最頻値 → gender_male は生成されない
    assert "gender_male" not in added
    assert "gender_female" in added
    assert "gender_other" in added

    manager.clear_tables()


# ========================================
# null_strategy テスト
# ========================================


def test_add_dummy_null_strategy_exclude(client):
    """null_strategy='exclude' で空文字・空白がダミー化されない"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "category": ["A", "B", "", " ", "A"],
            "value": [1, 2, 3, 4, 5],
        }
    )
    manager.store_table("NullTable", df)

    payload = {
        "tableName": "NullTable",
        "sourceColumnName": "category",
        "addPositionColumn": "category",
        "mode": "all_except_base",
        "dropBaseValue": "A",
        "nullStrategy": "exclude",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    added = response_data["result"]["addedColumnNames"]
    # 空文字・空白は null → 除外 → B のみ生成
    assert added == ["category_B"]
    # __null__ ダミーは生成されない
    assert not any("__null__" in n for n in added)

    manager.clear_tables()


def test_add_dummy_null_strategy_error(client):
    """null_strategy='error' で null があれば 500 エラー"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "category": ["A", None, "B"],
            "value": [1, 2, 3],
        }
    )
    manager.store_table("NullErrTable", df)

    payload = {
        "tableName": "NullErrTable",
        "sourceColumnName": "category",
        "addPositionColumn": "category",
        "mode": "all_except_base",
        "dropBaseValue": "A",
        "nullStrategy": "error",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        response_data["code"] == ErrorCode.ADD_DUMMY_COLUMN_NULL_VALUES_FOUND
    )

    manager.clear_tables()


def test_add_dummy_null_strategy_as_category(client):
    """null_strategy='as_category' で __null__ ダミーが生成される"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "category": ["A", None, "B", None, "A"],
            "value": [1, 2, 3, 4, 5],
        }
    )
    manager.store_table("AsCatTable", df)

    payload = {
        "tableName": "AsCatTable",
        "sourceColumnName": "category",
        "addPositionColumn": "category",
        "mode": "all_except_base",
        "dropBaseValue": "A",
        "nullStrategy": "as_category",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    added = response_data["result"]["addedColumnNames"]
    # null カテゴリのダミーが生成されている
    # "category___null__" → サニタイズ後 "category_null"
    assert "category_null" in added
    assert "category_B" in added

    df_result = manager.get_table("AsCatTable").table
    # null 行が 1、非 null 行が 0
    assert df_result["category_null"].to_list() == [0, 1, 0, 1, 0]

    manager.clear_tables()


# ========================================
# 順序保証テスト
# ========================================


def test_add_dummy_column_order_guarantee(client):
    """追加された n-1 個のカラムが指定位置に辞書順で並ぶ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "city": ["Nagoya", "Tokyo", "Osaka", "Nagoya", "Osaka"],
            "pop": [100, 200, 150, 110, 160],
        }
    )
    manager.store_table("CityTable", df)

    payload = {
        "tableName": "CityTable",
        "sourceColumnName": "city",
        "addPositionColumn": "city",
        "mode": "all_except_base",
        "dropBaseValue": "Tokyo",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    added = response_data["result"]["addedColumnNames"]

    # 辞書順: Nagoya < Osaka (Tokyo は base で除外)
    assert added == ["city_Nagoya", "city_Osaka"]

    df_result = manager.get_table("CityTable").table
    # 挿入位置は city の直後
    assert df_result.columns == [
        "id",
        "city",
        "city_Nagoya",
        "city_Osaka",
        "pop",
    ]

    manager.clear_tables()


# ========================================
# all_except_base モード:
# Pydantic バリデーション (422)
# ========================================


def test_add_dummy_all_except_base_missing_drop_base_value(
    client, tables_store
):
    """all_except_base モードで dropBaseValue が未指定なら 422"""
    df_before = tables_store.get_table("TestTable").table.clone()

    payload = {
        "tableName": "TestTable",
        "sourceColumnName": "gender",
        "addPositionColumn": "gender",
        "mode": "all_except_base",
        # dropBaseValue を意図的に省略
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "dropBaseValue は mode='all_except_base' のとき必須です。"
    assert response_data["message"] == expected_msg

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_dummy_single_mode_missing_target_value(client, tables_store):
    """single モードで targetValue が未指定なら 422"""
    df_before = tables_store.get_table("TestTable").table.clone()

    payload = {
        "tableName": "TestTable",
        "sourceColumnName": "gender",
        "dummyColumnName": "is_female",
        "addPositionColumn": "gender",
        "mode": "single",
        # targetValue を意図的に省略
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "targetValue は mode='single' のとき必須です。"
    assert response_data["message"] == expected_msg

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


# ========================================
# カラム名サニタイズテスト
# ========================================


def test_add_dummy_all_except_base_sanitize_col_name(client):
    """カテゴリ値にスペースが含まれる場合、_ に置換される"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "region": ["East Asia", "West Europe", "East Asia"],
            "value": [1, 2, 3],
        }
    )
    manager.store_table("RegTable", df)

    payload = {
        "tableName": "RegTable",
        "sourceColumnName": "region",
        "addPositionColumn": "region",
        "mode": "all_except_base",
        "dropBaseValue": "East Asia",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    added = response_data["result"]["addedColumnNames"]
    # "West Europe" → "West_Europe" に置換
    assert added == ["region_West_Europe"]

    manager.clear_tables()


# ========================================
# カバレッジ補完テスト
# ========================================


def test_make_unique_name_requires_v3(client):
    """
    _v2 まで衝突するとき _v3 が付与される

    _make_unique_name の while ループが 2 回目を実行する
    ケース（line 43）をカバーする。
    """
    manager = TablesStore()
    manager.clear_tables()
    # prefecture_Tokyo と prefecture_Tokyo_v2 が既存 → _v3 が必要
    df = pl.DataFrame(
        {
            "prefecture": ["Tokyo", "Osaka", "Nagoya"],
            "prefecture_Tokyo": [1, 0, 0],
            "prefecture_Tokyo_v2": [0, 0, 1],
            "value": [10, 20, 30],
        }
    )
    manager.store_table("TripleCollTable", df)

    payload = {
        "tableName": "TripleCollTable",
        "sourceColumnName": "prefecture",
        "addPositionColumn": "prefecture",
        "mode": "all_except_base",
        "dropBaseValue": "Nagoya",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    added = response_data["result"]["addedColumnNames"]
    assert "prefecture_Osaka" in added
    # _v2 も衝突するため _v3 が割り当てられる
    assert "prefecture_Tokyo_v3" in added

    manager.clear_tables()


def test_execute_unexpected_exception_returns_500(client, tables_store):
    """
    execute() 内で予期しない例外が発生した場合に 500 が返る

    update_table を RuntimeError に差し替えて
    except Exception as e: ブランチ（line 143-148）をカバーする。
    """
    expected_code = ErrorCode.ADD_DUMMY_COLUMN_PROCESS_ERROR

    payload = {
        "tableName": "TestTable",
        "sourceColumnName": "gender",
        "dummyColumnName": "is_male",
        "addPositionColumn": "gender",
        "targetValue": "male",
    }
    with patch.object(
        TablesStore,
        "update_table",
        side_effect=RuntimeError("forced unexpected error"),
    ):
        response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data["code"] == expected_code


def test_single_mode_null_strategy_error_with_null_returns_500(client):
    """
    mode='single', null_strategy='error', ソース列に null あり → 500

    _execute_single の null チェックブランチ（line 160-162）をカバーする。
    """
    expected_code = ErrorCode.ADD_DUMMY_COLUMN_NULL_VALUES_FOUND

    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "category": ["A", None, "B"],
            "value": [1, 2, 3],
        }
    )
    manager.store_table("NullSingleTable", df)

    payload = {
        "tableName": "NullSingleTable",
        "sourceColumnName": "category",
        "dummyColumnName": "is_a",
        "addPositionColumn": "category",
        "targetValue": "A",
        "nullStrategy": "error",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data["code"] == expected_code

    manager.clear_tables()


def test_single_mode_null_strategy_error_no_null_returns_200(client):
    """
    mode='single', null_strategy='error', ソース列に null なし → 200

    _execute_single の null チェック（line 160）で
    is_null().any() = False のとき正常処理されるブランチ（160->168）をカバー。
    """
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "category": ["A", "B", "C"],
            "value": [1, 2, 3],
        }
    )
    manager.store_table("NoNullTable", df)

    payload = {
        "tableName": "NoNullTable",
        "sourceColumnName": "category",
        "dummyColumnName": "is_a",
        "addPositionColumn": "category",
        "targetValue": "A",
        "nullStrategy": "error",
    }
    response = client.post("/api/column/add-dummy", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert "is_a" in response_data["result"]["addedColumnNames"]

    manager.clear_tables()
