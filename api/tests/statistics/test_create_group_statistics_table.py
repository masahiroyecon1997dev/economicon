"""GroupBy 統計テーブル作成 API のテスト"""

import polars as pl
import pytest
from fastapi import status

URL = "/api/statistics/create-group-statistics-table"

_GROUP_TABLE = "GroupTable"
_FLOAT_KEY_TABLE = "FloatKeyTable"
_NEW_TABLE = "GroupStatsResult"

# -----------------------------------------------------------
# テスト用データ
# -----------------------------------------------------------

# category: str, value: f64, score: i64
# X → [10.0, 20.0]  mean=15.0  std=7.0711...
# Y → [30.0, 40.0, 50.0]  mean=40.0  std=10.0
_GROUP_DF = pl.DataFrame(
    {
        "category": ["X", "X", "Y", "Y", "Y"],
        "sub_group": ["a", "b", "a", "a", "b"],
        "value": [10.0, 20.0, 30.0, 40.0, 50.0],
        "score": pl.Series([1, 2, 3, 4, 5], dtype=pl.Int64),
    }
)

_FLOAT_KEY_DF = pl.DataFrame(
    {
        "float_key": [1.5, 2.5, 1.5],
        "value": [10.0, 20.0, 30.0],
    }
)


@pytest.fixture
def group_tables_store(tables_store):
    """GroupBy テスト用テーブルを追加した TablesStore"""
    tables_store.store_table(_GROUP_TABLE, _GROUP_DF)
    tables_store.store_table(_FLOAT_KEY_TABLE, _FLOAT_KEY_DF)
    return tables_store


# -----------------------------------------------------------
# 成功ケース
# -----------------------------------------------------------


