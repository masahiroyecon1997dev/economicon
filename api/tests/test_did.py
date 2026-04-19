"""差の差（DID）分析テスト"""

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from main import app

_URL = "/api/analysis/did"
_TABLE_NAME = "DidData"
_DUP_TABLE = "DidDataDup"
_BAD_TREAT_TABLE = "DidDataBadTreat"

_N_ENTITIES = 4
_N_PERIODS = 4
_N_TREATED = 2
_N_CONTROL = 2
_POST_START_PERIOD = 2


@pytest.fixture
def client() -> TestClient:
    """DID API 用 TestClient フィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store() -> TablesStore:
    """DID テスト用のテーブルを初期化する"""
    manager = TablesStore()
    manager.clear_tables()

    result_store = AnalysisResultStore()
    result_store.clear_all()

    entity_ids: list[int] = []
    time_ids: list[int] = []
    treated: list[int] = []
    post: list[int] = []
    x1: list[float] = []
    y: list[float] = []

    for entity_id in range(1, _N_ENTITIES + 1):
        is_treated = 1 if entity_id <= _N_TREATED else 0
        for time_id in range(_N_PERIODS):
            is_post = 1 if time_id >= _POST_START_PERIOD else 0
            x_val = float(entity_id + time_id)
            treat_effect = 5.0 * is_treated * is_post
            y_val = 10.0 + 1.5 * x_val + treat_effect

            entity_ids.append(entity_id)
            time_ids.append(time_id)
            treated.append(is_treated)
            post.append(is_post)
            x1.append(x_val)
            y.append(y_val)

    df = pl.DataFrame(
        {
            "entity_id": entity_ids,
            "time_id": time_ids,
            "treated": treated,
            "post": post,
            "x1": x1,
            "y": y,
        }
    )
    manager.store_table(_TABLE_NAME, df)

    dup_df = pl.concat([df, df.head(1)], how="vertical")
    manager.store_table(_DUP_TABLE, dup_df)

    bad_treat_df = df.with_columns(
        pl.when(pl.col("entity_id") == 1)
        .then(2)
        .otherwise(pl.col("treated"))
        .alias("treated")
    )
    manager.store_table(_BAD_TREAT_TABLE, bad_treat_df)

    return manager


_BASE_PAYLOAD: dict = {
    "tableName": _TABLE_NAME,
    "resultName": "DID Test",
    "description": "DID endpoint regression test",
    "dependentVariable": "y",
    "explanatoryVariables": ["x1"],
    "treatmentColumn": "treated",
    "postColumn": "post",
    "timeColumn": "time_id",
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
    if "standardError" not in payload:
        payload["standardError"] = _BASE_PAYLOAD["standardError"]
    return payload


def _get_output(client: TestClient, payload: dict) -> dict:
    """POSTして result_data を返すヘルパー"""
    resp = client.post(_URL, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


def test_did_success(client, tables_store):
    """DID 分析が200を返し resultId を含むことを確認"""
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


def test_did_treatment_effect_positive(client, tables_store):
    """設計上、DID 推定量が正になることを確認"""
    output = _get_output(client, _payload())
    did_est = output["didEstimate"]
    model_stats = output["modelStatistics"]

    assert did_est["coefficient"] > 0.0
    assert model_stats["nTreated"] == _N_TREATED
    assert model_stats["nControl"] == _N_CONTROL


def test_did_event_study_success(client, tables_store):
    """Event Study 有効時に eventStudy が返ることを確認"""
    output = _get_output(client, _payload(includeEventStudy=True))

    event_study = output["eventStudy"]
    assert isinstance(event_study, list)
    assert len(event_study) > 0
    assert any(item["period"] == 1 for item in event_study)


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
    resp = client.post(
        _URL,
        json=_payload(tableName=_BAD_TREAT_TABLE),
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = resp.json()
    assert data["message"] == (
        "'treatmentColumn' must be a binary (0/1) dummy variable."
        " Found 1 non-binary value(s)."
    )


def test_did_duplicate_entity_time_error(client, tables_store):
    """同一 entity-time の重複行があると 500 を返す"""
    resp = client.post(
        _URL,
        json=_payload(tableName=_DUP_TABLE),
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = resp.json()
    assert data["message"] == (
        "Duplicate (entity, time) pairs found in data."
        " Each combination of entityIdColumn"
        " and timeColumn must be unique."
    )
