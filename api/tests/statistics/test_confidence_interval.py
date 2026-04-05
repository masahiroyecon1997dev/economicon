"""信頼区間計算APIのテスト"""

from typing import cast

import numpy as np
import polars as pl
import pytest
import scipy.stats as spstats
from fastapi import status
from fastapi.testclient import TestClient
from statsmodels.stats.proportion import proportion_confint

from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE_NAME = "ConfidenceTestTable"
_TEXT_TABLE = "TextTable"
_EMPTY_TABLE = "EmptyTable"
_N_SAMPLES = 100
_SEED = 42
_CI_LEVEL_90 = 0.90
_CI_LEVEL_95 = 0.95
_CI_LEVEL_99 = 0.99

_STAT_MEAN = "mean"
_STAT_MEDIAN = "median"
_STAT_PROPORTION = "proportion"
_STAT_VARIANCE = "variance"
_STAT_STD = "standard_deviation"

_STATISTIC_TYPE_ERROR = (
    "statisticTypeは次のいずれかである必要があります: "
    "mean, median, proportion, variance, standard_deviation"
)

URL = "/api/statistics/confidence-interval"


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

    np.random.seed(_SEED)
    normal_data = np.random.normal(50, 10, _N_SAMPLES)
    binary_data = np.random.binomial(1, 0.3, _N_SAMPLES)

    df = pl.DataFrame(
        {
            "normal_col": normal_data,
            "binary_col": binary_data.astype(float),
            "id": list(range(_N_SAMPLES)),
        }
    )
    manager.store_table(_TABLE_NAME, df)

    df_with_text = pl.DataFrame(
        {
            "numeric_col": [1.0, 2.0, 3.0, 4.0],
            "text_col": ["a", "b", "c", "d"],
        }
    )
    manager.store_table(_TEXT_TABLE, df_with_text)

    df_empty = pl.DataFrame(
        {"empty_col": [None, None, None]},
        schema={"empty_col": pl.Float64},
    )
    manager.store_table(_EMPTY_TABLE, df_empty)

    yield manager
    manager.clear_tables()
    AnalysisResultStore().clear_all()


# -----------------------------------------------------------
# 成功ケース
# -----------------------------------------------------------


def test_confidence_interval_mean_success(client, tables_store):
    """平均値の信頼区間計算が正常に動作する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["tableName"] == _TABLE_NAME
    assert result["columnName"] == "normal_col"
    assert result["confidenceLevel"] == _CI_LEVEL_95
    assert result["statistic"]["type"] == _STAT_MEAN
    assert isinstance(result["statistic"]["value"], float)

    ci = result["confidenceInterval"]
    assert "lower" in ci
    assert "upper" in ci
    assert ci["lower"] < ci["upper"]
    assert "resultId" in result
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_confidence_interval_mean_numerical(client, tables_store):
    """平均値CIの数値をscipy.stats.t.intervalと照合"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    # フィクスチャと同じシード・順序でデータを再現
    np.random.seed(_SEED)
    normal_data = np.random.normal(50, 10, _N_SAMPLES)

    expected_lower, expected_upper = spstats.t.interval(
        _CI_LEVEL_95,
        df=_N_SAMPLES - 1,
        loc=float(np.mean(normal_data)),
        scale=float(spstats.sem(normal_data)),
    )

    ci = result["confidenceInterval"]
    assert ci["lower"] == pytest.approx(expected_lower, abs=1e-6)
    assert ci["upper"] == pytest.approx(expected_upper, abs=1e-6)
    assert result["statistic"]["value"] == pytest.approx(
        float(np.mean(normal_data)), abs=1e-6
    )


