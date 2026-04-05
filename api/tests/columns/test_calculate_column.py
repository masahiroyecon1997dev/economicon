import math

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ========================================
# 定数
# ========================================

TABLE_NAME = "TestTable"
COL_A = "A"
COL_B = "B"
COL_C = "C"
COL_D = "D"
COL_TEXT = "text_col"

# テーブルの初期値
DATA_A = [1, 2, 3]
DATA_B = [4, 5, 6]
DATA_C = [10.0, 20.0, 30.0]
DATA_D = [2.5, 3.5, 4.5]
DATA_TEXT = ["hello", "world", "test"]

# 計算式パラメータ
MULTIPLY_FACTOR = 5
ADD_OFFSET = 10
COMPLEX_MULTIPLIER = 2

# 浮動小数点比較の許容誤差
FLOAT_TOLERANCE = 1e-5


# ========================================
# フィクスチャ
# ========================================


@pytest.fixture
def client():
    """TestClient のフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStore のフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            COL_A: DATA_A,
            COL_B: DATA_B,
            COL_C: DATA_C,
            COL_D: DATA_D,
            COL_TEXT: DATA_TEXT,
        }
    )
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_calculate_column_simple_addition(client, tables_store):
    """単純な足し算で新しい列を追加できる"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == "E"

    df = tables_store.get_table(TABLE_NAME).table
    assert "E" in df.columns
    expected = [a + b for a, b in zip(DATA_A, DATA_B, strict=True)]
    assert df["E"].to_list() == expected
    # 既存データが保持されている
    assert df[COL_A].to_list() == DATA_A


def test_calculate_column_complex_expression(client, tables_store):
    """複合演算式（四則演算とかっこ）で新しい列を追加できる"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "F",
            "calculationExpression": f"{{C}} / {{D}} + ({{A}} + {{B}})"
            f" * {COMPLEX_MULTIPLIER}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert "F" in df.columns
    result_values = df["F"].to_list()
    expected = [
        c / d + (a + b) * COMPLEX_MULTIPLIER
        for a, b, c, d in zip(DATA_A, DATA_B, DATA_C, DATA_D, strict=True)
    ]
    for actual, exp in zip(result_values, expected, strict=True):
        assert abs(actual - exp) < FLOAT_TOLERANCE


def test_calculate_column_with_number(client, tables_store):
    """列と数値の組み合わせで新しい列を追加できる"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "G",
            "calculationExpression": f"{{A}} * {MULTIPLY_FACTOR} "
            f"+ {ADD_OFFSET}",
            "addPositionColumn": COL_A,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table(TABLE_NAME).table
    expected = [a * MULTIPLY_FACTOR + ADD_OFFSET for a in DATA_A]
    assert df["G"].to_list() == expected


def test_calculate_column_add_position_right_of_target(client, tables_store):
    """addPositionColumn の右隣に新しい列が挿入される"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "NewCol",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_C,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table(TABLE_NAME).table
    # COL_C の右隣に挿入
    assert df.columns == [COL_A, COL_B, COL_C, "NewCol", COL_D, COL_TEXT]


def test_calculate_column_division_by_zero(client, tables_store):
    """ゼロ除算は Polars に従い inf または 0.0 を返す（エラーにならない）"""
    df_zero = pl.DataFrame({"X": [1, 2, 0], "Y": [0, 2, 1]})
    tables_store.store_table("ZeroTable", df_zero)

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": "ZeroTable",
            "newColumnName": "Z",
            "calculationExpression": "{X} / {Y}",
            "addPositionColumn": "X",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table("ZeroTable").table
    result_values = df["Z"].to_list()
    # 1/0 = inf, 2/2 = 1.0, 0/1 = 0.0
    assert math.isinf(result_values[0])
    assert result_values[1] == 1.0
    assert result_values[2] == 0.0


# ========================================
# 異常系テスト（Pydantic バリデーション: 422）
# ========================================


def test_calculate_column_missing_table_name(client, tables_store):
    """tableName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "newColumnName": "E",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "tableNameは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_missing_new_column_name(client, tables_store):
    """newColumnName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "newColumnNameは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_missing_calculation_expression(client, tables_store):
    """calculationExpression が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "calculationExpressionは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_missing_add_position_column(client, tables_store):
    """addPositionColumn が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} + {B}",
        },
    )

    expected_msg = "addPositionColumnは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_empty_expression(client, tables_store):
    """calculationExpression が空文字の場合は 422 を返す（minlength=1 違反）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "",
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "calculationExpressionは1文字以上で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 異常系テスト（内部バリデーション: 400）
# ========================================


