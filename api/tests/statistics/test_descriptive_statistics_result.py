"""記述統計 POST → GET 結合テスト

POST で得た resultId を使い、GET /api/analysis/results/{resultId} で
データ取得・型・フィールド存在を検証する。
数値精度の検証は test_descriptive_statistics.py で行う。
"""

from fastapi import status
from fastapi.testclient import TestClient

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE_NUMERIC = "DSResultTableNumeric"
_TABLE_STRING = "DSResultTableString"

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

URL_DS = "/api/statistics/descriptive"
URL_RESULTS = "/api/analysis/results"


# -----------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------


def _post_ds(
    client: TestClient,
    table_name: str,
    columns: list[str],
    statistics: list[str],
) -> str:
    """記述統計を POST して resultId を返す"""
    resp = client.post(
        URL_DS,
        json={
            "tableName": table_name,
            "columnNameList": columns,
            "statistics": statistics,
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


def test_ds_result_retrievable(client, tables_store):
    """POST で得た resultId を使って GET でデータを取得できる"""
    result_id = _post_ds(client, _TABLE_NUMERIC, ["A"], [_STAT_MEAN])
    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["code"] == "OK"


def test_ds_result_type(client, tables_store):
    """GET レスポンスの resultType が 'descriptive_statistics' である"""
    result_id = _post_ds(client, _TABLE_NUMERIC, ["A"], [_STAT_MEAN])
    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.json()["result"]["resultType"] == "descriptive_statistics"


def test_ds_result_data_structure(client, tables_store):
    """GET の resultData に tableName と statistics が含まれる"""
    result_id = _post_ds(client, _TABLE_NUMERIC, ["A"], [_STAT_MEAN])
    rd = _get_result_data(client, result_id)

    assert "tableName" in rd
    assert "statistics" in rd
    assert rd["tableName"] == _TABLE_NUMERIC
    assert "A" in rd["statistics"]
