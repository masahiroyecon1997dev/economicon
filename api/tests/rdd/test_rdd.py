"""RDD 分析テスト"""

import json
from pathlib import Path

import polars as pl
import pytest
from fastapi import status

from economicon.core.enums import ErrorCode
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.rdd.fitters import compute_bins_data
from tests.rdd.conftest import (
    TABLE_STRING,
    URL_RDD,
    RDDPayload,
)

# ベンチマークファイルパス
_BENCH_PY_DIR = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "benchmarks"
    / "python"
    / "synthetic"
)


def _load_rdd_gold() -> dict:
    """RDD gold JSON を読み込む"""
    with (_BENCH_PY_DIR / "synthetic_rdd_gold.json").open(
        encoding="utf-8"
    ) as f:
        return json.load(f)


# テスト用定数
_POLY_FIT_POINTS = 100
_BW_TOLERANCE = 1e-6
_PLACEBO_TOLERANCE = 1e-6
_MIN_PLACEBO_COUNT = 2
_TEST_PLACEBO_LEFT = -0.5
_TEST_PLACEBO_RIGHT = 0.5
_TEST_BINS_COUNT = 4

# -----------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------


def _get_result_data(client, payload: dict) -> dict:
    """POST → result_data を返すヘルパー"""
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系: レスポンス構造
# -----------------------------------------------------------


