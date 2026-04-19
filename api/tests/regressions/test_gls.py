"""GLS回帰テスト"""

import polars as pl
from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_GLS_DATA,
    URL_REGRESSION,
    GlsPayload,
    OlsPayload,
)

_ABS_TOL = 1e-12
_EXPECTED_N_OBS = 10
_EXPECTED_SLOPE = 2.0
_EXPECTED_INTERCEPT = 0.0
_BAD_SIGMA_ROWS = 3
_BAD_SIGMA_COLS = 3


def _get_output(client, payload: dict) -> dict:
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


def _valid_gls_payload() -> dict:
    """missingValueHandling='error' を含むGLSペイロードを返す"""
    payload = GlsPayload().build()
    payload["missingValueHandling"] = "error"
    return payload


def test_gls_success(client, tables_store):
    """GLS回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=_valid_gls_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_gls_identity_sigma_expected_coefficients(client, tables_store):
    """単位行列 sigma のGLSが既知係数を返すことを確認"""
    params = _get_output(client, _valid_gls_payload())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    assert abs(coef_map["const"] - _EXPECTED_INTERCEPT) < _ABS_TOL
    assert abs(coef_map["x1"] - _EXPECTED_SLOPE) < _ABS_TOL


def test_gls_identity_sigma_matches_ols(client, tables_store):
    """単位行列 sigma では GLS 係数が OLS と一致することを確認"""
    gls_params = _get_output(client, _valid_gls_payload())["parameters"]
    ols_params = _get_output(
        client,
        OlsPayload(table=TABLE_GLS_DATA, dep="y", expl=["x1"]).build(),
    )["parameters"]

    gls_map = {p["variable"]: p["coefficient"] for p in gls_params}
    ols_map = {p["variable"]: p["coefficient"] for p in ols_params}

    for var, exp_coef in ols_map.items():
        assert abs(gls_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: GLS={gls_map[var]!r}, OLS={exp_coef!r}"
        )


def test_gls_missing_sigma_table(client, tables_store):
    """存在しない sigmaTableName を指定すると 400 を返す"""
    payload = _valid_gls_payload()
    payload["analysis"]["sigmaTableName"] = "NoSuchSigma"

    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["message"] == "sigmaTableName 'NoSuchSigma'は存在しません。"


def test_gls_wrong_sigma_dimension(client, tables_store):
    """sigma の次元が観測数と不一致なら 500 を返す"""
    bad_sigma = pl.DataFrame(
        {
            "a": [1.0, 0.0, 0.0],
            "b": [0.0, 1.0, 0.0],
            "c": [0.0, 0.0, 1.0],
        }
    )
    tables_store.store_table("BadSigma", bad_sigma)

    payload = _valid_gls_payload()
    payload["analysis"]["sigmaTableName"] = "BadSigma"

    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = resp.json()
    assert data["code"] == "SIGMA_DIMENSION_MISMATCH"
    assert data["message"] == (
        "sigmaTableName must be a 10×10 square matrix,"
        " but got 3×3."
    )


def test_gls_requires_missing_value_handling_error(client, tables_store):
    """GLS は missingValueHandling='error' を要求する"""
    resp = client.post(URL_REGRESSION, json=GlsPayload().build())
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["message"] == (
        "GLS requires missingValueHandling='error'."
        " Please remove rows with missing values before using GLS."
    )
