"""相関係数テーブル作成APIのテスト"""

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE = "TestTable"
_TABLE_WITH_NULLS = "TestTableWithNulls"
_TABLE_STRING = "TestTableString"
_NEW_TABLE = "CorrelationResult"

URL = "/api/statistics/create-correlation-table"


# -----------------------------------------------------------
# フィクスチャ
# -----------------------------------------------------------


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()

    # A と B は完全正相関、C は A と完全負相関
    df = pl.DataFrame(
        {
            "A": [1.0, 2.0, 3.0, 4.0, 5.0],
            "B": [2.0, 4.0, 6.0, 8.0, 10.0],
            "C": [5.0, 4.0, 3.0, 2.0, 1.0],
            "D": [2.0, 3.0, 5.0, 4.0, 5.0],
        }
    )
    manager.store_table(_TABLE, df)

    # 欠損値あり
    df_nulls = pl.DataFrame(
        {
            "X": [1.0, None, 3.0, 4.0, 5.0],
            "Y": [2.0, 4.0, None, 8.0, 10.0],
        }
    )
    manager.store_table(_TABLE_WITH_NULLS, df_nulls)

    # 文字列列を含むテーブル
    df_string = pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "score": [1.0, 2.0, 3.0],
        }
    )
    manager.store_table(_TABLE_STRING, df_string)

    yield manager
    manager.clear_tables()


# -----------------------------------------------------------
# 成功ケース
# -----------------------------------------------------------


def test_create_correlation_table_success_pearson(client, tables_store):
    """pearson 手法で相関係数テーブルが正しく作成される"""
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

    # 保存されたテーブルの内容を確認
    df = tables_store.get_table(_NEW_TABLE).table
    assert df["variable_name"].to_list() == ["A", "B"]
    # A と B は完全正相関なので r = 1.0
    assert df["A"].to_list()[0] == pytest.approx(1.0)
    assert df["B"].to_list()[1] == pytest.approx(1.0)
    assert df["A"].to_list()[1] == pytest.approx(1.0)
    assert df["B"].to_list()[0] == pytest.approx(1.0)


def test_create_correlation_table_success_spearman(client, tables_store):
    """spearman 手法で相関係数テーブルが正しく作成される"""
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
    # A と C は完全負相関なので r = -1.0
    df = tables_store.get_table(_NEW_TABLE).table
    assert df["C"].to_list()[0] == pytest.approx(-1.0)


def test_create_correlation_table_success_kendall(client, tables_store):
    """kendall 手法で相関係数テーブルが正しく作成される"""
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
    # A と B は完全正相関なので kendall r = 1.0
    assert df["B"].to_list()[0] == pytest.approx(1.0)


def test_create_correlation_table_success_lower_triangle(client, tables_store):
    """lowerTriangleOnly=True のとき上三角部分が null になる"""
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

    # 行 0（A）: 対角 = 1.0, B列 = null, C列 = null
    assert df["A"].to_list()[0] == pytest.approx(1.0)
    assert df["B"].to_list()[0] is None
    assert df["C"].to_list()[0] is None

    # 行 1（B）: A列 = corr(B,A), 対角 = 1.0, C列 = null
    assert df["A"].to_list()[1] is not None
    assert df["B"].to_list()[1] == pytest.approx(1.0)
    assert df["C"].to_list()[1] is None

    # 行 2（C）: A列 = corr(C,A), B列 = corr(C,B), 対角 = 1.0
    assert df["A"].to_list()[2] is not None
    assert df["B"].to_list()[2] is not None
    assert df["C"].to_list()[2] == pytest.approx(1.0)


def test_create_correlation_table_success_decimal_places(client, tables_store):
    """decimalPlaces が相関係数の丸め精度を制御する"""
    # A と D の pearson 相関係数: 35 / sqrt(1700) ≈ 0.84887658...
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
    assert df3["D"].to_list()[0] == pytest.approx(0.849, abs=1e-9)

    # decimal_places=2 → 0.85
    payload2 = {**base_payload, "newTableName": "Result2", "decimalPlaces": 2}
    res2 = client.post(URL, json=payload2)
    assert res2.status_code == status.HTTP_200_OK
    df2 = tables_store.get_table("Result2").table
    assert df2["D"].to_list()[0] == pytest.approx(0.85, abs=1e-9)

    # decimal_places=1 → 0.8
    payload1 = {**base_payload, "newTableName": "Result1", "decimalPlaces": 1}
    res1 = client.post(URL, json=payload1)
    assert res1.status_code == status.HTTP_200_OK
    df1 = tables_store.get_table("Result1").table
    assert df1["D"].to_list()[0] == pytest.approx(0.8, abs=1e-9)


def test_create_correlation_table_success_pairwise_with_nulls(
    client, tables_store
):
    """pairwise 指定時に欠損値がある列でも相関係数が計算される"""
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

    # 有効なペア: (1,2), (4,8), (5,10) → 完全正相関 r=1.0
    df = tables_store.get_table(_NEW_TABLE).table
    assert df["Y"].to_list()[0] == pytest.approx(1.0)


def test_create_correlation_table_success_listwise_with_nulls(
    client, tables_store
):
    """listwise 指定時に欠損行を一括除去して相関係数が計算される"""
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

    # 有効行（両列が非null）: (1,2), (4,8), (5,10) → r=1.0
    df = tables_store.get_table(_NEW_TABLE).table
    assert df["Y"].to_list()[0] == pytest.approx(1.0)


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
    """columnNames が 1 件しかないとき 422 が返る（スキーマレベルの検証）"""
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

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