def test_rdd_basic_success(client, tables_store):
    """RDD 分析が 200 を返し resultId を含むことを確認"""
    resp = client.post(URL_RDD, json=RDDPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_rdd_response_structure(client, tables_store):
    """result_data に必須フィールドが含まれることを確認"""
    rd = _get_result_data(client, RDDPayload().build())

    assert "estimate" in rd
    assert "bandwidth" in rd
    assert "binsData" in rd
    assert "polyFitData" in rd
    assert "densityTest" in rd
    assert "placeboTests" in rd


def test_rdd_estimate_fields(client, tables_store):
    """estimate フィールドに必須キーが含まれることを確認"""
    rd = _get_result_data(client, RDDPayload().build())
    est = rd["estimate"]

    for key in (
        "coef",
        "stdErr",
        "zStat",
        "pValue",
        "ciLower",
        "ciUpper",
        "biasCorrectedCoef",
        "biasCorrectedCiLower",
        "biasCorrectedCiUpper",
        "rho",
    ):
        assert key in est, f"estimate に '{key}' が存在しない"


def test_rdd_bandwidth_fields(client, tables_store):
    """bandwidth フィールドに必須キーが含まれることを確認"""
    rd = _get_result_data(client, RDDPayload().build())
    bw = rd["bandwidth"]

    for key in (
        "bwLeft",
        "bwRight",
        "bwBiasLeft",
        "bwBiasRight",
        "nLeft",
        "nRight",
        "nTotal",
    ):
        assert key in bw, f"bandwidth に '{key}' が存在しない"


def test_rdd_bandwidth_positive(client, tables_store):
    """バンド幅・サンプル数が正の値であることを確認"""
    rd = _get_result_data(client, RDDPayload().build())
    bw = rd["bandwidth"]

    assert bw["bwLeft"] > 0
    assert bw["bwRight"] > 0
    assert bw["bwBiasLeft"] > 0
    assert bw["bwBiasRight"] > 0
    assert bw["nLeft"] > 0
    assert bw["nRight"] > 0
    assert bw["nTotal"] > 0


def test_rdd_bins_data_nonempty(client, tables_store):
    """bins_data が空でないことを確認"""
    rd = _get_result_data(client, RDDPayload().build())
    assert len(rd["binsData"]) > 0
    for b in rd["binsData"]:
        assert "x" in b
        assert "y" in b


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


def test_rdd_poly_fit_nonempty(client, tables_store):
    """poly_fit_data の左右にデータが含まれることを確認"""
    rd = _get_result_data(client, RDDPayload().build())
    pf = rd["polyFitData"]
    assert len(pf["left"]["x"]) == _POLY_FIT_POINTS
    assert len(pf["left"]["y"]) == _POLY_FIT_POINTS
    assert len(pf["right"]["x"]) == _POLY_FIT_POINTS
    assert len(pf["right"]["y"]) == _POLY_FIT_POINTS


def test_rdd_placebo_tests_auto_generated(client, tables_store):
    """placebo_cutoffs 未指定時に自動生成されたプラシーボ検定が返ること"""
    rd = _get_result_data(client, RDDPayload().build())
    # ±5% → 最低 2 点（データ範囲 [-1, 1] に収まる場合）
    assert len(rd["placeboTests"]) >= 1
    for pt in rd["placeboTests"]:
        for key in (
            "cutoff",
            "coef",
            "stdErr",
            "pValue",
            "ciLower",
            "ciUpper",
            "isSignificant",
        ):
            assert key in pt, f"placeboTests に '{key}' が存在しない"


def test_rdd_density_test_fields(client, tables_store):
    """density_test が null でない場合、必須フィールドを持つことを確認"""
    rd = _get_result_data(client, RDDPayload().build())
    dt = rd["densityTest"]
    if dt is not None:
        assert "testStatistic" in dt
        assert "pValue" in dt
        assert "description" in dt


# -----------------------------------------------------------
# 正常系: 手動バンド幅
# -----------------------------------------------------------


def test_rdd_manual_bandwidth(client, tables_store):
    """h 手動指定時にバンド幅が指定値と一致することを確認"""
    h_val = 0.3
    rd = _get_result_data(client, RDDPayload(h=h_val).build())
    bw = rd["bandwidth"]
    # rdrobust は対称バンド幅 h を指定した場合 h_left == h_right == h
    assert abs(bw["bwLeft"] - h_val) < _BW_TOLERANCE
    assert abs(bw["bwRight"] - h_val) < _BW_TOLERANCE


# -----------------------------------------------------------
# 正常系: 処置効果の方向性
# -----------------------------------------------------------


def test_rdd_effect_direction(client, tables_store):
    """
    DGP: true_effect = 1.5 (正の不連続)。
    conventional 推定値の符号が正であることを確認。
    """
    rd = _get_result_data(client, RDDPayload().build())
    assert rd["estimate"]["coef"] > 0, (
        "正の処置効果に対し coef が非正: {}".format(rd["estimate"]["coef"])
    )


# -----------------------------------------------------------
# 正常系: プラシーボ境界値手動指定
# -----------------------------------------------------------


def test_rdd_custom_placebo_cutoffs(client, tables_store):
    """ユーザー指定の placebo_cutoffs で検定が実行されることを確認"""
    rd = _get_result_data(
        client,
        RDDPayload(
            placebo_cutoffs=[_TEST_PLACEBO_LEFT, _TEST_PLACEBO_RIGHT]
        ).build(),
    )
    assert len(rd["placeboTests"]) == _MIN_PLACEBO_COUNT
    # プラシーボ境界値が正しく記録されていることを確認
    cutoffs = {round(pt["cutoff"], 6) for pt in rd["placeboTests"]}
    assert _TEST_PLACEBO_LEFT in cutoffs or any(
        abs(c - _TEST_PLACEBO_LEFT) < _PLACEBO_TOLERANCE for c in cutoffs
    )


# -----------------------------------------------------------
# 正常系: 結果ストアへの保存
# -----------------------------------------------------------


def test_rdd_result_stored(client, tables_store):
    """resultId で保存された結果が取得できることを確認"""
    resp = client.post(URL_RDD, json=RDDPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    result_id = resp.json()["result"]["resultId"]

    saved = AnalysisResultStore().get_result(result_id)
    assert saved is not None
    assert saved.result_type == "rdd"
    assert "estimate" in saved.result_data


# -----------------------------------------------------------
# エラー系: バリデーション
# -----------------------------------------------------------


def test_rdd_missing_table_error(client, tables_store):
    """存在しないテーブル名を指定した場合に 400 が返ることを確認"""
    payload = RDDPayload(table="NonExistentTable").build()
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["code"] == ErrorCode.DATA_NOT_FOUND
    assert data["message"] == "tableName 'NonExistentTable'は存在しません。"


def test_rdd_missing_outcome_column_error(client, tables_store):
    """存在しない結果変数列を指定した場合に 400 が返ることを確認"""
    payload = RDDPayload(outcome="no_such_col").build()
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["code"] == ErrorCode.DATA_NOT_FOUND
    assert data["message"] == "outcomeVariable 'no_such_col'は存在しません。"


def test_rdd_missing_running_column_error(client, tables_store):
    """存在しない実行変数列を指定した場合に 400 が返ることを確認"""
    payload = RDDPayload(running="no_such_col").build()
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["code"] == ErrorCode.DATA_NOT_FOUND
    assert data["message"] == "runningVariable 'no_such_col'は存在しません。"


def test_rdd_string_column_error(client, tables_store):
    """数値型でない列を指定した場合に 400 が返ることを確認"""
    payload = RDDPayload(table=TABLE_STRING).build()
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["code"] == ErrorCode.INVALID_DTYPE


def test_rdd_same_column_error(client, tables_store):
    """結果変数と実行変数が同じ列の場合に 422 が返ることを確認"""
    payload = RDDPayload(outcome="running_var", running="running_var").build()
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = resp.json()
    assert data["code"] == ErrorCode.VALIDATION_ERROR
    assert "outcomeVariable and runningVariable" in data["message"]


def test_rdd_insufficient_left_observations_error(client, tables_store):
    """カットオフ左側のサンプルが不足している場合に 400 が返ることを確認"""
    # running_var の範囲は [-2, 2]。cutoff=-1.95 で左側がはぼゼロ
    payload = RDDPayload(cutoff=-1.95).build()
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["code"] == ErrorCode.RDD_INSUFFICIENT_OBSERVATIONS
    assert "left of cutoff" in data["message"]


def test_rdd_placebo_cutoff_equals_main_error(client, tables_store):
    """プラシーボ境界値が main cutoff と重複する場合に 422 が返ることを確認"""
    payload = RDDPayload(placebo_cutoffs=[0.0]).build()
    resp = client.post(URL_RDD, json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# -----------------------------------------------------------
# 正常系: p=2 (2次式)
# -----------------------------------------------------------


def test_rdd_quadratic_poly(client, tables_store):
    """p=2 での推定が正常に完了することを確認"""
    rd = _get_result_data(client, RDDPayload(p=2).build())
    assert "estimate" in rd
    assert isinstance(rd["estimate"]["coef"], float)


# -----------------------------------------------------------
# 正常系: 異なるバンド幅選択アルゴリズム
# -----------------------------------------------------------


@pytest.mark.parametrize("bw", ["mserd", "msetwo", "cerrd"])
def test_rdd_bw_select_algorithms(client, tables_store, bw):
    """各バンド幅選択アルゴリズムで推定が成功することを確認"""
    rd = _get_result_data(client, RDDPayload(bw_select=bw).build())
    assert rd["bandwidth"]["bwLeft"] > 0
    assert rd["bandwidth"]["bwRight"] > 0


# -----------------------------------------------------------
# 数値検証: Gold JSON との対照
# -----------------------------------------------------------


def test_rdd_estimate_numerical(client, tables_store):
    """洗練データでの conventional 推定値を gold JSON と照合"""
    gold = _load_rdd_gold()
    expected_coef: float = gold["estimates"]["conventional"]["coef"]
    expected_se: float = gold["estimates"]["conventional"]["std_err"]

    rd = _get_result_data(client, RDDPayload().build())
    coef: float = rd["estimate"]["coef"]
    se: float = rd["estimate"]["se"]

    # rdrobust のローカル多項式測定は許容誤差大きめ
    assert abs(coef - expected_coef) <= 1e-4, (
        f"coef mismatch: got {coef}, expected {expected_coef}"
    )
    assert abs(se - expected_se) <= 1e-4, (
        f"se mismatch: got {se}, expected {expected_se}"
    )