def test_confidence_interval_median_success(client, tables_store):
    """中央値の信頼区間計算が正常に動作する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_90,
        "statisticType": _STAT_MEDIAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["statistic"]["type"] == _STAT_MEDIAN
    assert result["confidenceLevel"] == _CI_LEVEL_90
    assert (
        result["confidenceInterval"]["lower"]
        < result["confidenceInterval"]["upper"]
    )


def test_confidence_interval_median_numerical(client, tables_store):
    """中央値CIがBootstrap法の統計的性質を満たすことを検証

    シード固定非依存で以下の性質を確認:
      1. CI が非退化 (lower < upper)
      2. サンプル中央値が CI 内に収まる
      3. N(50, 10) データに対して妥当な範囲
      4. 点推定値が正確なサンプル中央値と一致
    """
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_90,
        "statisticType": _STAT_MEDIAN,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    # フィクスチャと同じシード・順序でデータを再現して期待中央値を算出
    np.random.seed(_SEED)
    normal_data = np.random.normal(50, 10, _N_SAMPLES)
    expected_median = float(np.median(normal_data))

    ci = result["confidenceInterval"]
    # 1. 区間の非退化性
    assert ci["lower"] < ci["upper"]
    # 2. サンプル中央値が CI 内に存在する
    assert ci["lower"] <= expected_median <= ci["upper"]
    # 3. N(50, 10), n=100 のデータに対して合理的な範囲（5σ 超えは実質不可能）
    min_lower = 30.0
    max_lower = 60.0
    min_upper = 40.0
    max_upper = 70.0
    assert min_lower < ci["lower"] < max_lower
    assert min_upper < ci["upper"] < max_upper
    # 4. 点推定値の正確性（Bootstrap と無関係に決定論的）
    assert result["statistic"]["value"] == pytest.approx(
        expected_median, abs=1e-6
    )


def test_confidence_interval_proportion_success(client, tables_store):
    """比率の信頼区間計算が正常に動作する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "binary_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_PROPORTION,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["statistic"]["type"] == _STAT_PROPORTION
    proportion_value = result["statistic"]["value"]
    assert 0.0 <= proportion_value <= 1.0

    ci = result["confidenceInterval"]
    assert 0.0 <= ci["lower"] <= ci["upper"] <= 1.0


def test_confidence_interval_proportion_numerical(client, tables_store):
    """比率CIの数値をstatsmodels Wilson scoreと照合"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "binary_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_PROPORTION,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    # フィクスチャと同じシード・順序でデータを再現
    np.random.seed(_SEED)
    _dummy = np.random.normal(50, 10, _N_SAMPLES)  # normal_col分のRNG消費
    binary_data = np.random.binomial(1, 0.3, _N_SAMPLES)
    n_successes = int(np.sum(binary_data))

    expected_lower, expected_upper = proportion_confint(
        n_successes,
        _N_SAMPLES,
        alpha=1 - _CI_LEVEL_95,
        method="wilson",
    )

    ci = result["confidenceInterval"]
    assert ci["lower"] == pytest.approx(cast(float, expected_lower), abs=1e-6)
    assert ci["upper"] == pytest.approx(cast(float, expected_upper), abs=1e-6)


def test_confidence_interval_variance_success(client, tables_store):
    """分散の信頼区間計算が正常に動作する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_VARIANCE,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["statistic"]["type"] == _STAT_VARIANCE
    assert result["statistic"]["value"] > 0
    assert (
        result["confidenceInterval"]["lower"]
        < result["confidenceInterval"]["upper"]
    )


