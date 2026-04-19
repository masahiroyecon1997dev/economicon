"""FGLS回帰テスト"""

from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_FGLS_AR1,
    URL_REGRESSION,
    FglsPayload,
    load_py_gold,
)

_ABS_TOL = 1e-10
_N_PARAMS_WITH_CONST = 4


def _get_output(client, payload: dict) -> dict:
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


def _build_ar1_payload(**kwargs) -> dict:
    payload = FglsPayload(
        table=TABLE_FGLS_AR1,
        dep="y",
        fgls_method="ar1",
        **kwargs,
    ).build()
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


def _assert_parameters_match_gold(output: dict, gold: dict) -> None:
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


def test_fgls_heteroskedastic_success(client, tables_store):
    """heteroskedastic FGLS が200を返すことを確認"""
    resp = client.post(
        URL_REGRESSION,
        json=FglsPayload(fgls_method="heteroskedastic").build(),
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_fgls_ar1_success(client, tables_store):
    """AR(1) FGLS が200を返すことを確認"""
    output = _get_output(client, _build_ar1_payload())
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_fgls_response_structure(client, tables_store):
    """FGLS の result_data に必須キーが含まれることを確認"""
    output = _get_output(client, FglsPayload().build())
    assert "parameters" in output
    assert "modelStatistics" in output
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_fgls_default_matches_heteroskedastic(client, tables_store):
    """デフォルト FGLS が heteroskedastic と一致することを確認"""
    default_params = _get_output(client, FglsPayload().build())["parameters"]
    hetero_params = _get_output(
        client,
        FglsPayload(fgls_method="heteroskedastic").build(),
    )["parameters"]

    default_map = {p["variable"]: p["coefficient"] for p in default_params}
    hetero_map = {p["variable"]: p["coefficient"] for p in hetero_params}

    for var, exp_coef in hetero_map.items():
        assert abs(default_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: default={default_map[var]!r}, hetero={exp_coef!r}"
        )


def test_fgls_heteroskedastic_matches_python_gold(client, tables_store):
    """heteroskedastic FGLS が Python gold benchmark と一致することを確認"""
    gold = load_py_gold("fgls_heteroskedastic")
    output = _get_output(
        client,
        FglsPayload(fgls_method="heteroskedastic").build(),
    )

    _assert_parameters_match_gold(output, gold)
    _assert_model_statistics_matches_gold(output, gold)


def test_fgls_ar1_matches_python_gold(client, tables_store):
    """AR(1) FGLS が Python gold benchmark と一致することを確認"""
    gold = load_py_gold("fgls_ar1")
    output = _get_output(client, _build_ar1_payload())

    _assert_parameters_match_gold(output, gold)
    _assert_model_statistics_matches_gold(output, gold)


def test_fgls_ar1_low_max_iter_still_returns_result(client, tables_store):
    """AR(1) で maxIter=1 でも結果が返ることを確認"""
    output = _get_output(client, _build_ar1_payload(max_iter=1))
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_fgls_coefficient_signs(client, tables_store):
    """heteroskedastic データ上で x1 は正、x2 は負の係数を返すことを確認"""
    params = _get_output(client, FglsPayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    assert coef_map["x1"] > 0.0
    assert coef_map["x2"] < 0.0


def test_fgls_robust_request_success(client, tables_store):
    """robust 標準誤差でも FGLS が成功することを確認"""
    output = _get_output(client, FglsPayload(se_method="robust").build())
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST
