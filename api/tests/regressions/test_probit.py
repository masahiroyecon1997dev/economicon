"""Probit回帰テスト"""

from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    LogitPayload,
    ProbitPayload,
    load_py_gold,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-8

# パラメータ数定数
_N_PARAMS_WITH_CONST = 4  # const, x1, x2, x3

# probit/logit係数比の許容範囲
_RATIO_MIN = 0.2
_RATIO_MAX = 0.9

# 有意な係数の最小絶対値
_MIN_COEF_THRESHOLD = 0.1


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_probit_success(client, tables_store):
    """Probit回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=ProbitPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_probit_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, ProbitPayload().build())
    model_stats = output["modelStatistics"]

    for key in ("pseudoRSquared", "logLikelihood"):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )

    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST
    for p in params:
        for key in (
            "variable",
            "coefficient",
            "standardError",
            "tValue",
            "pValue",
        ):
            assert key in p


def test_probit_coefficients_numerical(client, tables_store):
    """Probit係数が gold JSON と一致することを確認"""
    gold = load_py_gold("probit")["estimates"]["coefficients"]

    params = _get_output(client, ProbitPayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    for var, exp_coef in gold.items():
        assert abs(coef_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: got {coef_map[var]!r}, expected {exp_coef!r}"
        )


def test_probit_pseudo_r2_range(client, tables_store):
    """pseudoRSquaredが0以上1未満であることを確認"""
    model_stats = _get_output(client, ProbitPayload().build())[
        "modelStatistics"
    ]
    assert 0.0 <= model_stats["pseudoRSquared"] < 1.0


def test_probit_log_likelihood_negative(client, tables_store):
    """logLikelihoodが負値（≤0）であることを確認"""
    model_stats = _get_output(client, ProbitPayload().build())[
        "modelStatistics"
    ]
    assert model_stats["logLikelihood"] <= 0.0


def test_probit_log_likelihood_numerical(client, tables_store):
    """logLikelihoodが gold JSON と一致することを確認"""
    gold_ll = load_py_gold("probit")["estimates"]["log_likelihood"]

    model_stats = _get_output(client, ProbitPayload().build())[
        "modelStatistics"
    ]
    assert abs(model_stats["logLikelihood"] - gold_ll) < _ABS_TOL


def test_probit_vs_logit_coefficient_magnitude(client, tables_store):
    """Probitの係数の絶対値はLogit係数の約0.55倍になることを確認（規則の目安）"""
    logit_params = _get_output(client, LogitPayload().build())["parameters"]
    probit_params = _get_output(client, ProbitPayload().build())["parameters"]

    # const以外の係数で比較
    for lp, pp in zip(logit_params[1:], probit_params[1:], strict=False):
        if abs(lp["coefficient"]) > _MIN_COEF_THRESHOLD:
            ratio = abs(pp["coefficient"]) / abs(lp["coefficient"])
            # 概ね 0.3 ～ 0.7 の範囲（統計的目安）
            assert _RATIO_MIN < ratio < _RATIO_MAX, (
                f"{pp['variable']}: probit/logit比={ratio:.3f}"
                f" (期待: 0.3～0.7)"
            )


def test_probit_pseudo_r2_numerical(client, tables_store):
    """McFadden pseudoR2が gold JSON と一致することを確認"""
    gold_prsq = load_py_gold("probit")["estimates"]["pseudo_r_squared"]

    model_stats = _get_output(client, ProbitPayload().build())[
        "modelStatistics"
    ]
    assert abs(model_stats["pseudoRSquared"] - gold_prsq) < _ABS_TOL


def test_probit_pvalues_range(client, tables_store):
    """p値が0以上1以下であることを確認"""
    params = _get_output(client, ProbitPayload().build())["parameters"]
    for p in params:
        assert 0.0 <= p["pValue"] <= 1.0