def test_create_group_statistics_table_success_mean_std(
    client, group_tables_store
):
    """mean/std を指定して GroupBy 統計テーブルが正常作成される"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["value"],
        "statistics": ["mean", "std_dev"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    assert data["result"]["tableName"] == _NEW_TABLE

    result_df = group_tables_store.get_table(_NEW_TABLE).table
    assert result_df.columns == ["category", "value__mean", "value__std_dev"]

    x_row = result_df.filter(pl.col("category") == "X")
    assert x_row["value__mean"][0] == pytest.approx(15.0)
    assert x_row["value__std_dev"][0] == pytest.approx(7.0710678118654755)

    y_row = result_df.filter(pl.col("category") == "Y")
    assert y_row["value__mean"][0] == pytest.approx(40.0)
    assert y_row["value__std_dev"][0] == pytest.approx(10.0)


def test_create_group_statistics_table_success_iqr_range(
    client, group_tables_store
):
    """IQR・RANGE の後処理計算が正しく動作する"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["value"],
        "statistics": ["iqr", "range"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    result_df = group_tables_store.get_table(_NEW_TABLE).table
    assert result_df.columns == ["category", "value__iqr", "value__range"]

    x_row = result_df.filter(pl.col("category") == "X")
    # X: [10, 20] → q75=20.0 (nearest),
    # q25=10.0 (nearest) → IQR=10.0; range=10.0
    assert x_row["value__iqr"][0] == pytest.approx(10.0)
    assert x_row["value__range"][0] == pytest.approx(10.0)

    y_row = result_df.filter(pl.col("category") == "Y")
    # Y: [30, 40, 50] → q75=50.0 (nearest),
    # q25=40.0 (nearest) → IQR=10.0; range=20.0
    assert y_row["value__iqr"][0] == pytest.approx(10.0)
    assert y_row["value__range"][0] == pytest.approx(20.0)


def test_create_group_statistics_table_success_multi_group_keys(
    client, group_tables_store
):
    """複数のグループキーで正常に集計できる"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category", "sub_group"],
        "statColumns": ["value"],
        "statistics": ["count", "mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    result_df = group_tables_store.get_table(_NEW_TABLE).table
    assert result_df.columns == [
        "category",
        "sub_group",
        "value__count",
        "value__mean",
    ]
    expected_rows = 4
    assert result_df.height == expected_rows  # (X,a), (X,b), (Y,a), (Y,b)


def test_create_group_statistics_table_success_multi_stat_columns(
    client, group_tables_store
):
    """複数の統計列で結果テーブルの列が正しく並ぶ"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["value", "score"],
        "statistics": ["mean", "min"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    result_df = group_tables_store.get_table(_NEW_TABLE).table
    assert result_df.columns == [
        "category",
        "value__mean",
        "value__min",
        "score__mean",
        "score__min",
    ]


# -----------------------------------------------------------
# 400 エラーケース
# -----------------------------------------------------------


def test_create_group_statistics_table_error_table_not_found(
    client, group_tables_store
):
    """存在しないテーブルを指定すると 400 が返る"""
    payload = {
        "tableName": "NonExistent",
        "groupByColumns": ["category"],
        "statColumns": ["value"],
        "statistics": ["mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_NOT_FOUND"
    assert data["message"] == "tableName 'NonExistent'は存在しません。"


def test_create_group_statistics_table_error_new_table_already_exists(
    client, group_tables_store
):
    """新テーブル名が既存テーブルと重複すると 400 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["value"],
        "statistics": ["mean"],
        "newTableName": _GROUP_TABLE,  # 既存テーブル名と同じ
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_ALREADY_EXISTS"
    assert (
        data["message"] == f"newTableName '{_GROUP_TABLE}'は既に存在します。"
    )


def test_create_group_statistics_table_error_group_column_not_found(
    client, group_tables_store
):
    """存在しない GroupBy 列を指定すると 400 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["no_such_col"],
        "statColumns": ["value"],
        "statistics": ["mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_NOT_FOUND"
    assert data["message"] == "groupByColumns 'no_such_col'は存在しません。"


def test_create_group_statistics_table_error_stat_column_not_found(
    client, group_tables_store
):
    """存在しない統計列を指定すると 400 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["no_such_col"],
        "statistics": ["mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_NOT_FOUND"
    assert data["message"] == "statColumns 'no_such_col'は存在しません。"


def test_create_group_statistics_table_error_overlap_columns(
    client, group_tables_store
):
    """GroupBy 列と統計列が重複すると 400 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["category", "value"],  # category が重複
        "statistics": ["mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "VALIDATION_ERROR"
    assert (
        data["message"]
        == "statColumns must not overlap with groupByColumns: category"
    )


def test_create_group_statistics_table_error_float_group_key(
    client, group_tables_store
):
    """浮動小数点列を GroupBy キーにすると 400 が返る"""
    payload = {
        "tableName": _FLOAT_KEY_TABLE,
        "groupByColumns": ["float_key"],
        "statColumns": ["value"],
        "statistics": ["mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "INVALID_DTYPE"
    assert data["message"] == (
        "以下の列は浮動小数点型のためグループキーとして使用できません: "
        "float_key"
    )


# -----------------------------------------------------------
# 422 バリデーションエラーケース
# -----------------------------------------------------------


def test_create_group_statistics_table_validation_empty_group_columns(
    client, group_tables_store
):
    """groupByColumns が空リストだと 422 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": [],
        "statColumns": ["value"],
        "statistics": ["mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_group_statistics_table_validation_empty_stat_columns(
    client, group_tables_store
):
    """statColumns が空リストだと 422 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": [],
        "statistics": ["mean"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_group_statistics_table_validation_empty_statistics(
    client, group_tables_store
):
    """statistics が空リストだと 422 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["value"],
        "statistics": [],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_group_statistics_table_validation_invalid_statistic_type(
    client, group_tables_store
):
    """statistics に無効な値を指定すると 422 が返る"""
    payload = {
        "tableName": _GROUP_TABLE,
        "groupByColumns": ["category"],
        "statColumns": ["value"],
        "statistics": ["invalid_stat"],
        "newTableName": _NEW_TABLE,
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