def test_confidence_interval_variance_numerical(client, tables_store):
    """分散CIの数値をカイ二乗分布と照合"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_VARIANCE,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    np.random.seed(_SEED)
    normal_data = np.random.normal(50, 10, _N_SAMPLES)
    variance_val = float(np.var(normal_data, ddof=1))
    alpha = 1 - _CI_LEVEL_95
    chi2_lower = spstats.chi2.ppf(alpha / 2, df=_N_SAMPLES - 1)
    chi2_upper = spstats.chi2.ppf(1 - alpha / 2, df=_N_SAMPLES - 1)
    expected_lower = (_N_SAMPLES - 1) * variance_val / chi2_upper
    expected_upper = (_N_SAMPLES - 1) * variance_val / chi2_lower

    ci = result["confidenceInterval"]
    assert ci["lower"] == pytest.approx(expected_lower, abs=1e-6)
    assert ci["upper"] == pytest.approx(expected_upper, abs=1e-6)
    assert result["statistic"]["value"] == pytest.approx(
        variance_val, abs=1e-6
    )


def test_confidence_interval_std_success(client, tables_store):
    """標準偏差の信頼区間計算が正常に動作する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_STD,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["statistic"]["type"] == _STAT_STD
    assert result["statistic"]["value"] > 0
    assert (
        result["confidenceInterval"]["lower"]
        < result["confidenceInterval"]["upper"]
    )


def test_confidence_interval_std_numerical(client, tables_store):
    """標準偏差CIの数値を分散CIの平方根と照合"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_STD,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    np.random.seed(_SEED)
    normal_data = np.random.normal(50, 10, _N_SAMPLES)
    variance_val = float(np.var(normal_data, ddof=1))
    alpha = 1 - _CI_LEVEL_95
    chi2_lower = spstats.chi2.ppf(alpha / 2, df=_N_SAMPLES - 1)
    chi2_upper = spstats.chi2.ppf(1 - alpha / 2, df=_N_SAMPLES - 1)
    var_lower = (_N_SAMPLES - 1) * variance_val / chi2_upper
    var_upper = (_N_SAMPLES - 1) * variance_val / chi2_lower
    expected_lower = float(np.sqrt(var_lower))
    expected_upper = float(np.sqrt(var_upper))

    ci = result["confidenceInterval"]
    assert ci["lower"] == pytest.approx(expected_lower, abs=1e-6)
    assert ci["upper"] == pytest.approx(expected_upper, abs=1e-6)


def test_confidence_interval_different_levels(client, tables_store):
    """信頼度レベルが高いほど区間が広くなる"""
    widths = {}
    for level in [_CI_LEVEL_90, _CI_LEVEL_95, _CI_LEVEL_99]:
        payload = {
            "tableName": _TABLE_NAME,
            "columnName": "normal_col",
            "confidenceLevel": level,
            "statisticType": _STAT_MEAN,
        }
        response = client.post(URL, json=payload)
        assert response.status_code == status.HTTP_200_OK
        ci = response.json()["result"]["confidenceInterval"]
        widths[level] = ci["upper"] - ci["lower"]

    assert widths[_CI_LEVEL_90] < widths[_CI_LEVEL_95] < widths[_CI_LEVEL_99]


def test_confidence_interval_response_structure(client, tables_store):
    """レスポンスのJSON構造が仕様通りである"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    required_fields = [
        "tableName",
        "columnName",
        "statistic",
        "confidenceInterval",
        "confidenceLevel",
    ]
    for field in required_fields:
        assert field in result

    assert "type" in result["statistic"]
    assert "value" in result["statistic"]
    assert "lower" in result["confidenceInterval"]
    assert "upper" in result["confidenceInterval"]


# -----------------------------------------------------------
# 400 エラーケース
# -----------------------------------------------------------


