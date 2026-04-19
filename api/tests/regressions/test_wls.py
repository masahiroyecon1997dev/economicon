"""WLS回帰テスト"""

import polars as pl
from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_WLS,
    URL_REGRESSION,
    OlsPayload,
    WlsPayload,
)

_ABS_TOL = 1e-12
_N_PARAMS_WITH_CONST = 4
_N_INVALID_WEIGHTS = 2


def _get_output(client, payload: dict) -> dict:
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


def test_wls_success(client, tables_store):
    """WLS回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=WlsPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_wls_response_structure(client, tables_store):
    """WLSの result_data に必須キーが含まれることを確認"""
    output = _get_output(client, WlsPayload().build())

    assert "parameters" in output
    assert "modelStatistics" in output
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_wls_equal_weights_matches_ols(client, tables_store):
    """全重みが1のときWLS係数がOLS係数と一致することを確認"""
    df = tables_store.get_table(TABLE_WLS).table.with_columns(
        pl.lit(1.0).alias("weights_one")
    )
    tables_store.store_table(TABLE_WLS, df)

    wls_params = _get_output(
        client,
        WlsPayload(weights_col="weights_one").build(),
    )["parameters"]
    ols_params = _get_output(client, OlsPayload(table=TABLE_WLS).build())[
        "parameters"
    ]

    wls_map = {p["variable"]: p["coefficient"] for p in wls_params}
    ols_map = {p["variable"]: p["coefficient"] for p in ols_params}

    for var, exp_coef in ols_map.items():
        assert abs(wls_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: WLS={wls_map[var]!r}, OLS={exp_coef!r}"
        )


def test_wls_missing_weights_column(client, tables_store):
    """存在しない weightsColumn を指定すると 400 を返す"""
    resp = client.post(
        URL_REGRESSION,
        json=WlsPayload(weights_col="no_such_weights").build(),
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["message"] == "weightsColumn 'no_such_weights'は存在しません。"


def test_wls_invalid_weights_values(client, tables_store):
    """0以下の重みが含まれると 500 INVALID_WEIGHTS_VALUES を返す"""
    df = tables_store.get_table(TABLE_WLS).table
    bad_weights = [0.0, -1.0] + [1.0] * (df.height - _N_INVALID_WEIGHTS)
    df_bad = df.with_columns(pl.Series("weights_bad", bad_weights))
    tables_store.store_table(TABLE_WLS, df_bad)

    resp = client.post(
        URL_REGRESSION,
        json=WlsPayload(weights_col="weights_bad").build(),
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = resp.json()
    assert data["code"] == "INVALID_WEIGHTS_VALUES"
    assert data["message"] == (
        "weightsColumn must contain only positive values (> 0)."
        " Found 2 invalid values."
    )
