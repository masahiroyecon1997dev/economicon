import datetime
import math

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# --- 定数 ---
TABLE_NAME = "TestTable"
TABLE_NONEXISTENT = "NoTable"
COL_A = "A"
COL_B = "B"
COL_C = "C"
COL_NONEXISTENT = "Z"
ENDPOINT = "/api/column/cast"


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ（文字列データを含む）"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            COL_A: ["1,234.5", "  0.5  ", "abc", None],
            COL_B: ["2026/02/26", "2025/01/01", "invalid", None],
            COL_C: [1, 2, 3, 4],
        }
    )
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_cast_column_str_to_float_with_comma(client, tables_store):
    """正常系 (Numeric): "1,234.5" をカンマ削除後に float に変換できること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_A,
        "cleanupWhitespace": True,
        "removeCommas": True,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == "A_float"

    df = tables_store.get_table(TABLE_NAME).table
    # "1,234.5" → カンマ削除 → "1234.5" → 1234.5
    assert df["A_float"][0] == pytest.approx(1234.5)
    # "  0.5  " → 空白削除 → "0.5" → 0.5
    assert df["A_float"][1] == pytest.approx(0.5)
    # "abc" → 変換失敗 → null (strict=False)
    assert df["A_float"][2] is None


def test_cast_column_str_to_date(client, tables_store):
    """
    正常系 (Date): "2026/02/26" をフォーマット %Y/%m/%d で
    date 型に変換できること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_B,
        "targetType": "date",
        "newColumnName": "B_date",
        "addPositionColumn": COL_B,
        "datetimeFormat": "%Y/%m/%d",
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["B_date"].dtype == pl.Date
    # "2026/02/26" → date(2026, 2, 26)
    assert df["B_date"][0] == datetime.date(2026, 2, 26)
    assert df["B_date"][1] == datetime.date(2025, 1, 1)
    # "invalid" → null (strict=False)
    assert df["B_date"][2] is None


def test_cast_column_insert_position(client, tables_store):
    """正常系: 新しい列が add_position_column の右隣に配置されること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "str",
        "newColumnName": "A_copy",
        "addPositionColumn": COL_C,
        "cleanupWhitespace": False,
        "removeCommas": False,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(TABLE_NAME).table
    # COL_C の右隣に "A_copy" が挿入される
    expected_order = [COL_A, COL_B, COL_C, "A_copy"]
    assert df.columns == expected_order


def test_cast_column_int_non_strict_null(client, tables_store):
    """
    正常系 (Non-Strict): strict=False のとき不適切な文字列が
    null になり処理が続行されること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "int",
        "newColumnName": "A_int",
        "addPositionColumn": COL_A,
        "cleanupWhitespace": True,
        "removeCommas": True,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    # "abc" → null
    assert df["A_int"][2] is None
    # None → null
    assert df["A_int"][3] is None


# ========================================
# 異常系テスト
# ========================================


def test_cast_column_strict_error(client, tables_store):
    """
    異常系 (Strict): strict=True のとき不適切な文字列で
    400 エラーが発生すること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "int",
        "newColumnName": "A_int",
        "addPositionColumn": COL_A,
        "cleanupWhitespace": False,
        "removeCommas": False,
        "strict": True,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.CAST_COLUMN_TYPE_ERROR


def test_cast_column_strict_date_error(client, tables_store):
    """
    異常系 (Strict/Date): strict=True のとき不適切な日付文字列で
    400 エラーが発生すること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_B,
        "targetType": "date",
        "newColumnName": "B_date",
        "addPositionColumn": COL_B,
        "datetimeFormat": "%Y/%m/%d",
        "strict": True,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.CAST_COLUMN_TYPE_ERROR


def test_cast_column_invalid_table(client, tables_store):
    """異常系: 存在しないテーブルを指定した場合に 400 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NONEXISTENT,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_cast_column_invalid_source_column(client, tables_store):
    """異常系: 存在しない変換元列を指定した場合に 400 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_NONEXISTENT,
        "targetType": "float",
        "newColumnName": "Z_float",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_cast_column_invalid_position_column(client, tables_store):
    """異常系: 存在しない挿入位置列を指定した場合に 400 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_NONEXISTENT,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_cast_column_duplicate_column_name(client, tables_store):
    """
    異常系: 既存列名と重複する新列名を指定した場合に
    400 エラーが発生すること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": COL_B,  # 既存列名と重複
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS


def test_cast_column_invalid_target_type(client, tables_store):
    """異常系: 無効な targetType を指定した場合に 422 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "invalid_type",
        "newColumnName": "A_new",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ========================================
# フィクスチャ（追加テスト用）
# ========================================

TABLE_DT = "DtTable"
COL_DT = "DT"
COL_ALL_NULL = "NULLCOL"
COL_NANVAL = "NANVAL"

MAX_COL_LEN = 128


@pytest.fixture
def tables_store_dt():
    """datetime 文字列データを含む TablesStore"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            COL_DT: [
                "2026/02/26 10:00:00",
                "2025/01/01 00:00:00",
                "invalid",
                None,
            ],
            "REF": [1, 2, 3, 4],
        }
    )
    manager.store_table(TABLE_DT, df)
    yield manager
    manager.clear_tables()


