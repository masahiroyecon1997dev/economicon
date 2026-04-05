"""記述統計計算APIのテスト"""

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE_NUMERIC = "TestTableNumeric"
_TABLE_STRING = "TestTableString"

_STAT_MEAN = "mean"
_STAT_MEDIAN = "median"
_STAT_MODE = "mode"
_STAT_VARIANCE = "variance"
_STAT_STD_DEV = "std_dev"
_STAT_RANGE = "range"
_STAT_IQR = "iqr"
_STAT_COUNT = "count"
_STAT_NULL_COUNT = "null_count"
_STAT_NULL_RATIO = "null_ratio"
_STAT_POP_VARIANCE = "population_variance"

_STATISTICS_ERROR = (
    "statisticsは次のいずれかである必要があります: "
    "mean, median, mode, variance, std_dev, range, iqr, "
    "count, null_count, null_ratio, population_variance"
)

URL = "/api/statistics/descriptive"


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
    AnalysisResultStore().clear_all()

    df_numeric = pl.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50],
            "C": [5.234, 8.321, 2.976, 4.567, 9.629],
        }
    )
    manager.store_table(_TABLE_NUMERIC, df_numeric)

    df_string = pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Alice", "Bob"],
            "category": ["A", "B", "A", "A", "C"],
        }
    )
    manager.store_table(_TABLE_STRING, df_string)

    yield manager
    manager.clear_tables()
    AnalysisResultStore().clear_all()


@pytest.fixture
def tables_store_with_nulls():
    """null包含データのテーブルストア"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            "X": pl.Series([1.0, None, 3.0, None, 5.0], dtype=pl.Float64),
        }
    )
    manager.store_table("TestNulls", df)
    yield manager
    manager.clear_tables()


# -----------------------------------------------------------
# 成功ケース
# -----------------------------------------------------------


def test_descriptive_statistics_success_numeric(client, tables_store):
    """数値データに対する記述統計の計算が正常に動作する"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [
            _STAT_MEAN,
            _STAT_MEDIAN,
            _STAT_VARIANCE,
            _STAT_STD_DEV,
        ],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert "resultId" in result
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0
    assert result["tableName"] == _TABLE_NUMERIC
    stats_a = result["statistics"]["A"]
    assert stats_a[_STAT_MEAN] == pytest.approx(3.0, abs=1e-5)
    assert stats_a[_STAT_MEDIAN] == pytest.approx(3.0, abs=1e-5)
    assert stats_a[_STAT_VARIANCE] == pytest.approx(2.5, abs=1e-5)
    assert stats_a[_STAT_STD_DEV] == pytest.approx(
        1.5811388300841898, abs=1e-5
    )


def test_descriptive_statistics_numerical_via_describe(client, tables_store):
    """polars describe()との数値照合"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A", "B"],
        "statistics": [_STAT_MEAN, _STAT_STD_DEV],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    df = pl.DataFrame({"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50]})
    desc = df.describe()
    mean_row = desc.filter(pl.col("statistic") == "mean")
    std_row = desc.filter(pl.col("statistic") == "std")
    expected_mean_a = float(mean_row["A"][0])
    expected_std_a = float(std_row["A"][0])
    expected_mean_b = float(mean_row["B"][0])
    expected_std_b = float(std_row["B"][0])

    assert result["statistics"]["A"][_STAT_MEAN] == pytest.approx(
        expected_mean_a, abs=1e-6
    )
    assert result["statistics"]["A"][_STAT_STD_DEV] == pytest.approx(
        expected_std_a, abs=1e-6
    )
    assert result["statistics"]["B"][_STAT_MEAN] == pytest.approx(
        expected_mean_b, abs=1e-6
    )
    assert result["statistics"]["B"][_STAT_STD_DEV] == pytest.approx(
        expected_std_b, abs=1e-6
    )


def test_descriptive_statistics_success_all_stats(client, tables_store):
    """全統計量を複数列で計算する"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A", "B", "C"],
        "statistics": [
            _STAT_MEAN,
            _STAT_MODE,
            _STAT_MEDIAN,
            _STAT_VARIANCE,
            _STAT_STD_DEV,
            _STAT_RANGE,
            _STAT_IQR,
        ],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    stats_b = result["statistics"]["B"]
    assert stats_b[_STAT_MEAN] == pytest.approx(30.0, abs=1e-5)
    assert stats_b[_STAT_MEDIAN] == pytest.approx(30.0, abs=1e-5)
    assert stats_b[_STAT_RANGE] == pytest.approx(40.0, abs=1e-5)
    assert stats_b[_STAT_IQR] == pytest.approx(20.0, abs=1e-5)


