"""Logit回帰テスト"""

import numpy as np
import statsmodels.api as sm
from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    LogitPayload,
    generate_all_data,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-3

# パラメータ数定数
_N_PARAMS_WITH_CONST = 3


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
    """Logit係数がstatsmodelsと一致することを確認"""
    (x1, x2, _, y_binary), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.Logit(y_binary, x_mat).fit(disp=False)

    params = _get_output(client, LogitPayload().build())["parameters"]

    for i, exp_coef in enumerate(sm_result.params):
        assert abs(params[i]["coefficient"] - exp_coef) < _ABS_TOL, (
            f"Logit params[{i}]: {params[i]['coefficient']!r} != {exp_coef!r}"
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
    """logLikelihoodがstatsmodelsと一致することを確認"""
    (x1, x2, _, y_binary), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.Logit(y_binary, x_mat).fit(disp=False)

    model_stats = _get_output(client, LogitPayload().build())[
        "modelStatistics"
    ]
    assert abs(model_stats["logLikelihood"] - sm_result.llf) < _ABS_TOL


def test_logit_pseudo_r2_numerical(client, tables_store):
    """McFadden pseudoR2がstatsmodelsと一致することを確認"""
    (x1, x2, _, y_binary), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.Logit(y_binary, x_mat).fit(disp=False)

    model_stats = _get_output(client, LogitPayload().build())[
        "modelStatistics"
    ]
    assert abs(model_stats["pseudoRSquared"] - sm_result.prsquared) < _ABS_TOL


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
