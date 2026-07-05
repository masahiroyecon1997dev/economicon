"""RDD 分析テスト

NOTE: rdrobust / rddensity は GPL ライセンスのため削除済み。
      API エンドポイントは 501 Not Implemented を返す。
      以下の既存テストはコメントアウト済み。
      compute_bins_data の単体テストのみ有効。
"""

# import json
# from pathlib import Path

import polars as pl

# import pytest
from fastapi import status

# from economicon.core.enums import ErrorCode
# from economicon.services.data.analysis_result_store import (
#     AnalysisResultStore,
# )
from economicon.services.rdd.fitters import compute_bins_data
from tests.rdd.conftest import (
    # TABLE_NO_LEFT,
    # TABLE_STRING,
    URL_RDD,
    RDDPayload,
)

# ベンチマークファイルパス（rdrobust 削除により未使用）
# _BENCH_PY_DIR = (
#     Path(__file__).resolve().parents[3]
#     / "test"
#     / "benchmarks"
#     / "python"
#     / "synthetic"
# )


# def _load_rdd_gold() -> dict:
#     """RDD gold JSON を読み込む"""
#     with (_BENCH_PY_DIR / "synthetic_rdd_gold.json").open(
#         encoding="utf-8"
#     ) as f:
#         return json.load(f)


# テスト用定数（rdrobust 依存のため未使用）
# _POLY_FIT_POINTS = 100
# _BW_TOLERANCE = 1e-6
# _PLACEBO_TOLERANCE = 1e-6
# _RDROBUST_ESTIMATE_TOLERANCE = 1e-4
# _MIN_PLACEBO_COUNT = 2
# _TEST_PLACEBO_LEFT = -0.5
# _TEST_PLACEBO_RIGHT = 0.5
_TEST_BINS_COUNT = 4

# -----------------------------------------------------------
# Not Implemented: エンドポイントが 501 を返すことを確認
# -----------------------------------------------------------


def test_rdd_returns_not_implemented(client, tables_store):
    resp = client.post(URL_RDD, json=RDDPayload().build())
    assert resp.status_code == status.HTTP_501_NOT_IMPLEMENTED
    data = resp.json()
    assert data["code"] == "NOT_IMPLEMENTED"


# -----------------------------------------------------------
# compute_bins_data 単体テスト（純粋 Polars / numpy: 引き続き有効）
# -----------------------------------------------------------


def test_rdd_bins_data_internal_bin_name_collision() -> None:
    """内部ビン列名が実列名と衝突しても集計できることを確認"""
    df_pl = pl.DataFrame(
        {
            "_bin": [-1.0, -0.5, 0.5, 1.0],
            "y": [1.0, 2.0, 3.0, 4.0],
        }
    )

    bins = compute_bins_data(
        df_pl,
        outcome_var="y",
        running_var="_bin",
        cutoff=0.0,
        n_bins=_TEST_BINS_COUNT,
    )

    assert len(bins) == _TEST_BINS_COUNT
    assert bins[0] == {"x": -1.0, "y": 1.0}
    assert bins[-1] == {"x": 1.0, "y": 4.0}


def test_rdd_bins_data_base_internal_name_collision() -> None:
    """内部基底名と衝突しても連番付き一時列名で集計できることを確認"""
    df_pl = pl.DataFrame(
        {
            "__rdd_internal_bin_index__": [-1.0, -0.5, 0.5, 1.0],
            "y": [1.0, 2.0, 3.0, 4.0],
        }
    )

    bins = compute_bins_data(
        df_pl,
        outcome_var="y",
        running_var="__rdd_internal_bin_index__",
        cutoff=0.0,
        n_bins=_TEST_BINS_COUNT,
    )

    assert len(bins) == _TEST_BINS_COUNT
    assert bins[1] == {"x": -0.5, "y": 2.0}
    assert bins[2] == {"x": 0.5, "y": 3.0}


# -----------------------------------------------------------
# 以下は rdrobust / rddensity 削除により全テストをコメントアウト
# -----------------------------------------------------------

