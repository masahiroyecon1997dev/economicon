"""相関係数テーブル作成APIのテスト"""

import math

import polars as pl
import pytest
from fastapi import status

from tests.statistics.conftest import load_statistics_gold_case

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE = "TestTable"
_TABLE_WITH_NULLS = "TestTableWithNulls"
_TABLE_STRING = "TestTableString"
_TABLE_SPARSE = "TestTableSparse"  # P-Q で有効ペア数 0
_TABLE_CONSTANT = "TestTableConstant"  # 定数列（分散ゼロ）
_TABLE_JP = "日本語テーブル"  # 日本語テーブル・列名
_TABLE_LARGE = "TestTableLarge"  # 5 列（大きな行列）
_NEW_TABLE = "CorrelationResult"

URL = "/api/statistics/create-correlation-table"

# -----------------------------------------------------------
# 422 エラーメッセージ定数
# -----------------------------------------------------------
_MSG_METHOD_INVALID = (
    "methodは次のいずれかである必要があります: pearson, spearman, kendall"
)
_MSG_MISSING_HANDLING_INVALID = (
    "missingHandlingは次のいずれかである必要があります: pairwise, listwise"
)
_MSG_DECIMAL_PLACES_TOO_SMALL = "decimalPlacesは1以上で入力してください。"
_MSG_DECIMAL_PLACES_TOO_LARGE = "decimalPlacesは15以下で入力してください。"
_MSG_TABLE_NAME_REQUIRED = "tableNameは必須です。"
_MSG_TABLE_NAME_EMPTY = "tableNameは1文字以上で入力してください。"
_MSG_COLUMN_NAMES_NOT_LIST = "columnNamesはリストで入力してください。"
_MSG_COLUMN_NAMES_TOO_FEW = "columnNamesは2件以上ある必要があります。"


# -----------------------------------------------------------
# 成功ケース
# -----------------------------------------------------------


def _assert_corr_table_matches_gold(df: pl.DataFrame, case_id: str) -> None:
    gold = load_statistics_gold_case("correlation_table", case_id)
    expected = gold["expected"]
    order = expected["variable_order"]

    assert df["variable_name"].to_list() == order

    for row_idx, row_name in enumerate(order):
        for col_idx, col_name in enumerate(order):
            actual = df[col_name].to_list()[row_idx]
            expected_value = expected["rounded_matrix"][row_idx][col_idx]
            if expected_value is None:
                assert actual is None or math.isnan(actual), (
                    "expected null at "
                    f"({row_name}, {col_name}) but got {actual}"
                )
            else:
                assert actual == pytest.approx(expected_value, abs=1e-8)


def test_create_correlation_table_success_pearson(client, tables_store):
    """pearson 手法で相関係数テーブルが gold JSON と一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    assert data["result"]["tableName"] == _NEW_TABLE
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_ab_pearson_dp3")


def test_create_correlation_table_success_spearman(client, tables_store):
    """spearman 手法で相関係数テーブルが gold JSON と一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "C"],
        "newTableName": _NEW_TABLE,
        "method": "spearman",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_ac_spearman_dp3")


def test_create_correlation_table_success_kendall(client, tables_store):
    """kendall 手法で相関係数テーブルが gold JSON と一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "kendall",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_ab_kendall_dp3")


def test_create_correlation_table_success_lower_triangle(client, tables_store):
    """lowerTriangleOnly=True の行列が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B", "C"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": True,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_abc_lower_triangle_pairwise")


def test_create_correlation_table_success_decimal_places(client, tables_store):
    """decimalPlaces が gold JSON と同じ丸め結果を返す"""
    base_payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "D"],
        "method": "pearson",
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }

    # decimal_places=3 → 0.849
    payload3 = {**base_payload, "newTableName": "Result3", "decimalPlaces": 3}
    res3 = client.post(URL, json=payload3)
    assert res3.status_code == status.HTTP_200_OK
    df3 = tables_store.get_table("Result3").table
    _assert_corr_table_matches_gold(df3, "corr_ad_pearson_dp3")

    payload2 = {**base_payload, "newTableName": "Result2", "decimalPlaces": 2}
    res2 = client.post(URL, json=payload2)
    assert res2.status_code == status.HTTP_200_OK
    df2 = tables_store.get_table("Result2").table
    _assert_corr_table_matches_gold(df2, "corr_ad_pearson_dp2")

    payload1 = {**base_payload, "newTableName": "Result1", "decimalPlaces": 1}
    res1 = client.post(URL, json=payload1)
    assert res1.status_code == status.HTTP_200_OK
    df1 = tables_store.get_table("Result1").table
    _assert_corr_table_matches_gold(df1, "corr_ad_pearson_dp1")


def test_create_correlation_table_success_pairwise_with_nulls(
    client, tables_store
):
    """pairwise 指定時の相関係数が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_WITH_NULLS,
        "columnNames": ["X", "Y"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_xy_pairwise_pearson")


def test_create_correlation_table_success_listwise_with_nulls(
    client, tables_store
):
    """listwise 指定時の相関係数が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_WITH_NULLS,
        "columnNames": ["X", "Y"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "listwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_xy_listwise_pearson")