@pytest.fixture
def tables_store_special():
    """bool 変換・全 null・NaN/inf 文字列を含む TablesStore"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            COL_ALL_NULL: pl.Series([None, None, None, None], dtype=pl.Utf8),
            COL_NANVAL: ["NaN", "inf", "-inf", "abc"],
            "REF": [1, 2, 3, 4],
        }
    )
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# C1 カバレッジ補完テスト
# ========================================


def test_cast_column_datetime_non_strict(client, tables_store_dt):
    """
    正常系 (Datetime): datetime 文字列を datetime 型に変換できること
    （_build_temporal_expr の datetime ブランチのカバレッジ補完）
    """
    payload = {
        "tableName": TABLE_DT,
        "sourceColumnName": COL_DT,
        "targetType": "datetime",
        "newColumnName": "DT_dt",
        "addPositionColumn": COL_DT,
        "datetimeFormat": "%Y/%m/%d %H:%M:%S",
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store_dt.get_table(TABLE_DT).table
    assert df["DT_dt"].dtype == pl.Datetime
    assert df["DT_dt"][0] == datetime.datetime(2026, 2, 26, 10, 0, 0)
    assert df["DT_dt"][1] == datetime.datetime(2025, 1, 1, 0, 0, 0)
    # "invalid" → null (strict=False)
    assert df["DT_dt"][2] is None


def test_cast_column_datetime_strict_error(client, tables_store_dt):
    """
    異常系 (Strict/Datetime): strict=True のとき不適切な
    datetime 文字列で 400 エラーが発生すること
    """
    payload = {
        "tableName": TABLE_DT,
        "sourceColumnName": COL_DT,
        "targetType": "datetime",
        "newColumnName": "DT_dt",
        "addPositionColumn": COL_DT,
        "datetimeFormat": "%Y/%m/%d %H:%M:%S",
        "strict": True,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.CAST_COLUMN_TYPE_ERROR


def test_cast_column_strict_no_error(client, tables_store):
    """
    正常系 (Strict/全値有効): strict=True かつ全値がキャスト可能な場合に
    200 OK が返ること（_build_scalar_expr の正常分岐カバレッジ補完）
    """
    # COL_C = [1, 2, 3, 4] Int64 → Float64 は全値変換可能
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_C,
        "targetType": "float",
        "newColumnName": "C_float",
        "addPositionColumn": COL_C,
        "strict": True,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["C_float"].dtype == pl.Float64
    assert df["C_float"][0] == pytest.approx(1.0)
    assert df["C_float"][3] == pytest.approx(4.0)


# ========================================
# 422 バリデーションテスト（追加）
# ========================================


def test_cast_column_missing_required_fields(client, tables_store):
    """422: 必須フィールド (tableName, sourceColumnName) が欠落した場合"""
    payload = {
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_cast_column_whitespace_only_table_name(client, tables_store):
    """
    422: tableName がスペースのみ
    （strip_whitespace=True により trim → 空文字 → min_length 違反）
    """
    payload = {
        "tableName": "   ",
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_cast_column_whitespace_only_new_column_name(client, tables_store):
    """
    422: newColumnName がスペースのみ
    （strip_whitespace=True により trim → 空文字 → min_length 違反）
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "   ",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_cast_column_too_long_new_column_name(client, tables_store):
    """422: newColumnName が 128 文字超（max_length=128 違反）"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A" * (MAX_COL_LEN + 1),
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_cast_column_control_char_in_new_column_name(client, tables_store):
    """
    422: newColumnName に制御文字 (\\t = \\x09) が含まれる
    （NAME_PATTERN = r"^[^\\x00-\\x1f\\x7f]+$" 違反）
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "col\t1",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ========================================
# 機能網羅テスト
# ========================================


def test_cast_column_bool(client, tables_store):
    """
    正常系 (Bool): Int64 列を bool 型に変換できること
    Polars は文字列→Boolean の直接キャストをサポートしないため
    Int64 源（0=False、非0=True）を使用する。
    """
    # COL_C = [1, 2, 3, 4] Int64 → bool：全て非ゼロ → True
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_C,
        "targetType": "bool",
        "newColumnName": "C_bool",
        "addPositionColumn": COL_C,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["C_bool"].dtype == pl.Boolean
    # [1, 2, 3, 4] は全て非ゼロ → True
    assert all(v is True for v in df["C_bool"].to_list())