# def _get_result_data(client, payload: dict) -> dict:
#     """POST → result_data を返すヘルパー"""
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_200_OK, resp.text
#     result_id = resp.json()["result"]["resultId"]
#     return AnalysisResultStore().get_result(result_id).result_data


# def test_rdd_basic_success(client, tables_store):
#     resp = client.post(URL_RDD, json=RDDPayload().build())
#     assert resp.status_code == status.HTTP_200_OK
#     data = resp.json()
#     assert data["code"] == "OK"
#     assert "resultId" in data["result"]


# def test_rdd_response_structure(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     assert "estimate" in rd
#     assert "bandwidth" in rd
#     assert "binsData" in rd
#     assert "polyFitData" in rd
#     assert "densityTest" in rd
#     assert "placeboTests" in rd


# def test_rdd_estimate_fields(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     est = rd["estimate"]
#     for key in (
#         "coef", "stdErr", "zStat", "pValue", "ciLower", "ciUpper",
#         "biasCorrectedCoef", "biasCorrectedCiLower", "biasCorrectedCiUpper",
#         "rho",
#     ):
#         assert key in est, f"estimate に '{key}' が存在しない"


# def test_rdd_bandwidth_fields(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     bw = rd["bandwidth"]
#     for key in (
#         "bwLeft", "bwRight", "bwBiasLeft", "bwBiasRight",
#         "nLeft", "nRight", "nTotal",
#     ):
#         assert key in bw, f"bandwidth に '{key}' が存在しない"


# def test_rdd_bandwidth_positive(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     bw = rd["bandwidth"]
#     assert bw["bwLeft"] > 0
#     assert bw["bwRight"] > 0
#     assert bw["bwBiasLeft"] > 0
#     assert bw["bwBiasRight"] > 0
#     assert bw["nLeft"] > 0
#     assert bw["nRight"] > 0
#     assert bw["nTotal"] > 0


# def test_rdd_bins_data_nonempty(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     assert len(rd["binsData"]) > 0
#     for b in rd["binsData"]:
#         assert "x" in b
#         assert "y" in b


# def test_rdd_poly_fit_nonempty(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     pf = rd["polyFitData"]
#     assert len(pf["left"]["x"]) == _POLY_FIT_POINTS
#     assert len(pf["left"]["y"]) == _POLY_FIT_POINTS
#     assert len(pf["right"]["x"]) == _POLY_FIT_POINTS
#     assert len(pf["right"]["y"]) == _POLY_FIT_POINTS


# def test_rdd_placebo_tests_auto_generated(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     assert len(rd["placeboTests"]) >= 1
#     for pt in rd["placeboTests"]:
#         for key in (
#             "cutoff", "coef", "stdErr", "pValue", "ciLower", "ciUpper",
#             "isSignificant",
#         ):
#             assert key in pt, f"placeboTests に '{key}' が存在しない"


# def test_rdd_density_test_fields(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     dt = rd["densityTest"]
#     if dt is not None:
#         assert "testStatistic" in dt
#         assert "pValue" in dt
#         assert "description" in dt


# def test_rdd_manual_bandwidth(client, tables_store):
#     h_val = 0.3
#     rd = _get_result_data(client, RDDPayload(h=h_val).build())
#     bw = rd["bandwidth"]
#     assert abs(bw["bwLeft"] - h_val) < _BW_TOLERANCE
#     assert abs(bw["bwRight"] - h_val) < _BW_TOLERANCE


# def test_rdd_effect_direction(client, tables_store):
#     rd = _get_result_data(client, RDDPayload().build())
#     assert rd["estimate"]["coef"] > 0


# def test_rdd_custom_placebo_cutoffs(client, tables_store):
#     rd = _get_result_data(
#         client,
#         RDDPayload(placebo_cutoffs=[_TEST_PLACEBO_LEFT, _TEST_PLACEBO_RIGHT]).build(), # noqa: E501
#     )
#     assert len(rd["placeboTests"]) == _MIN_PLACEBO_COUNT
#     cutoffs = {round(pt["cutoff"], 6) for pt in rd["placeboTests"]}
#     assert _TEST_PLACEBO_LEFT in cutoffs or any(
#         abs(c - _TEST_PLACEBO_LEFT) < _PLACEBO_TOLERANCE for c in cutoffs
#     )