def test_confidence_interval_invalid_table(client, tables_store):
    """存在しないテーブル名でDATA_NOT_FOUNDエラーが返される"""
    payload = {
        "tableName": "NonExistentTable",
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DATA_NOT_FOUND"
    assert (
        response_data["message"]
        == "tableName 'NonExistentTable'は存在しません。"
    )


def test_confidence_interval_invalid_column(client, tables_store):
    """存在しない列名でDATA_NOT_FOUNDエラーが返される"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "nonexistent_column",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DATA_NOT_FOUND"
    assert (
        response_data["message"]
        == "columnName 'nonexistent_column'は存在しません。"
    )


def test_confidence_interval_proportion_invalid_data(client, tables_store):
    """比率計算で0,1以外のデータがある場合INVALID_PROPORTION_DATAが返される"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",  # 連続値列
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_PROPORTION,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "INVALID_PROPORTION_DATA"
    assert (
        "データには0と1の値のみが含まれる必要があります"
        in response_data["message"]
    )


def test_confidence_interval_empty_data(client, tables_store):
    """空データの場合CONFIDENCE_INTERVAL_ERRORが返される"""
    payload = {
        "tableName": _EMPTY_TABLE,
        "columnName": "empty_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "CONFIDENCE_INTERVAL_ERROR"
    assert "カラムに有効なデータが含まれていません" in response_data["message"]


# -----------------------------------------------------------
# 422 バリデーションエラーケース
# -----------------------------------------------------------


def test_confidence_interval_missing_table_name(client, tables_store):
    """tableNameが欠損している場合はVALIDATION_ERRORになる"""
    payload = {
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert "tableNameは必須です。" in response_data["message"]


def test_confidence_interval_missing_column_name(client, tables_store):
    """columnNameが欠損している場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert "columnNameは必須です。" in response_data["message"]


def test_confidence_interval_missing_confidence_level(client, tables_store):
    """confidenceLevelが欠損している場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert "confidenceLevelは必須です。" in response_data["message"]


def test_confidence_interval_missing_statistic_type(client, tables_store):
    """statisticTypeが欠損している場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert "statisticTypeは必須です。" in response_data["message"]


def test_confidence_interval_empty_table_name(client, tables_store):
    """tableNameが空文字列の場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": "",
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "tableNameは1文字以上で入力してください。" in response_data["message"]
    )


def test_confidence_interval_empty_column_name(client, tables_store):
    """columnNameが空文字列の場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "columnNameは1文字以上で入力してください。" in response_data["message"]
    )


def test_confidence_interval_whitespace_only_table_name(client, tables_store):
    """tableNameがスペースのみの場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": "   ",
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "tableNameは1文字以上で入力してください。" in response_data["message"]
    )


def test_confidence_interval_tab_only_column_name(client, tables_store):
    """columnNameがタブのみの場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "\t",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "columnNameは1文字以上で入力してください。" in response_data["message"]
    )


def test_confidence_interval_empty_statistic_type(client, tables_store):
    """statisticTypeが空文字列の場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": "",
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert _STATISTIC_TYPE_ERROR in response_data["message"]


def test_confidence_interval_invalid_statistic_type(client, tables_store):
    """不正なstatisticType値の場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": "invalid_stat",
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert _STATISTIC_TYPE_ERROR in response_data["message"]


def test_confidence_interval_old_std_value_is_invalid(client, tables_store):
    """旧値'std'はVALIDATION_ERRORになる（正しくは'standard_deviation'）"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": "std",
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert _STATISTIC_TYPE_ERROR in response_data["message"]


def test_confidence_interval_confidence_level_zero(client, tables_store):
    """confidenceLevelが0.0の場合はgt=0.0違反でVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": 0.0,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "confidenceLevelは0.0より大きい値で入力してください。"
        in response_data["message"]
    )


def test_confidence_interval_confidence_level_negative(client, tables_store):
    """confidenceLevelが負の場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": -0.1,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "confidenceLevelは0.0より大きい値で入力してください。"
        in response_data["message"]
    )


def test_confidence_interval_confidence_level_one(client, tables_store):
    """confidenceLevelが1.0の場合はlt=1.0違反でVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": 1.0,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "confidenceLevelは1.0未満で入力してください。"
        in response_data["message"]
    )


def test_confidence_interval_confidence_level_over_one(client, tables_store):
    """confidenceLevelが1.0超の場合はVALIDATION_ERRORになる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": 1.5,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    assert (
        "confidenceLevelは1.0未満で入力してください。"
        in response_data["message"]
    )