def test_create_correlation_table_result_schema(client, tables_store):
    """結果テーブルのスキーマが正しい（1列目 String, 残列 Float64）"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B", "C"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    client.post(URL, json=payload)
    df = tables_store.get_table(_NEW_TABLE).table

    assert df.schema["variable_name"] == pl.String
    assert df.schema["A"] == pl.Float64
    assert df.schema["B"] == pl.Float64
    assert df.schema["C"] == pl.Float64
    assert df.shape == (3, 4)  # 3行（変数数）× 4列（variable_name + 3変数）


# -----------------------------------------------------------
# 異常ケース（バリデーションエラー: 400）
# -----------------------------------------------------------


def test_create_correlation_table_table_not_found(client, tables_store):
    """存在しないテーブル名を指定したとき 400 が返る"""
    payload = {
        "tableName": "NonExistentTable",
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_NOT_FOUND"
    assert "tableName" in data["message"]


def test_create_correlation_table_new_table_already_exists(
    client, tables_store
):
    """新テーブル名が既存のテーブル名と重複するとき 400 が返る"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B"],
        # _TABLE は既に存在するテーブル名
        "newTableName": _TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_ALREADY_EXISTS"
    assert "newTableName" in data["message"]


def test_create_correlation_table_column_not_found(client, tables_store):
    """存在しない列名を指定したとき 400 が返る"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "NonExistentColumn"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_NOT_FOUND"
    assert "columnNames" in data["message"]


def test_create_correlation_table_non_numeric_column(client, tables_store):
    """数値型でない列を指定したとき 400 が返る"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNames": ["name", "score"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "INVALID_DTYPE"
    assert "name" in data["message"]  # 非数値列名がメッセージに含まれる


def test_create_correlation_table_too_few_columns(client, tables_store):
    """columnNames が 1 件しかないとき 422 が返り、メッセージが一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_COLUMN_NAMES_TOO_FEW
    assert data["details"] == [_MSG_COLUMN_NAMES_TOO_FEW]


# -----------------------------------------------------------
# 422 エラーメッセージ完全一致
# -----------------------------------------------------------


def test_create_correlation_table_invalid_method_message(client, tables_store):
    """不正な method を送ると 422 + 日本語メッセージが完全一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "invalid_method",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_METHOD_INVALID
    assert data["details"] == [_MSG_METHOD_INVALID]


def test_create_correlation_table_invalid_missing_handling_message(
    client, tables_store
):
    """不正な missingHandling を送ると 422 + 日本語メッセージが完全一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "unknown",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_MISSING_HANDLING_INVALID
    assert data["details"] == [_MSG_MISSING_HANDLING_INVALID]


def test_create_correlation_table_decimal_places_below_minimum(
    client, tables_store
):
    """decimalPlaces=0（ge=1 違反）のとき 422 + メッセージが完全一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 0,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_DECIMAL_PLACES_TOO_SMALL
    assert data["details"] == [_MSG_DECIMAL_PLACES_TOO_SMALL]


def test_create_correlation_table_decimal_places_above_maximum(
    client, tables_store
):
    """decimalPlaces=16（le=15 違反）のとき 422 + メッセージが完全一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 16,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_DECIMAL_PLACES_TOO_LARGE
    assert data["details"] == [_MSG_DECIMAL_PLACES_TOO_LARGE]


def test_create_correlation_table_missing_table_name(client, tables_store):
    """tableName を省略したとき 422 + メッセージが完全一致する"""
    payload = {
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_TABLE_NAME_REQUIRED
    assert _MSG_TABLE_NAME_REQUIRED in data["details"]


def test_create_correlation_table_whitespace_only_table_name(
    client, tables_store
):
    """
    tableName がスペースのみのとき strip 後に min_length 違反で 422 になる
    """
    payload = {
        "tableName": "   ",
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_TABLE_NAME_EMPTY
    assert data["details"] == [_MSG_TABLE_NAME_EMPTY]


def test_create_correlation_table_column_names_not_list(client, tables_store):
    """columnNames にリストではなく文字列を送ると 422 になる"""
    payload = {
        "tableName": _TABLE,
        "columnNames": "A",
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == _MSG_COLUMN_NAMES_NOT_LIST
    assert data["details"] == [_MSG_COLUMN_NAMES_NOT_LIST]


# -----------------------------------------------------------
# 統計的境界値ケース
# -----------------------------------------------------------


def test_create_correlation_table_pair_corr_returns_none_when_no_valid_pairs(
    client, tables_store
):
    """pairwise で有効ペアが 0 件のとき gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_SPARSE,
        "columnNames": ["P", "Q"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_sparse_pairwise")


def test_create_correlation_table_constant_column_does_not_raise(
    client, tables_store
):
    """定数列（分散ゼロ）でも 500 を返さず 200 で完了する

    scipy は ConstantInputWarning を発して NaN を返す。
    API は NaN をそのまま格納して正常終了することを確認する。
    """
    payload = {
        "tableName": _TABLE_CONSTANT,
        "columnNames": ["Const", "Vary"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["result"]["tableName"] == _NEW_TABLE
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_constant_column")


def test_create_correlation_table_listwise_spearman_with_nulls(
    client, tables_store
):
    """listwise + spearman の相関係数が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_WITH_NULLS,
        "columnNames": ["X", "Y"],
        "newTableName": _NEW_TABLE,
        "method": "spearman",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "listwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_xy_listwise_spearman")


def test_create_correlation_table_listwise_kendall_with_nulls(
    client, tables_store
):
    """listwise + kendall の相関係数が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_WITH_NULLS,
        "columnNames": ["X", "Y"],
        "newTableName": _NEW_TABLE,
        "method": "kendall",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "listwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_xy_listwise_kendall")


# -----------------------------------------------------------
# 行列パターン・対称性
# -----------------------------------------------------------


def test_create_correlation_table_symmetry(client, tables_store):
    """相関行列が gold JSON の対称行列と一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B", "C", "D"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 10,  # 丸め誤差を避けるため高精度
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    client.post(URL, json=payload)
    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_abcd_symmetry_dp10")


def test_create_correlation_table_lower_triangle_listwise_pearson(
    client, tables_store
):
    """lowerTriangle=True + listwise + pearson が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B", "C"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": True,
        "missingHandling": "listwise",
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_abc_lower_triangle_listwise")
    # 下三角は非 null
    assert df["A"].to_list()[1] is not None  # (B 行, A 列)
    assert df["A"].to_list()[2] is not None  # (C 行, A 列)
    assert df["B"].to_list()[2] is not None  # (C 行, B 列)


def test_create_correlation_table_five_columns(client, tables_store):
    """
    5 列の行列でスキーマ・形状が正しい
    （variable_name + 5 列 = 6 列 × 5 行）
    """
    cols = ["V1", "V2", "V3", "V4", "V5"]
    payload = {
        "tableName": _TABLE_LARGE,
        "columnNames": cols,
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table(_NEW_TABLE).table
    _assert_corr_table_matches_gold(df, "corr_v1_v5_large_matrix")
    assert df.shape == (5, 6)  # 5 変数 × (variable_name + 5 列)
    assert df["variable_name"].to_list() == cols


# -----------------------------------------------------------
# 日本語・特殊文字
# -----------------------------------------------------------


def test_create_correlation_table_japanese_table_and_column_names(
    client, tables_store
):
    """日本語のテーブル名・列名で正常に計算・保存できる"""
    new_jp_table = "相関結果テーブル"
    payload = {
        "tableName": _TABLE_JP,
        "columnNames": ["変数A", "変数B"],
        "newTableName": new_jp_table,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["result"]["tableName"] == new_jp_table

    df = tables_store.get_table(new_jp_table).table
    _assert_corr_table_matches_gold(df, "corr_japanese_names")
    assert df["variable_name"].to_list() == ["変数A", "変数B"]
    assert df.schema["変数A"] == pl.Float64
    assert df.schema["変数B"] == pl.Float64


def test_create_correlation_table_table_name_with_leading_trailing_spaces(
    client, tables_store
):
    """tableName の前後スペースは strip されてテーブルが見つかる"""
    payload = {
        "tableName": f"  {_TABLE}  ",  # 前後スペース付き
        "columnNames": ["A", "B"],
        "newTableName": _NEW_TABLE,
        "method": "pearson",
        "decimalPlaces": 3,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"


# -----------------------------------------------------------
# 冪等性
# -----------------------------------------------------------


def test_create_correlation_table_idempotency(client, tables_store):
    """同一パラメータで 2 回実行しても message / 結果テーブルの値が一致する"""
    base_payload = {
        "tableName": _TABLE,
        "columnNames": ["A", "B", "C"],
        "method": "pearson",
        "decimalPlaces": 5,
        "lowerTriangleOnly": False,
        "missingHandling": "pairwise",
    }
    res1 = client.post(URL, json={**base_payload, "newTableName": "Idem1"})
    res2 = client.post(URL, json={**base_payload, "newTableName": "Idem2"})

    assert res1.status_code == status.HTTP_200_OK
    assert res2.status_code == status.HTTP_200_OK

    df1 = tables_store.get_table("Idem1").table
    df2 = tables_store.get_table("Idem2").table

    # 変数名・スキーマが同一
    assert df1["variable_name"].to_list() == df2["variable_name"].to_list()
    # 全要素が一致
    for col in ["A", "B", "C"]:
        for v1, v2 in zip(
            df1[col].to_list(), df2[col].to_list(), strict=False
        ):
            if v1 is None:
                assert v2 is None
            else:
                assert v1 == pytest.approx(v2, abs=1e-12)