# def test_rdd_result_stored(client, tables_store):
#     resp = client.post(URL_RDD, json=RDDPayload().build())
#     assert resp.status_code == status.HTTP_200_OK
#     result_id = resp.json()["result"]["resultId"]
#     saved = AnalysisResultStore().get_result(result_id)
#     assert saved is not None
#     assert saved.result_type == "rdd"
#     assert "estimate" in saved.result_data


# def test_rdd_missing_table_error(client, tables_store):
#     payload = RDDPayload(table="NonExistentTable").build()
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_400_BAD_REQUEST
#     data = resp.json()
#     assert data["code"] == ErrorCode.DATA_NOT_FOUND
#     assert data["message"] == "tableName 'NonExistentTable'は存在しません。"


# def test_rdd_missing_outcome_column_error(client, tables_store):
#     payload = RDDPayload(outcome="no_such_col").build()
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_400_BAD_REQUEST
#     data = resp.json()
#     assert data["code"] == ErrorCode.DATA_NOT_FOUND
#     assert data["message"] == "outcomeVariable 'no_such_col'は存在しません。"


# def test_rdd_missing_running_column_error(client, tables_store):
#     payload = RDDPayload(running="no_such_col").build()
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_400_BAD_REQUEST
#     data = resp.json()
#     assert data["code"] == ErrorCode.DATA_NOT_FOUND
#     assert data["message"] == "runningVariable 'no_such_col'は存在しません。"


# def test_rdd_string_column_error(client, tables_store):
#     payload = RDDPayload(table=TABLE_STRING).build()
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_400_BAD_REQUEST
#     assert resp.json()["code"] == ErrorCode.INVALID_DTYPE


# def test_rdd_same_column_error(client, tables_store):
#     payload = RDDPayload(outcome="running_var", running="running_var").build() # noqa: E501
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     data = resp.json()
#     assert data["code"] == ErrorCode.VALIDATION_ERROR
#     assert "outcomeVariable and runningVariable" in data["message"]


# def test_rdd_insufficient_left_observations_error(client, tables_store):
#     payload = RDDPayload(table=TABLE_NO_LEFT, cutoff=0.0).build()
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_400_BAD_REQUEST
#     data = resp.json()
#     assert data["code"] == ErrorCode.RDD_INSUFFICIENT_OBSERVATIONS
#     assert "left of cutoff" in data["message"]


# def test_rdd_placebo_cutoff_equals_main_error(client, tables_store):
#     payload = RDDPayload(placebo_cutoffs=[0.0]).build()
#     resp = client.post(URL_RDD, json=payload)
#     assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# def test_rdd_quadratic_poly(client, tables_store):
#     rd = _get_result_data(client, RDDPayload(p=2).build())
#     assert "estimate" in rd
#     assert isinstance(rd["estimate"]["coef"], float)


# @pytest.mark.parametrize("bw", ["mserd", "msetwo", "cerrd"])
# def test_rdd_bw_select_algorithms(client, tables_store, bw):
#     rd = _get_result_data(client, RDDPayload(bw_select=bw).build())
#     assert rd["bandwidth"]["bwLeft"] > 0
#     assert rd["bandwidth"]["bwRight"] > 0


# def test_rdd_estimate_numerical(client, tables_store):
#     gold = _load_rdd_gold()
#     expected_coef: float = gold["estimates"]["conventional"]["coef"]
#     expected_se: float = gold["estimates"]["conventional"]["std_err"]
#     rd = _get_result_data(client, RDDPayload().build())
#     coef: float = rd["estimate"]["coef"]
#     se: float = rd["estimate"]["stdErr"]
#     assert abs(coef - expected_coef) <= _RDROBUST_ESTIMATE_TOLERANCE
#     assert abs(se - expected_se) <= _RDROBUST_ESTIMATE_TOLERANCE