def test_descriptive_statistics_range_iqr_numerical(client, tables_store):
    """rangeとIQRの数値をpolarsの直接計算と照合"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_RANGE, _STAT_IQR],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    df = pl.DataFrame({"A": [1, 2, 3, 4, 5]})
    expected_range = float(
        df.select(pl.col("A").max() - pl.col("A").min()).to_series(0)[0]
    )
    expected_iqr = float(
        df.select(
            pl.col("A").quantile(0.75) - pl.col("A").quantile(0.25)
        ).to_series(0)[0]
    )

    assert result["statistics"]["A"][_STAT_RANGE] == pytest.approx(
        expected_range, abs=1e-6
    )
    assert result["statistics"]["A"][_STAT_IQR] == pytest.approx(
        expected_iqr, abs=1e-6
    )


def test_descriptive_statistics_success_string_mode(client, tables_store):
    """文字列データに対するmode計算"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [_STAT_MODE],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    # name列はAliceかBobが最頻値
    assert result["statistics"]["name"][_STAT_MODE] in ["Alice", "Bob"]


def test_descriptive_statistics_count_no_nulls(client, tables_store):
    """nullなしデータでcount/null_count/null_ratioが正しく返る"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_COUNT, _STAT_NULL_COUNT, _STAT_NULL_RATIO],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    stats_a = result["statistics"]["A"]
    _expected_count = 5
    assert stats_a[_STAT_COUNT] == _expected_count
    assert stats_a[_STAT_NULL_COUNT] == 0
    assert stats_a[_STAT_NULL_RATIO] == pytest.approx(0.0, abs=1e-9)


def test_descriptive_statistics_count_with_nulls(
    client, tables_store_with_nulls
):
    """null2件データでcount=3, null_count=2, null_ratio≈0.4"""
    payload = {
        "tableName": "TestNulls",
        "columnNameList": ["X"],
        "statistics": [_STAT_COUNT, _STAT_NULL_COUNT, _STAT_NULL_RATIO],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    stats_x = result["statistics"]["X"]
    _expected_valid = 3
    _expected_null = 2
    assert stats_x[_STAT_COUNT] == _expected_valid
    assert stats_x[_STAT_NULL_COUNT] == _expected_null
    assert stats_x[_STAT_NULL_RATIO] == pytest.approx(0.4, abs=1e-9)


def test_descriptive_statistics_population_variance_numerical(
    client, tables_store
):
    """A=[1..5]で母分散=2.0、不偏分散=2.5の区別を検証"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_VARIANCE, _STAT_POP_VARIANCE],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    stats_a = result["statistics"]["A"]
    # 不偏分散 (ddof=1): 10/4 = 2.5
    assert stats_a[_STAT_VARIANCE] == pytest.approx(2.5, abs=1e-9)
    # 母分散 (ddof=0): 10/5 = 2.0
    assert stats_a[_STAT_POP_VARIANCE] == pytest.approx(2.0, abs=1e-9)


def test_descriptive_statistics_null_stats_on_string_column(
    client, tables_store
):
    """count/null_count/null_ratioは文字列列からも正常値を返す"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [_STAT_COUNT, _STAT_NULL_COUNT, _STAT_NULL_RATIO],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    stats = result["statistics"]["name"]
    _expected_str_count = 5
    assert stats[_STAT_COUNT] == _expected_str_count
    assert stats[_STAT_NULL_COUNT] == 0
    assert stats[_STAT_NULL_RATIO] == pytest.approx(0.0, abs=1e-9)


def test_descriptive_statistics_pop_variance_on_string_column(
    client, tables_store
):
    """population_varianceは文字列列に対してNoneを返す"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [_STAT_POP_VARIANCE],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["statistics"]["name"][_STAT_POP_VARIANCE] is None