def test_calculate_column_invalid_table_name(client, tables_store):
    """存在しないテーブル名を指定した場合は 400 を返す"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": "NoTable",
            "newColumnName": "E",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert response_data["message"] == "tableName 'NoTable'は存在しません。"


def test_calculate_column_duplicate_column_name(client, tables_store):
    """既存の列名と同じ newColumnName を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": COL_A,  # 既存の列名
            "calculationExpression": "{B} + {C}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"]
        == f"newColumnName '{COL_A}'は既に存在します。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_invalid_column_in_expression(client, tables_store):
    """計算式に存在しない列名を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} + {Z}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "columnNameInCalculationExpression 'Z'は存在しません。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_non_numeric_column(client, tables_store):
    """計算式に非数値列を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} + {text_col}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.INVALID_DTYPE
    assert COL_TEXT in response_data["message"]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_invalid_position_column(client, tables_store):
    """存在しない addPositionColumn を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": "no_such_col",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "addPositionColumn 'no_such_col'は存在しません。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_unsupported_operator(client, tables_store):
    """サポートされていない演算子（@）を使うと 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            # @ 演算子は OPERATOR_MAP 外 → Pydantic field_validator で 422
            "calculationExpression": "{A} @ {B}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "計算式に未サポートの構文が含まれています: 演算子 '@'"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 異常系テスト（構文バリデーション: 422）
# ========================================


def test_calculate_column_syntax_error_unbalanced_parens(client, tables_store):
    """括弧が閉じられていない場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "({A} + {B}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"].startswith("計算式の構文エラー:")
    assert len(response_data["details"]) == 1
    assert response_data["details"][0].startswith("計算式の構文エラー:")

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_syntax_error_function_call(client, tables_store):
    """未サポートの関数呼び出しを使うと 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "abs({A})",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        "計算式に未サポートの構文が含まれています: 関数呼び出し 'abs'"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_calculate_column_syntax_error_modulo_operator(client, tables_store):
    """未サポートの演算子（%）を使うと 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} % {B}",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "計算式に未サポートの構文が含まれています: 演算子 '%'"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_calculate_column_japanese_new_column_name(client, tables_store):
    """N1: 日本語の新規列名でも正常に計算列が追加される"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "合計値",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "合計値"

    df = tables_store.get_table(TABLE_NAME).table
    assert "合計値" in df.columns
    assert df["合計値"].to_list() == [5, 7, 9]


def test_calculate_column_japanese_formula_reference(client, tables_store):
    """N2: 数式中で日本語列名（{売上}）を参照しても正常に計算される

    formula_parser の re.sub(r"{(\\w+)}", ...) は Unicode \\w にマッチするため
    日本語列名も正しく展開される。
    """
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame(
            {
                "売上": [100, 200, 300],
                COL_B: DATA_B,
                COL_C: DATA_C,
                COL_D: DATA_D,
                COL_TEXT: DATA_TEXT,
            }
        ),
    )
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "売上2倍",
            "calculationExpression": "{売上} * 2",
            "addPositionColumn": "売上",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["売上2倍"].to_list() == [200, 400, 600]


def test_calculate_column_emoji_new_column_name(client, tables_store):
    """N3: 絵文字のみの新規列名でも正常に計算列が追加される"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "💹",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "💹"


def test_calculate_column_strip_whitespace_position_column(
    client, tables_store
):
    """N4: addPositionColumn の前後スペースは除去されて正常に処理される"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": "  A  ",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns[0] == COL_A
    assert df.columns[1] == "E"


def test_calculate_column_max_length_new_column_name(client, tables_store):
    """N5: 128文字（最大長境界値）の新規列名は正常に追加される"""
    long_name = "x" * 128
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": long_name,
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == long_name


def test_calculate_column_too_long_new_column_name(client, tables_store):
    """N6: 129文字（最大長超過）の新規列名は422エラーになる"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "x" * 129,
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameは128文字以内で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_calculate_column_tab_char_new_column_name(client, tables_store):
    """N7: タブ文字を含む新規列名は422エラーになる"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "col	A",
            "calculationExpression": "{A} + {B}",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameに使用できない文字が含まれています。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


# ========================================
# 意地悪な入力テスト (C1-C3: 計算式パターン)
# ========================================


def test_calculate_column_large_power(client, tables_store):
    """
    C2:
        非常に大きな指数演算 ({A} ** 300) でも
        正常に計算される（一部 inf 値許容）
    """
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "{A} ** 300",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"


def test_calculate_column_constant_expression(client, tables_store):
    """C3: 列参照なしの定数式でも正常に計算列が追加される"""
    response = client.post(
        "/api/column/calculate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": "E",
            "calculationExpression": "42 + 0",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
