"""信頼区間計算 POST エンドポイントのテスト"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.statistics.conftest import load_statistics_gold_case

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE_NAME = "ConfidenceTestTable"
_TEXT_TABLE = "TextTable"
_EMPTY_TABLE = "EmptyTable"
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
    """平均値 CI の数値が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_MEAN,
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case("confidence_interval", "ci_mean_95")

    ci = rd["confidenceInterval"]
    assert rd["statistic"]["type"] == gold["statistic"]["type"]
    assert rd["statistic"]["value"] == pytest.approx(
        gold["statistic"]["value"], abs=1e-8
    )
    assert ci["lower"] == pytest.approx(
        gold["confidence_interval"]["lower"], abs=1e-8
    )
    assert ci["upper"] == pytest.approx(
        gold["confidence_interval"]["upper"], abs=1e-8
    )


def test_confidence_interval_median_properties(client, tables_store):
    """中央値 CI の数値が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_90,
        "statisticType": _STAT_MEDIAN,
        "bootstrapNResamples": 10000,
        "bootstrapSeed": 42,
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case("confidence_interval", "ci_median_90")

    ci = rd["confidenceInterval"]
    assert ci["lower"] < ci["upper"]
    assert ci["lower"] == pytest.approx(
        gold["confidence_interval"]["lower"], abs=1e-8
    )
    assert ci["upper"] == pytest.approx(
        gold["confidence_interval"]["upper"], abs=1e-8
    )
    assert ci["lower"] <= gold["statistic"]["value"] <= ci["upper"]
    assert rd["statistic"]["value"] == pytest.approx(
        gold["statistic"]["value"], abs=1e-8
    )


def test_confidence_interval_proportion_numerical(client, tables_store):
    """比率 CI の数値が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "binary_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_PROPORTION,
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case("confidence_interval", "ci_proportion_95")

    ci = rd["confidenceInterval"]
    assert rd["statistic"]["value"] == pytest.approx(
        gold["statistic"]["value"], abs=1e-8
    )
    assert ci["lower"] == pytest.approx(
        gold["confidence_interval"]["lower"], abs=1e-8
    )
    assert ci["upper"] == pytest.approx(
        gold["confidence_interval"]["upper"], abs=1e-8
    )


def test_confidence_interval_variance_numerical(client, tables_store):
    """分散 CI の数値が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_VARIANCE,
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case("confidence_interval", "ci_variance_95")

    ci = rd["confidenceInterval"]
    assert rd["statistic"]["value"] == pytest.approx(
        gold["statistic"]["value"], abs=1e-8
    )
    assert ci["lower"] == pytest.approx(
        gold["confidence_interval"]["lower"], abs=1e-8
    )
    assert ci["upper"] == pytest.approx(
        gold["confidence_interval"]["upper"], abs=1e-8
    )


def test_confidence_interval_std_numerical(client, tables_store):
    """標準偏差 CI の数値が gold JSON と一致する"""
    payload = {
        "tableName": _TABLE_NAME,
        "columnName": "normal_col",
        "confidenceLevel": _CI_LEVEL_95,
        "statisticType": _STAT_STD,
    }
    rd = _get_result_data(client, payload)
    gold = load_statistics_gold_case("confidence_interval", "ci_std_95")

    ci = rd["confidenceInterval"]
    assert rd["statistic"]["value"] == pytest.approx(
        gold["statistic"]["value"], abs=1e-8
    )
    assert ci["lower"] == pytest.approx(
        gold["confidence_interval"]["lower"], abs=1e-8
    )
    assert ci["upper"] == pytest.approx(
        gold["confidence_interval"]["upper"], abs=1e-8
    )


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
