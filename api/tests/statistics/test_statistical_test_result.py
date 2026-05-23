"""統計的検定 POST → GET 結合テスト

POST で得た resultId を使い、GET /api/analysis/results/{resultId} で
データ取得・型・フィールド存在を検証する。
数値精度の検証は test_statistical_test.py で行う。
"""

from fastapi import status
from fastapi.testclient import TestClient

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE_A = "STResultTableA"
_TABLE_B = "STResultTableB"
_TABLE_C = "STResultTableC"
_COL = "value"
URL_TEST = "/api/statistics/test"
URL_RESULTS = "/api/analysis/results"
# -----------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------


def _samples(*pairs: tuple[str, str]) -> list[dict[str, str]]:
    """サンプルリストを生成するヘルパー"""
    return [{"tableName": t, "columnName": c} for t, c in pairs]


def _post_test(client: TestClient, payload: dict) -> str:
    """統計検定を POST して resultId を返す"""
    resp = client.post(URL_TEST, json=payload)
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


def test_st_result_retrievable(client, tables_store):
    """POST で得た resultId を使って GET でデータを取得できる"""
    result_id = _post_test(
        client,
        {
            "testType": "t-test",
            "samples": _samples((_TABLE_A, _COL)),
            "options": {"mu": 50.0},
        },
    )
    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["code"] == "OK"


def test_st_result_type(client, tables_store):
    """GET レスポンスの resultType が 'statistical_test' である"""
    result_id = _post_test(
        client,
        {
            "testType": "t-test",
            "samples": _samples((_TABLE_A, _COL)),
            "options": {"mu": 50.0},
        },
    )
    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.json()["result"]["resultType"] == "statistical_test"


def test_st_result_data_structure_ttest(client, tables_store):
    """t-test の resultData に必須フィールドが全て含まれる"""
    result_id = _post_test(
        client,
        {
            "testType": "t-test",
            "samples": _samples((_TABLE_A, _COL)),
            "options": {"mu": 50.0},
        },
    )
    rd = _get_result_data(client, result_id)

    for field in (
        "statistic",
        "pValue",
        "df",
        "confidenceInterval",
        "effectSize",
    ):
        assert field in rd, f"resultData に '{field}' が存在しない"

    assert rd["confidenceInterval"] is not None
    assert "lower" in rd["confidenceInterval"]
    assert "upper" in rd["confidenceInterval"]


def test_st_result_data_structure_ftest(client, tables_store):
    """f-test の resultData に df2 が含まれ CI は None である"""
    result_id = _post_test(
        client,
        {
            "testType": "f-test",
            "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        },
    )
    rd = _get_result_data(client, result_id)

    assert "df2" in rd
    assert rd["confidenceInterval"] is None
