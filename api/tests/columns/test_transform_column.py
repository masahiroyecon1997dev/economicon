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
# テスト用データ: A = 2^n 系列（対数やべき乗の検証に最適）
DATA_A = [1, 2, 4, 8, 16]
DATA_B = [10, 20, 30, 40, 50]
DATA_C = [0.5, 1.0, 1.5, 2.0, 2.5]
FLOAT_TOLERANCE = 1e-5

# 422 エラーメッセージ定数
# union_tag_invalid はテンプレート未定義のため英語のまま
MSG_INVALID_METHOD = (
    "Input tag 'invalid' found using 'method' does not match"
    " any of the expected tags:"
    " <TransformMethodType.LOG: 'log'>,"
    " <TransformMethodType.POWER: 'power'>,"
    " <TransformMethodType.ROOT: 'root'>"
)
# value_error はテンプレート "{msg}" のまま（翻訳なし）
MSG_LOG_BASE_ONE = "Value error, Log base cannot be 1."


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame({COL_A: DATA_A, COL_B: DATA_B, COL_C: DATA_C})
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


def test_transform_column_log_natural_success(client, tables_store):
    """正常系: 自然対数変換が成功することを検証する"""
    # transformMethod は TransformMethodConfig（Discriminated Union）
    # LogParams/PowerParams/RootParams は BaseModel 継承 → snake_case キー
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_ln",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == "A_ln"
    df = tables_store.get_table(TABLE_NAME).table
    # A の右隣に挿入される
    assert df.columns == [COL_A, "A_ln", COL_B, COL_C]
    ln_values = df["A_ln"].to_list()
    expected = [math.log(v) for v in DATA_A]
    for actual, exp in zip(ln_values, expected):
        assert actual == pytest.approx(exp, abs=FLOAT_TOLERANCE)


def test_transform_column_log_base2_success(client, tables_store):
    """正常系: 底2の対数変換が成功することを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_log2",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log", "log_base": 2},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    log2_values = df["A_log2"].to_list()
    # log2(1)=0, log2(2)=1, log2(4)=2, log2(8)=3, log2(16)=4
    expected = [0, 1, 2, 3, 4]
    for actual, exp in zip(log2_values, expected):
        assert actual == pytest.approx(exp, abs=FLOAT_TOLERANCE)


def test_transform_column_power_square_success(client, tables_store):
    """正常系: 二乗変換（デフォルト exponent=2）が成功することを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_square",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "power"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    square_values = df["A_square"].to_list()
    # 1^2, 2^2, 4^2, 8^2, 16^2
    expected = [1, 4, 16, 64, 256]
    assert square_values == expected


def test_transform_column_power_cube_success(client, tables_store):
    """正常系: 三乗変換（exponent=3）が成功することを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_cube",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "power", "exponent": 3},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    cube_values = df["A_cube"].to_list()
    # 1^3, 2^3, 4^3, 8^3, 16^3
    expected = [1, 8, 64, 512, 4096]
    assert cube_values == expected


def test_transform_column_power_fractional_exponent(client, tables_store):
    """正常系: 小数指数（exponent=0.5 = 平方根）の累乗変換が成功することを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_sqrt",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "power", "exponent": 0.5},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    sqrt_values = df["A_sqrt"].to_list()
    expected = [v**0.5 for v in DATA_A]
    for actual, exp in zip(sqrt_values, expected):
        assert actual == pytest.approx(exp, abs=FLOAT_TOLERANCE)


def test_transform_column_root_square_success(client, tables_store):
    """正常系: 平方根変換（デフォルト root_index=2）が成功することを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_sqrt",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "root"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    sqrt_values = df["A_sqrt"].to_list()
    # sqrt(1)=1, sqrt(2)≈1.41421, sqrt(4)=2, sqrt(8)≈2.82843, sqrt(16)=4
    expected = [v**0.5 for v in DATA_A]
    for actual, exp in zip(sqrt_values, expected):
        assert actual == pytest.approx(exp, abs=FLOAT_TOLERANCE)


def test_transform_column_root_cubic_success(client, tables_store):
    """正常系: 立方根変換（root_index=3）が成功することを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_cbrt",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "root", "root_index": 3},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    cbrt_values = df["A_cbrt"].to_list()
    expected = [v ** (1 / 3) for v in DATA_A]
    for actual, exp in zip(cbrt_values, expected):
        assert actual == pytest.approx(exp, abs=FLOAT_TOLERANCE)


