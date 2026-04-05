"""信頼区間計算 POST エンドポイントのテスト"""

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
# ヘルパー
# -----------------------------------------------------------


def _get_result_data(client: TestClient, payload: dict) -> dict:
    """POST して AnalysisResultStore から result_data を直接取得"""
    resp = client.post(URL, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


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
    """平均値の信頼区間計算で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_confidence_interval_median_success(client, tables_store):
    """中央値の信頼区間計算で resultId を含むレスポンスが返る"""
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
    assert "resultId" in result
    assert len(result["resultId"]) > 0


def test_confidence_interval_proportion_success(client, tables_store):
    """比率の信頼区間計算で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_confidence_interval_variance_success(client, tables_store):
    """分散の信頼区間計算で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_confidence_interval_std_success(client, tables_store):
    """標準偏差の信頼区間計算で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_confidence_interval_response_structure(client, tables_store):
    """レスポンスには resultId のみが含まれる"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)


# -----------------------------------------------------------
# 数値精度テスト（AnalysisResultStore 直接参照）
# -----------------------------------------------------------


def test_confidence_interval_mean_numerical(client, tables_store):
    """平均値 CI の数値が scipy.stats.t.interval と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    rd = _get_result_data(client, payload)

    np.random.seed(_SEED)
    data = np.random.normal(50, 10, _N_SAMPLES)
    exp_lower, exp_upper = spstats.t.interval(
        _CI_LEVEL_95,
        df=_N_SAMPLES - 1,
        loc=float(np.mean(data)),
        scale=float(spstats.sem(data)),
    )
    ci = rd["confidenceInterval"]
    assert ci["lower"] == pytest.approx(exp_lower, abs=1e-8)
    assert ci["upper"] == pytest.approx(exp_upper, abs=1e-8)
    assert rd["statistic"]["value"] == pytest.approx(
        float(np.mean(data)), abs=1e-8
    )


def test_confidence_interval_median_properties(client, tables_store):
    """中央値 CI がブートストラップ法の統計的性質を満たす"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_90,
        "statisticType": _STAT_MEDIAN,
    }
    rd = _get_result_data(client, payload)

    np.random.seed(_SEED)
    data = np.random.normal(50, 10, _N_SAMPLES)
    expected_median = float(np.median(data))

    ci = rd["confidenceInterval"]
    assert ci["lower"] < ci["upper"]
    assert ci["lower"] <= expected_median <= ci["upper"]
    assert rd["statistic"]["value"] == pytest.approx(expected_median, abs=1e-8)


def test_confidence_interval_proportion_numerical(client, tables_store):
    """比率 CI の数値が statsmodels Wilson score と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "binary_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_PROPORTION,
    }
    rd = _get_result_data(client, payload)

    np.random.seed(_SEED)
    _dummy = np.random.normal(50, 10, _N_SAMPLES)  # normal_col 分の消費
    binary_data = np.random.binomial(1, 0.3, _N_SAMPLES)
    n_successes = int(np.sum(binary_data))
    exp_lower, exp_upper = proportion_confint(
        n_successes,
        _N_SAMPLES,
        alpha=1 - _CI_LEVEL_95,
        method="wilson",
    )
    ci = rd["confidenceInterval"]
    assert ci["lower"] == pytest.approx(
        float(cast(float, exp_lower)), abs=1e-8
    )
    assert ci["upper"] == pytest.approx(
        float(cast(float, exp_upper)), abs=1e-8
    )


def test_confidence_interval_variance_numerical(client, tables_store):
    """分散 CI の数値がカイ二乗分布と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_VARIANCE,
    }
    rd = _get_result_data(client, payload)

    np.random.seed(_SEED)
    data = np.random.normal(50, 10, _N_SAMPLES)
    var_val = float(np.var(data, ddof=1))
    alpha = 1 - _CI_LEVEL_95
    chi2_lo = spstats.chi2.ppf(alpha / 2, df=_N_SAMPLES - 1)
    chi2_hi = spstats.chi2.ppf(1 - alpha / 2, df=_N_SAMPLES - 1)
    exp_lower = (_N_SAMPLES - 1) * var_val / chi2_hi
    exp_upper = (_N_SAMPLES - 1) * var_val / chi2_lo
    ci = rd["confidenceInterval"]
    assert ci["lower"] == pytest.approx(exp_lower, abs=1e-8)
    assert ci["upper"] == pytest.approx(exp_upper, abs=1e-8)
    assert rd["statistic"]["value"] == pytest.approx(var_val, abs=1e-8)


def test_confidence_interval_std_numerical(client, tables_store):
    """標準偏差 CI の数値が分散 CI の平方根と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_STD,
    }
    rd = _get_result_data(client, payload)

    np.random.seed(_SEED)
    data = np.random.normal(50, 10, _N_SAMPLES)
    var_val = float(np.var(data, ddof=1))
    alpha = 1 - _CI_LEVEL_95
    chi2_lo = spstats.chi2.ppf(alpha / 2, df=_N_SAMPLES - 1)
    chi2_hi = spstats.chi2.ppf(1 - alpha / 2, df=_N_SAMPLES - 1)
    exp_lower = float(np.sqrt((_N_SAMPLES - 1) * var_val / chi2_hi))
    exp_upper = float(np.sqrt((_N_SAMPLES - 1) * var_val / chi2_lo))
    ci = rd["confidenceInterval"]
    assert ci["lower"] == pytest.approx(exp_lower, abs=1e-8)
    assert ci["upper"] == pytest.approx(exp_upper, abs=1e-8)


def test_confidence_interval_levels_width_ordering(client, tables_store):
    """信頼度レベルが高いほど CI 幅が広くなる（90 < 95 < 99）"""
    widths: dict[float, float] = {}
    for level in [_CI_LEVEL_90, _CI_LEVEL_95, _CI_LEVEL_99]:
        payload = {
            "tableName": _TABLE_NAME,
            "columnName": "normal_col",
            "confidenceLevel": level,
            "statisticType": _STAT_MEAN,
        }
        rd = _get_result_data(client, payload)
        ci = rd["confidenceInterval"]
        widths[level] = ci["upper"] - ci["lower"]

    assert widths[_CI_LEVEL_90] < widths[_CI_LEVEL_95] < widths[_CI_LEVEL_99]


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
