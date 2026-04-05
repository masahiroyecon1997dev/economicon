"""信頼区間 POST → GET 結合テスト

POST で得た resultId を使い、GET /api/analysis/results/{resultId} で
データ取得・型・フィールド存在を検証する。
数値精度の検証は test_confidence_interval.py で行う。
"""

import numpy as np
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

_TABLE_NAME = "CIResultTestTable"
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

URL_CI = "/api/statistics/confidence-interval"
URL_RESULTS = "/api/analysis/results"


# -----------------------------------------------------------
# フィクスチャ
# -----------------------------------------------------------


@pytest.fixture
def client():
    """TestClient のフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStore のフィクスチャ"""
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
        }
    )
    manager.store_table(_TABLE_NAME, df)

    yield manager
    manager.clear_tables()
    AnalysisResultStore().clear_all()


# -----------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------


def _post_ci(client: TestClient, statistic_type: str, level: float) -> str:
    """CI を POST して resultId を返す"""
    col = "binary_col" if statistic_type == _STAT_PROPORTION else "normal_col"
    resp = client.post(
        URL_CI,
        json={
            "tableName": _TABLE_NAME,
            "columnName": col,
            "confidenceLevel": level,
            "statisticType": statistic_type,
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["result"]["resultId"]


def _get_result_data(client: TestClient, result_id: str) -> dict:
    """GET /api/analysis/results/{result_id} で resultData を返す"""
    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["result"]["resultData"]


# -----------------------------------------------------------
# resultId の GET 取得テスト
# -----------------------------------------------------------


def test_ci_result_retrievable(client, tables_store):
    """POST で得た resultId を使って GET でデータを取得できる"""
    result_id = _post_ci(client, _STAT_MEAN, _CI_LEVEL_95)
    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["code"] == "OK"


def test_ci_result_type_is_confidence_interval(client, tables_store):
    """GET レスポンスの resultType が 'confidence_interval' である"""
    result_id = _post_ci(client, _STAT_MEAN, _CI_LEVEL_95)
    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.json()["result"]["resultType"] == "confidence_interval"


def test_ci_result_data_structure(client, tables_store):
    """GET の resultData に必須フィールドが全て含まれる"""
    result_id = _post_ci(client, _STAT_MEAN, _CI_LEVEL_95)
    rd = _get_result_data(client, result_id)

    for field in (
        "tableName",
        "columnName",
        "statistic",
        "confidenceInterval",
        "confidenceLevel",
    ):
        assert field in rd, f"resultData に '{field}' が存在しない"

    assert "type" in rd["statistic"]
    assert "value" in rd["statistic"]
    assert "lower" in rd["confidenceInterval"]
    assert "upper" in rd["confidenceInterval"]