def test_transform_column_root_fractional_success(client, tables_store):
    """正常系: root_index=0.5（二乗）の変換が成功することを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_square",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "root", "root_index": 0.5},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    square_values = df["A_square"].to_list()
    # root_index=0.5 → pow(x, 1/0.5) = x^2
    expected = [v**2 for v in DATA_A]
    for actual, exp in zip(square_values, expected):
        assert actual == pytest.approx(exp, abs=FLOAT_TOLERANCE)


def test_transform_column_invalid_table(client, tables_store):
    """異常系: 存在しないテーブルを指定した場合は400エラーになることを検証する"""
    payload = {
        "tableName": TABLE_NONEXISTENT,
        "sourceColumnName": COL_A,
        "newColumnName": "A_ln",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"tableName '{TABLE_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg


def test_transform_column_invalid_source_column(client, tables_store):
    """異常系: 存在しないソース列名を指定した場合は400エラーになることを検証する"""
    df_before = tables_store.get_table(TABLE_NAME).table
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_NONEXISTENT,
        "newColumnName": "Z_ln",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"sourceColumnName '{COL_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg
    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_transform_column_duplicate_column_name(client, tables_store):
    """異常系: 新列名が既存列名と重複する場合は400エラーになることを検証する"""
    df_before = tables_store.get_table(TABLE_NAME).table
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": COL_B,  # 既存列名
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    expected_msg = f"newColumnName '{COL_B}'は既に存在します。"
    assert response_data["message"] == expected_msg
    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_transform_column_invalid_method(client, tables_store):
    """
    異常系:
        不正な変換メソッドを指定した場合は422エラーになることを検証する
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_invalid",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "invalid"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == MSG_INVALID_METHOD


def test_transform_column_invalid_log_base(client, tables_store):
    """異常系: log_base=1（不正な底）の場合は422エラーになることを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_log",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log", "log_base": 1},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == MSG_LOG_BASE_ONE


def test_transform_column_negative_log_base(client, tables_store):
    """異常系: log_base<0（負の底）の場合は422エラーになることを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_log",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log", "log_base": -2},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    # フィールドパスが長いため（transformMethod.log.LogParams.log_base）
    # log_base に関わるフィールドエラーであることを確認
    assert "log_base" in response_data["message"]


def test_transform_column_missing_table_name(client, tables_store):
    """異常系: tableNameが欠けている場合は422エラーになることを検証する"""
    payload = {
        "sourceColumnName": COL_A,
        "newColumnName": "A_ln",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "tableNameは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_transform_column_missing_source_column_name(client, tables_store):
    """
    異常系:
        sourceColumnNameが欠けている場合は422エラーになることを検証する
    """
    payload = {
        "tableName": TABLE_NAME,
        "newColumnName": "A_ln",
        "addPositionColumn": COL_A,
        "transformMethod": {"method": "log"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "sourceColumnNameは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_transform_column_missing_add_position_column(client, tables_store):
    """
    異常系:
        addPositionColumnが欠けている場合は422エラーになることを検証する
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "newColumnName": "A_ln",
        "transformMethod": {"method": "log"},
    }
    response = client.post("/api/column/transform", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "addPositionColumnは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_transform_column_process_error(client, tables_store):
    """異常系: update_tableが例外を送出するとき500エラーになることを検証する"""
    original_update_table = tables_store.update_table
    try:

        def raise_error(*args, **kwargs):
            raise RuntimeError("forced error")

        tables_store.update_table = raise_error
        payload = {
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": "A_ln",
            "addPositionColumn": COL_A,
            "transformMethod": {"method": "log"},
        }
        response = client.post("/api/column/transform", json=payload)
        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            response_data["code"] == ErrorCode.TRANSFORM_COLUMN_PROCESS_ERROR
        )
    finally:
        tables_store.update_table = original_update_table
