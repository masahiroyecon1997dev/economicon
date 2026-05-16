"""Logit回帰テスト"""

from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    LogitPayload,
    load_py_gold,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-8

# パラメータ数定数
_N_PARAMS_WITH_CONST = 4


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_logit_success(client, tables_store):
    """Logit回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=LogitPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_logit_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, LogitPayload().build())
    model_stats = output["modelStatistics"]

    for key in ("pseudoRSquared", "logLikelihood"):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )

    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST  # const, x1, x2
    for p in params:
        for key in (
            "variable",
            "coefficient",
            "standardError",
            "tValue",
            "pValue",
        ):
            assert key in p


def test_logit_coefficients_numerical(client, tables_store):
    """Logit係数が gold JSON と一致することを確認"""
    gold = load_py_gold("logit")["estimates"]
    expected = gold["coefficients"]

    params = _get_output(client, LogitPayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    for var, exp_coef in expected.items():
        assert abs(coef_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: got {coef_map[var]!r}, expected {exp_coef!r}"
        )


def test_logit_pseudo_r2_range(client, tables_store):
    """pseudoRSquaredが0以上1未満であることを確認"""
    model_stats = _get_output(client, LogitPayload().build())[
        "modelStatistics"
    ]
    pseudo_r2 = model_stats["pseudoRSquared"]
    assert 0.0 <= pseudo_r2 < 1.0


def test_logit_log_likelihood_negative(client, tables_store):
    """logLikelihoodが負値（≤0）であることを確認"""
    model_stats = _get_output(client, LogitPayload().build())[
        "modelStatistics"
    ]
    assert model_stats["logLikelihood"] <= 0.0


def test_logit_log_likelihood_numerical(client, tables_store):
    """logLikelihood が gold JSON と一致することを確認"""
    gold_ll: float = load_py_gold("logit")["estimates"]["log_likelihood"]

    model_stats = _get_output(client, LogitPayload().build())[
        "modelStatistics"
    ]
    assert abs(model_stats["logLikelihood"] - gold_ll) < _ABS_TOL


def test_logit_pseudo_r2_numerical(client, tables_store):
    """McFadden pseudoR2 が gold JSON と一致することを確認"""
    gold_pr2: float = load_py_gold("logit")["estimates"]["pseudo_r_squared"]

    model_stats = _get_output(client, LogitPayload().build())[
        "modelStatistics"
    ]
    assert abs(model_stats["pseudoRSquared"] - gold_pr2) < _ABS_TOL


def test_logit_robust_se(client, tables_store):
    """ロバスト標準誤差付きLogitが成功することを確認"""
    resp = client.post(
        URL_REGRESSION, json=LogitPayload(se_method="robust").build()
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["code"] == "OK"


def test_logit_pvalues_range(client, tables_store):
    """p値が0以上1以下であることを確認"""
    params = _get_output(client, LogitPayload().build())["parameters"]
    for p in params:
        assert 0.0 <= p["pValue"] <= 1.0