def test_descriptive_statistics_string_numeric_stats(client, tables_store):
    """文字列データに対して数値専用統計を要求した場合はNoneが返される"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [
            _STAT_MEAN,
            _STAT_VARIANCE,
            _STAT_STD_DEV,
            _STAT_RANGE,
            _STAT_IQR,
        ],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["statistics"]["name"][_STAT_MEAN] is None
    assert result["statistics"]["name"][_STAT_VARIANCE] is None
    assert result["statistics"]["name"][_STAT_STD_DEV] is None
    assert result["statistics"]["name"][_STAT_RANGE] is None
    assert result["statistics"]["name"][_STAT_IQR] is None


def test_descriptive_statistics_response_structure(client, tables_store):
    """レスポンスのJSON構造が仕様通りである"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    result = response_data["result"]
    assert "tableName" in result
    assert "statistics" in result
    assert "A" in result["statistics"]
    assert _STAT_MEAN in result["statistics"]["A"]


# -----------------------------------------------------------
# 400 エラーケース
# -----------------------------------------------------------


def test_descriptive_statistics_invalid_table(client, tables_store):
    """存在しないテーブル名でDATA_NOT_FOUNDエラーが返される"""
    payload = {
        "tableName": "NoTable",
        "columnNameList": ["A"],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DATA_NOT_FOUND"
    assert response_data["message"] == "tableName 'NoTable'は存在しません。"


def test_descriptive_statistics_invalid_column(client, tables_store):
    """存在しないカラム名でDATA_NOT_FOUNDエラーが返される"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A", "Z"],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DATA_NOT_FOUND"
    assert response_data["message"] == "columnName 'Z'は存在しません。"


# -----------------------------------------------------------
# 422 バリデーションエラーケース
# -----------------------------------------------------------


def test_descriptive_statistics_invalid_statistic(client, tables_store):
    """不正なstatistics値はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": ["invalid_stat"],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert _STATISTICS_ERROR in response_data["message"]


def test_descriptive_statistics_old_std_value_is_invalid(client, tables_store):
    """旧値'std'はVALIDATION_ERRORになる（正しくは'std_dev'）"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": ["std"],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert _STATISTICS_ERROR in response_data["message"]


def test_descriptive_statistics_empty_statistics_list(client, tables_store):
    """空のstatisticsリストはVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "statisticsは1件以上ある必要があります。" in response_data["message"]
    )


def test_descriptive_statistics_empty_column_name_list(client, tables_store):
    """空のcolumnNameListはVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": [],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "columnNameListは1件以上ある必要があります。"
        in response_data["message"]
    )


def test_descriptive_statistics_empty_table_name(client, tables_store):
    """tableNameが空文字列の場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": "",
        "columnNameList": ["A"],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "tableNameは1文字以上で入力してください。" in response_data["message"]
    )


def test_descriptive_statistics_whitespace_only_table_name(
    client, tables_store
):
    """tableNameがスペースのみの場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": "   ",
        "columnNameList": ["A"],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "tableNameは1文字以上で入力してください。" in response_data["message"]
    )


def test_descriptive_statistics_tab_only_column_name(client, tables_store):
    """columnNameListの要素がタブのみの場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["\t"],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"


def test_descriptive_statistics_missing_table_name(client, tables_store):
    """tableNameが欠損している場合はVALIDATION_ERRORになる"""
    payload = {"columnNameList": ["A"], "statistics": [_STAT_MEAN]}
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert "tableNameは必須です。" in response_data["message"]


def test_descriptive_statistics_missing_column_name_list(client, tables_store):
    """columnNameListが欠損している場合はVALIDATION_ERRORになる"""
    payload = {"tableName": _TABLE_NUMERIC, "statistics": [_STAT_MEAN]}
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert "columnNameListは必須です。" in response_data["message"]


def test_descriptive_statistics_missing_statistics(client, tables_store):
    """statisticsが欠損している場合はVALIDATION_ERRORになる"""
    payload = {"tableName": _TABLE_NUMERIC, "columnNameList": ["A"]}
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert "statisticsは必須です。" in response_data["message"]
