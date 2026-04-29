"""記述統計計算APIのテスト"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.statistics.conftest import load_statistics_gold_case

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
# ヘルパー
# -----------------------------------------------------------


def _get_result_data(client: TestClient, payload: dict) -> dict:
    """POST して AnalysisResultStore から result_data を直接取得"""
    resp = client.post(URL, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 成功ケース
# -----------------------------------------------------------


def test_descriptive_statistics_success_numeric(client, tables_store):
    """数値データに対する記述統計の計算で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_success_all_stats(client, tables_store):
    """全統計量を複数列で計算し resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_success_string_mode(client, tables_store):
    """文字列データに対するmode計算で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_count_no_nulls(client, tables_store):
    """nullなしデータでcount/null_count/null_ratioを含む resultId が返る"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_COUNT, _STAT_NULL_COUNT, _STAT_NULL_RATIO],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_count_with_nulls(
    client, tables_store_with_nulls
):
    """null含有データで resultId を含むレスポンスが返る"""
    payload = {
        "tableName": "TestNulls",
        "columnNameList": ["X"],
        "statistics": [_STAT_COUNT, _STAT_NULL_COUNT, _STAT_NULL_RATIO],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_population_variance_numerical(
    client, tables_store
):
    """population_variance を含む resultId が返る"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_VARIANCE, _STAT_POP_VARIANCE],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_null_stats_on_string_column(
    client, tables_store
):
    """count/null_count/null_ratio は文字列列からも resultId が返る"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [_STAT_COUNT, _STAT_NULL_COUNT, _STAT_NULL_RATIO],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_pop_variance_on_string_column(
    client, tables_store
):
    """population_varianceはNoneを含む resultId が返る"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [_STAT_POP_VARIANCE],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_string_numeric_stats(client, tables_store):
    """文字列データに対して数値専用統計を要求しても resultId が返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_descriptive_statistics_response_structure(client, tables_store):
    """レスポンスには resultId のみが含まれる"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_MEAN],
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)


# -----------------------------------------------------------
# 数値精度テスト（AnalysisResultStore 直接参照）
# -----------------------------------------------------------


def test_descriptive_statistics_mean_median_variance_std_numerical(
    client, tables_store
):
    """A=[1..5] の平均・中央値・分散・標準偏差が gold JSON と一致する"""
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
    rd = _get_result_data(client, payload)
    stats_a = rd["statistics"]["A"]
    gold = load_statistics_gold_case("descriptive_statistics", "ds_A_basic")
    expected = gold["expected"]["statistics"]["A"]

    assert stats_a[_STAT_MEAN] == pytest.approx(expected[_STAT_MEAN], abs=1e-8)
    assert stats_a[_STAT_MEDIAN] == pytest.approx(
        expected[_STAT_MEDIAN], abs=1e-8
    )
    assert stats_a[_STAT_VARIANCE] == pytest.approx(
        expected[_STAT_VARIANCE], abs=1e-8
    )
    assert stats_a[_STAT_STD_DEV] == pytest.approx(
        expected[_STAT_STD_DEV], abs=1e-8
    )


def test_descriptive_statistics_range_iqr_numerical(client, tables_store):
    """A=[1..5] の range と IQR が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_RANGE, _STAT_IQR],
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case(
        "descriptive_statistics", "ds_A_range_iqr"
    )
    expected = gold["expected"]["statistics"]["A"]
    stats_a = rd["statistics"]["A"]
    assert stats_a[_STAT_RANGE] == pytest.approx(
        expected[_STAT_RANGE], abs=1e-8
    )
    assert stats_a[_STAT_IQR] == pytest.approx(expected[_STAT_IQR], abs=1e-8)


def test_descriptive_statistics_population_variance_distinction(
    client, tables_store
):
    """A=[1..5] で不偏分散と母分散が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_VARIANCE, _STAT_POP_VARIANCE],
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case(
        "descriptive_statistics",
        "ds_A_variance_vs_population",
    )
    expected = gold["expected"]["statistics"]["A"]
    stats_a = rd["statistics"]["A"]

    assert stats_a[_STAT_VARIANCE] == pytest.approx(
        expected[_STAT_VARIANCE], abs=1e-8
    )
    assert stats_a[_STAT_POP_VARIANCE] == pytest.approx(
        expected[_STAT_POP_VARIANCE], abs=1e-8
    )


def test_descriptive_statistics_string_mode_result(client, tables_store):
    """文字列列の最頻値が Alice または Bob である"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [_STAT_MODE],
    }
    rd = _get_result_data(client, payload)
    assert rd["statistics"]["name"][_STAT_MODE] in ["Alice", "Bob"]


def test_descriptive_statistics_count_null_result(client, tables_store):
    """count/null_count/null_ratio が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A"],
        "statistics": [_STAT_COUNT, _STAT_NULL_COUNT, _STAT_NULL_RATIO],
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case("descriptive_statistics", "ds_A_counts")
    expected = gold["expected"]["statistics"]["A"]
    stats_a = rd["statistics"]["A"]

    assert stats_a[_STAT_COUNT] == expected[_STAT_COUNT]
    assert stats_a[_STAT_NULL_COUNT] == expected[_STAT_NULL_COUNT]
    assert stats_a[_STAT_NULL_RATIO] == pytest.approx(
        expected[_STAT_NULL_RATIO], abs=1e-8
    )


def test_descriptive_statistics_multi_column_numerical(client, tables_store):
    """A と B の平均と標準偏差が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NUMERIC,
        "columnNameList": ["A", "B"],
        "statistics": [_STAT_MEAN, _STAT_STD_DEV],
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case(
        "descriptive_statistics", "ds_AB_mean_std"
    )
    expected = gold["expected"]["statistics"]

    assert rd["statistics"]["A"][_STAT_MEAN] == pytest.approx(
        expected["A"][_STAT_MEAN], abs=1e-8
    )
    assert rd["statistics"]["B"][_STAT_MEAN] == pytest.approx(
        expected["B"][_STAT_MEAN], abs=1e-8
    )
    assert rd["statistics"]["A"][_STAT_STD_DEV] == pytest.approx(
        expected["A"][_STAT_STD_DEV], abs=1e-8
    )
    assert rd["statistics"]["B"][_STAT_STD_DEV] == pytest.approx(
        expected["B"][_STAT_STD_DEV], abs=1e-8
    )


def test_descriptive_statistics_string_numeric_stats_are_none(
    client, tables_store
):
    """文字列列に数値専用統計を要求した場合は None が返る"""
    payload = {
        "tableName": _TABLE_STRING,
        "columnNameList": ["name"],
        "statistics": [_STAT_MEAN, _STAT_VARIANCE],
    }
    rd = _get_result_data(client, payload)
    assert rd["statistics"]["name"][_STAT_MEAN] is None
    assert rd["statistics"]["name"][_STAT_VARIANCE] is None


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
