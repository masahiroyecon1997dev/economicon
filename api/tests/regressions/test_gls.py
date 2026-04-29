"""GLS回帰テスト"""

import polars as pl
from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_GLS_DATA,
    URL_REGRESSION,
    GlsPayload,
    OlsPayload,
    load_py_gold,
)

_ABS_TOL = 1e-12
_GLS_OLS_DIFFERENCE_THRESHOLD = 1e-6
_EXPECTED_N_OBS = 48
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


def _assert_model_statistics_matches_gold(output: dict, gold: dict) -> None:
    stats = output["modelStatistics"]
    diagnostics = gold["estimates"]["diagnostics"]

    assert stats["nObservations"] == gold["estimates"]["n_obs"]
    assert abs(stats["R2"] - diagnostics["r_squared"]) < _ABS_TOL
    assert abs(stats["adjustedR2"] - diagnostics["adj_r_squared"]) < _ABS_TOL
    assert abs(stats["fValue"] - diagnostics["f_test"]["statistic"]) < _ABS_TOL
    assert (
        abs(stats["fProbability"] - diagnostics["f_test"]["p_value"])
        < _ABS_TOL
    )
    assert abs(stats["AIC"] - diagnostics["aic"]) < _ABS_TOL
    assert abs(stats["BIC"] - diagnostics["bic"]) < _ABS_TOL
    assert (
        abs(stats["logLikelihood"] - diagnostics["log_likelihood"]) < _ABS_TOL
    )


def test_gls_success(client, tables_store):
    """GLS回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=_valid_gls_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_gls_matches_python_gold(client, tables_store):
    """GLS が Python gold benchmark と一致することを確認"""
    gold = load_py_gold("gls")
    output = _get_output(client, _valid_gls_payload())
    params = {param["variable"]: param for param in output["parameters"]}
    gold_params = gold["estimates"]["nonrobust"]

    for variable, expected in gold_params["coefficients"].items():
        got = params[variable]
        assert abs(got["coefficient"] - expected) < _ABS_TOL
        assert (
            abs(got["standardError"] - gold_params["std_errors"][variable])
            < _ABS_TOL
        )
        assert (
            abs(got["tValue"] - gold_params["t_values"][variable]) < _ABS_TOL
        )
        assert (
            abs(got["pValue"] - gold_params["p_values"][variable]) < _ABS_TOL
        )
        assert (
            abs(
                got["confidenceIntervalLower"]
                - gold_params["conf_int"][variable]["lower"]
            )
            < _ABS_TOL
        )
        assert (
            abs(
                got["confidenceIntervalUpper"]
                - gold_params["conf_int"][variable]["upper"]
            )
            < _ABS_TOL
        )

    _assert_model_statistics_matches_gold(output, gold)


def test_gls_differs_from_ols_when_sigma_is_non_identity(client, tables_store):
    """非単位の sigma を使う GLS が OLS と異なることを確認"""
    gls_params = _get_output(client, _valid_gls_payload())["parameters"]
    ols_params = _get_output(
        client,
        OlsPayload(table=TABLE_GLS_DATA, dep="y", expl=["x1", "x2"]).build(),
    )["parameters"]

    gls_map = {p["variable"]: p["coefficient"] for p in gls_params}
    ols_map = {p["variable"]: p["coefficient"] for p in ols_params}

    assert any(
        abs(gls_map[var] - ols_map[var]) > _GLS_OLS_DIFFERENCE_THRESHOLD
        for var in gls_map
    ), "GLS coefficients unexpectedly match OLS under non-identity sigma"


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
        "sigmaTableName must be a 48×48 square matrix, but got 3×3."
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
