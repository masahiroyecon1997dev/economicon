"""差の差（DID）分析テスト

合成データ (test/data/csv/synthetic_did*.csv) を TablesStore に登録し、
Python gold benchmark (test/benchmarks/python/synthetic/synthetic_did_gold.json)
と照合して推定精度を保証する。
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# パス定数
# -----------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parents[2] / "test" / "data" / "csv"
_BENCH_DIR = (
    Path(__file__).resolve().parents[2]
    / "test"
    / "benchmarks"
    / "python"
    / "synthetic"
)

# -----------------------------------------------------------
# テーブル名
# -----------------------------------------------------------

_TABLE_NAME = "DidData"
_DUP_TABLE = "DidDataDup"
_BAD_TREAT_TABLE = "DidDataBadTreat"

_URL = "/api/analysis/did"

# 許容誤差
_ABS_TOL = 1e-8

# -----------------------------------------------------------
# Gold JSON ローダー
# -----------------------------------------------------------

_GOLD: dict = {}


def _load_gold() -> dict:
    global _GOLD  # noqa: PLW0603
    if not _GOLD:
        path = _BENCH_DIR / "synthetic_did_gold.json"
        with path.open(encoding="utf-8") as f:
            _GOLD = json.load(f)
    return _GOLD


# -----------------------------------------------------------
# フィクスチャ
# -----------------------------------------------------------


@pytest.fixture(scope="module")
def tables_store() -> TablesStore:
    """CSV から読み込んだ DID テーブルを TablesStore に登録する。"""
    ts = TablesStore()
    ts.clear_tables()
    AnalysisResultStore().clear_all()

    ts.store_table(_TABLE_NAME, pl.read_csv(_DATA_DIR / "synthetic_did.csv"))
    ts.store_table(
        _DUP_TABLE, pl.read_csv(_DATA_DIR / "synthetic_did_duplicate.csv")
    )
    ts.store_table(
        _BAD_TREAT_TABLE,
        pl.read_csv(_DATA_DIR / "synthetic_did_bad_treatment.csv"),
    )
    return ts


@pytest.fixture(scope="module")
def client(tables_store):  # noqa: ARG001
    with TestClient(app) as c:
        yield c


# -----------------------------------------------------------
# ペイロードビルダー
# -----------------------------------------------------------

_BASE_PAYLOAD: dict = {
    "tableName": _TABLE_NAME,
    "resultName": "DID Test",
    "description": "DID endpoint regression test",
    "dependentVariable": "y",
    "explanatoryVariables": ["x1", "x2"],
    "treatmentColumn": "treated",
    "postColumn": "post",
    "timeColumn": "event_time",
    "entityIdColumn": "entity_id",
    "includeEventStudy": False,
    "missingValueHandling": "remove",
    "standardError": {
        "method": "cluster",
        "groups": ["entity_id"],
    },
    "confidenceLevel": 0.95,
}


def _payload(**overrides) -> dict:
    payload = {**_BASE_PAYLOAD, **overrides}
    return payload


def _get_output(client: TestClient, payload: dict) -> dict:
    resp = client.post(_URL, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系: レスポンス構造
# -----------------------------------------------------------


def test_did_success(client, tables_store):
    """DID 分析が 200 を返し resultId を含むことを確認"""
    resp = client.post(_URL, json=_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_did_response_structure(client, tables_store):
    """result_data に DID 固有キーが含まれることを確認"""
    output = _get_output(client, _payload())

    assert "didEstimate" in output
    assert "parameters" in output
    assert "modelStatistics" in output
    assert "diagnostics" in output


# -----------------------------------------------------------
# 正常系: ベンチマーク照合（nonrobust 推定量）
# -----------------------------------------------------------


def test_did_att_coefficient_vs_benchmark(client, tables_store):
    """ATT 推定量が Python gold benchmark と一致する（nonrobust SE）"""
    gold = _load_gold()
    gold_att = gold["estimates"]["twfe"]["nonrobust"]["did_estimate"][
        "coefficient"
    ]

    output = _get_output(
        client,
        _payload(standardError={"method": "nonrobust"}),
    )
    att = output["didEstimate"]["coefficient"]

    assert abs(att - gold_att) <= _ABS_TOL, (
        f"ATT mismatch: API={att}, gold={gold_att}"
    )


def test_did_att_se_vs_benchmark(client, tables_store):
    """ATT 標準誤差が Python gold benchmark と一致する（nonrobust SE）"""
    gold = _load_gold()
    gold_se = gold["estimates"]["twfe"]["nonrobust"]["did_estimate"][
        "standard_error"
    ]

    output = _get_output(
        client,
        _payload(standardError={"method": "nonrobust"}),
    )
    se = output["didEstimate"]["standardError"]

    assert abs(se - gold_se) <= _ABS_TOL, (
        f"SE mismatch: API={se}, gold={gold_se}"
    )


def test_did_x1_coefficient_vs_benchmark(client, tables_store):
    """x1 係数が Python gold benchmark と一致する（nonrobust SE）"""
    gold = _load_gold()
    gold_x1 = gold["estimates"]["twfe"]["nonrobust"]["parameters"][0][
        "coefficient"
    ]

    output = _get_output(
        client,
        _payload(standardError={"method": "nonrobust"}),
    )
    params = {p["name"]: p for p in output["parameters"]}
    x1_coef = params["x1"]["coefficient"]

    assert abs(x1_coef - gold_x1) <= _ABS_TOL, (
        f"x1 mismatch: API={x1_coef}, gold={gold_x1}"
    )


def test_did_x2_coefficient_vs_benchmark(client, tables_store):
    """x2 係数が Python gold benchmark と一致する（nonrobust SE）"""
    gold = _load_gold()
    gold_x2 = gold["estimates"]["twfe"]["nonrobust"]["parameters"][1][
        "coefficient"
    ]

    output = _get_output(
        client,
        _payload(standardError={"method": "nonrobust"}),
    )
    params = {p["name"]: p for p in output["parameters"]}
    x2_coef = params["x2"]["coefficient"]

    assert abs(x2_coef - gold_x2) <= _ABS_TOL, (
        f"x2 mismatch: API={x2_coef}, gold={gold_x2}"
    )


def test_did_model_statistics_vs_benchmark(client, tables_store):
    """n_observations / n_treated / n_control / n_periods が正しい"""
    gold = _load_gold()
    gold_stats = gold["estimates"]["twfe"]["nonrobust"]["model_statistics"]

    output = _get_output(
        client, _payload(standardError={"method": "nonrobust"})
    )
    ms = output["modelStatistics"]

    assert ms["nObservations"] == gold_stats["n_observations"]
    assert ms["nTreated"] == gold_stats["n_treated"]
    assert ms["nControl"] == gold_stats["n_control"]
    assert ms["nPeriods"] == gold_stats["n_periods"]


def test_did_clustered_att_vs_benchmark(client, tables_store):
    """entity cluster SE の ATT 係数が gold benchmark と一致する"""
    gold = _load_gold()
    gold_att = gold["estimates"]["twfe"]["clustered_entity"]["did_estimate"][
        "coefficient"
    ]

    output = _get_output(client, _payload())  # デフォルトは cluster
    att = output["didEstimate"]["coefficient"]

    assert abs(att - gold_att) <= _ABS_TOL, (
        f"Clustered ATT mismatch: API={att}, gold={gold_att}"
    )


# -----------------------------------------------------------
# 正常系: Event Study
# -----------------------------------------------------------


def test_did_event_study_success(client, tables_store):
    """Event Study 有効時に eventStudy が返ることを確認"""
    output = _get_output(client, _payload(includeEventStudy=True))

    event_study = output["eventStudy"]
    assert isinstance(event_study, list)
    assert len(event_study) > 0


def test_did_event_study_points_count(client, tables_store):
    """Event Study のポイント数が N_PERIODS-1 (=7) であることを確認"""
    gold = _load_gold()
    gold_n = len(gold["estimates"]["event_study"]["event_study_points"])

    output = _get_output(client, _payload(includeEventStudy=True))
    n_points = len(output["eventStudy"])

    # gold と同数になること
    assert n_points == gold_n, (
        f"Event Study points: API={n_points}, gold={gold_n}"
    )


def test_did_event_study_base_period_is_zero(client, tables_store):
    """Event Study の基準期 (period=-1) が係数=0 であることを確認"""
    output = _get_output(client, _payload(includeEventStudy=True))
    base_entries = [p for p in output["eventStudy"] if p["period"] == -1]
    assert len(base_entries) == 1
    assert base_entries[0]["coefficient"] == 0.0


def test_did_event_study_post_coefficients_positive(client, tables_store):
    """Event Study の post 期間 (period >= 0) 係数の平均が正であることを確認"""
    output = _get_output(client, _payload(includeEventStudy=True))
    post_coefs = [
        p["coefficient"] for p in output["eventStudy"] if p["period"] >= 0
    ]
    assert len(post_coefs) > 0
    assert sum(post_coefs) / len(post_coefs) > 0.0


def test_did_event_study_vs_benchmark(client, tables_store):
    """Event Study 係数が gold benchmark と一致する（period=0 を照合）"""
    gold = _load_gold()
    gold_points = {
        p["period"]: p
        for p in gold["estimates"]["event_study"]["event_study_points"]
    }

    output = _get_output(client, _payload(includeEventStudy=True))
    api_points = {p["period"]: p for p in output["eventStudy"]}

    # post 最初の期間 (period=0) で比較
    period = 0
    assert period in gold_points, "gold に period=0 のエントリがない"
    assert period in api_points, "API 応答に period=0 のエントリがない"
    gold_coef = gold_points[period]["coefficient"]
    api_coef = api_points[period]["coefficient"]
    assert abs(api_coef - gold_coef) <= _ABS_TOL, (
        f"Event Study period={period}: API={api_coef}, gold={gold_coef}"
    )


# -----------------------------------------------------------
# 異常系: バリデーション
# -----------------------------------------------------------


def test_did_base_period_requires_event_study(client, tables_store):
    """includeEventStudy=False で basePeriod 指定時は 422 を返す"""
    resp = client.post(_URL, json=_payload(basePeriod=1))
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = resp.json()
    assert data["message"] == (
        "basePeriod can only be set when includeEventStudy is true."
    )


def test_did_treatment_column_must_be_binary(client, tables_store):
    """treatmentColumn に 0/1 以外があると 500 を返す"""
    resp = client.post(_URL, json=_payload(tableName=_BAD_TREAT_TABLE))
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = resp.json()
    assert data["message"] == (
        "'treatmentColumn' must be a binary (0/1) dummy variable."
        " Found 1 non-binary value(s)."
    )


def test_did_duplicate_entity_time_error(client, tables_store):
    """同一 entity-time の重複行があると 500 を返す"""
    resp = client.post(_URL, json=_payload(tableName=_DUP_TABLE))
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = resp.json()
    assert data["message"] == (
        "Duplicate (entity, time) pairs found in data."
        " Each combination of entityIdColumn"
        " and timeColumn must be unique."
    )