def test_cast_column_non_string_source(client, tables_store):
    """
    正常系 (非文字列ソース): Int64 列を str に変換する際、
    文字列クリーニング処理がスキップされること
    （df.schema[col] != pl.Utf8 のブランチカバレッジ補完）
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_C,  # Int64 [1, 2, 3, 4]
        "targetType": "str",
        "newColumnName": "C_str",
        "addPositionColumn": COL_C,
        "cleanupWhitespace": True,
        "removeCommas": True,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["C_str"].dtype == pl.Utf8
    assert df["C_str"][0] == "1"
    assert df["C_str"][3] == "4"


def test_cast_column_all_null_source(client, tables_store_special):
    """
    正常系 (全 null ソース): 全行が null の列を float に変換すると
    全行 null の Float64 列が追加されること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_ALL_NULL,
        "targetType": "float",
        "newColumnName": "NULL_float",
        "addPositionColumn": COL_ALL_NULL,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store_special.get_table(TABLE_NAME).table
    assert df["NULL_float"].dtype == pl.Float64
    assert df["NULL_float"].null_count() == len(df)


def test_cast_column_nan_inf_string_to_float(client, tables_store_special):
    """
    正常系 (NaN/inf 文字列): Polars は "NaN"→NaN, "inf"→+inf,
    "-inf"→-inf, 変換不能文字列→null として扱うこと
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_NANVAL,
        "targetType": "float",
        "newColumnName": "NAN_float",
        "addPositionColumn": COL_NANVAL,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store_special.get_table(TABLE_NAME).table
    assert df["NAN_float"].dtype == pl.Float64
    # "NaN" → float NaN（null ではない）
    assert math.isnan(df["NAN_float"][0])
    # "inf" → +∞
    assert math.isinf(df["NAN_float"][1])
    assert df["NAN_float"][1] > 0
    # "-inf" → -∞
    assert math.isinf(df["NAN_float"][2])
    assert df["NAN_float"][2] < 0
    # "abc" → null
    assert df["NAN_float"][3] is None


def test_cast_column_japanese_column_name(client, tables_store):
    """
    正常系 (日本語カラム名): newColumnName に日本語を含む名前を指定しても
    正常に処理されること（NAME_PATTERN は \\x00-\\x1f, \\x7f のみ禁止）
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_C,
        "targetType": "float",
        "newColumnName": "人口_float",
        "addPositionColumn": COL_C,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "人口_float"


def test_cast_column_partial_cleanup(client, tables_store):
    """
    正常系 (部分クリーン): cleanup_whitespace=True, remove_commas=False の場合
    空白は除去されるがカンマは残り、"1,234.5" は float 変換失敗 → null
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_partial",
        "addPositionColumn": COL_A,
        "cleanupWhitespace": True,
        "removeCommas": False,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    # "1,234.5" → strip → "1,234.5" → カンマ残 → 変換失敗 → null
    assert df["A_partial"][0] is None
    # "  0.5  " → strip → "0.5" → 0.5
    assert df["A_partial"][1] == pytest.approx(0.5)


def test_cast_column_idempotency(client, tables_store):
    """
    冪等性: 同一パラメータで 2 回リクエストすると、
    1 回目は 200 OK、2 回目は列名重複で 400 DATA_ALREADY_EXISTS が返ること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_idem",
        "addPositionColumn": COL_A,
        "strict": False,
    }
    # 1 回目: 成功
    resp1 = client.post(ENDPOINT, json=payload)
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.json()["code"] == "OK"

    # 2 回目: 列名が既に存在するため失敗
    resp2 = client.post(ENDPOINT, json=payload)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert resp2.json()["code"] == ErrorCode.DATA_ALREADY_EXISTS


def test_cast_column_datetime_strict_success(client, tables_store_dt):
    """
    正常系 (Strict/Datetime/全値有効): strict=True かつ全値が有効な
    datetime 文字列の場合に 200 OK が返ること
    （_build_temporal_expr の strict=True 正常分岐カバレッジ補完）
    """
    # tables_store_dt の DT 列から有効値のみのテーブルを別途登録する
    manager = tables_store_dt
    df_valid = pl.DataFrame(
        {
            COL_DT: [
                "2026/02/26 10:00:00",
                "2025/01/01 00:00:00",
            ],
            "REF": [1, 2],
        }
    )
    table_valid = "DtValid"
    manager.store_table(table_valid, df_valid)

    payload = {
        "tableName": table_valid,
        "sourceColumnName": COL_DT,
        "targetType": "datetime",
        "newColumnName": "DT_dt",
        "addPositionColumn": COL_DT,
        "datetimeFormat": "%Y/%m/%d %H:%M:%S",
        "strict": True,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = manager.get_table(table_valid).table
    assert df["DT_dt"].dtype == pl.Datetime
    assert df["DT_dt"][0] == datetime.datetime(2026, 2, 26, 10, 0, 0)
    assert df["DT_dt"][1] == datetime.datetime(2025, 1, 1, 0, 0, 0)
