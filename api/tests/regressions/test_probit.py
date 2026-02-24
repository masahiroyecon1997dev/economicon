"""Probit回帰テスト"""

import numpy as np
import statsmodels.api as sm
from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    generate_all_data,
    logit_payload,
    probit_payload,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-3

# パラメータ数定数
_N_PARAMS_WITH_CONST = 3

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
    return AnalysisResultStore().get_result(result_id).regression_output


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_probit_success(client, tables_store):
    """Probit回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=probit_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_probit_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, probit_payload())
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
    """Probit係数がstatsmodelsと一致することを確認"""
    (x1, x2, _, y_binary), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.Probit(y_binary, x_mat).fit(disp=False)

    params = _get_output(client, probit_payload())["parameters"]

    for i, exp_coef in enumerate(sm_result.params):
        assert abs(params[i]["coefficient"] - exp_coef) < _ABS_TOL, (
            f"Probit params[{i}]: {params[i]['coefficient']!r} != {exp_coef!r}"
        )


def test_probit_pseudo_r2_range(client, tables_store):
    """pseudoRSquaredが0以上1未満であることを確認"""
    model_stats = _get_output(client, probit_payload())["modelStatistics"]
    assert 0.0 <= model_stats["pseudoRSquared"] < 1.0


def test_probit_log_likelihood_negative(client, tables_store):
    """logLikelihoodが負値（≤0）であることを確認"""
    model_stats = _get_output(client, probit_payload())["modelStatistics"]
    assert model_stats["logLikelihood"] <= 0.0


def test_probit_log_likelihood_numerical(client, tables_store):
    """logLikelihoodがstatsmodelsと一致することを確認"""
    (x1, x2, _, y_binary), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.Probit(y_binary, x_mat).fit(disp=False)

    model_stats = _get_output(client, probit_payload())["modelStatistics"]
    assert abs(model_stats["logLikelihood"] - sm_result.llf) < _ABS_TOL


def test_probit_vs_logit_coefficient_magnitude(client, tables_store):
    """Probitの係数の絶対値はLogit係数の約0.55倍になることを確認（規則の目安）"""
    logit_params = _get_output(client, logit_payload())["parameters"]
    probit_params = _get_output(client, probit_payload())["parameters"]

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
    """McFadden pseudoR2がstatsmodelsと一致することを確認"""
    (x1, x2, _, y_binary), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.Probit(y_binary, x_mat).fit(disp=False)

    model_stats = _get_output(client, probit_payload())["modelStatistics"]
    assert abs(model_stats["pseudoRSquared"] - sm_result.prsquared) < _ABS_TOL


def test_probit_pvalues_range(client, tables_store):
    """p値が0以上1以下であることを確認"""
    params = _get_output(client, probit_payload())["parameters"]
    for p in params:
        assert 0.0 <= p["pValue"] <= 1.0
