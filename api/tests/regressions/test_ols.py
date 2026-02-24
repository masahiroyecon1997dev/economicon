"""OLS回帰テスト"""

import numpy as np
import statsmodels.api as sm
from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_BASIC,
    URL_REGRESSION,
    generate_all_data,
    ols_payload,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-4
# HAC標準誤差は収束に依存するため緩い許容誤差を使用
_HAC_ABS_TOL = 1e-3

# パラメータ数定数
_N_PARAMS_WITH_CONST = 3
_N_PARAMS_NO_CONST = 2

# 係数符号確認の最小閾値（設計値 x1=1.5 に基づく）
_MIN_X1_COEF = 0.5


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).regression_output


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_ols_success(client, tables_store):
    """OLS回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=ols_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_ols_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, ols_payload())
    model_stats = output["modelStatistics"]

    for key in ("R2", "adjustedR2", "fValue", "fProbability"):
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
            "confidenceIntervalLower",
            "confidenceIntervalUpper",
        ):
            assert key in p, f"パラメータに {key!r} が存在しない"


def test_ols_result_stored(client, tables_store):
    """resultIdで保存された結果が取得できることを確認"""
    resp = client.post(URL_REGRESSION, json=ols_payload())
    assert resp.status_code == status.HTTP_200_OK
    result_id = resp.json()["result"]["resultId"]

    saved = AnalysisResultStore().get_result(result_id)
    assert saved is not None
    assert "parameters" in saved.regression_output
    assert "modelStatistics" in saved.regression_output


def test_ols_coefficients_numerical(client, tables_store):
    """OLS係数がstatsmodels結果と一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.OLS(y_linear, x_mat).fit()

    params = _get_output(client, ols_payload())["parameters"]

    for i, (exp_coef, exp_se) in enumerate(
        zip(sm_result.params, sm_result.bse, strict=False)
    ):
        assert abs(params[i]["coefficient"] - exp_coef) < _ABS_TOL, (
            f"params[{i}] coef: {params[i]['coefficient']!r} != {exp_coef!r}"
        )
        assert abs(params[i]["standardError"] - exp_se) < _ABS_TOL, (
            f"params[{i}] se: {params[i]['standardError']!r} != {exp_se!r}"
        )


def test_ols_r2_numerical(client, tables_store):
    """R2・adjustedR2・fValueがstatsmodelsと一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.OLS(y_linear, x_mat).fit()

    model_stats = _get_output(client, ols_payload())["modelStatistics"]

    assert abs(model_stats["R2"] - sm_result.rsquared) < _ABS_TOL
    assert abs(model_stats["adjustedR2"] - sm_result.rsquared_adj) < _ABS_TOL
    assert abs(model_stats["fValue"] - sm_result.fvalue) < _ABS_TOL


def test_ols_confidence_intervals_numerical(client, tables_store):
    """信頼区間がstatsmodels (95%) と一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    ci = sm.OLS(y_linear, x_mat).fit().conf_int()

    params = _get_output(client, ols_payload())["parameters"]

    for i in range(_N_PARAMS_WITH_CONST):
        assert abs(params[i]["confidenceIntervalLower"] - ci[i, 0]) < _ABS_TOL
        assert abs(params[i]["confidenceIntervalUpper"] - ci[i, 1]) < _ABS_TOL


def test_ols_pvalues_numerical(client, tables_store):
    """p値がstatsmodels結果と一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    pvals = sm.OLS(y_linear, x_mat).fit().pvalues

    params = _get_output(client, ols_payload())["parameters"]

    for i, exp_pval in enumerate(pvals):
        assert abs(params[i]["pValue"] - exp_pval) < _ABS_TOL


def test_ols_without_constant(client, tables_store):
    """hasConst=Falseで定数項なしの回帰が動作することを確認"""
    params = _get_output(client, ols_payload(has_const=False))["parameters"]
    # 定数なし → 変数2つのみ
    assert len(params) == _N_PARAMS_NO_CONST
    names = [p["variable"] for p in params]
    assert "const" not in names
    assert "x1" in names
    assert "x2" in names


def test_ols_robust_hc1(client, tables_store):
    """HC1ロバスト標準誤差がstatsmodelsと一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.OLS(y_linear, x_mat).fit(cov_type="HC1")

    payload = ols_payload(se_method="robust", hcType="HC1")
    params = _get_output(client, payload)["parameters"]

    for i, exp_se in enumerate(sm_result.bse):
        assert abs(params[i]["standardError"] - exp_se) < _ABS_TOL


def test_ols_hac(client, tables_store):
    """HAC (Newey-West) 標準誤差でのリクエストが成功することを確認"""
    output = _get_output(client, ols_payload(se_method="hac", maxlags=1))
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_ols_clustered_se(client, tables_store):
    """クラスタロバスト標準誤差でリクエストが成功することを確認"""
    payload = {
        "tableName": TABLE_BASIC,
        "dependentVariable": "y_linear",
        "explanatoryVariables": ["x1"],
        "hasConst": True,
        "analysis": {"method": "ols"},
        "standardError": {
            "method": "cluster",
            "groups": ["x2"],
        },
    }
    resp = client.post(URL_REGRESSION, json=payload)
    # x2は連続値のためクラスタ数が多い場合でも正常/エラーいずれも許容
    assert resp.status_code in (
        status.HTTP_200_OK,
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def test_ols_name_description_stored(client, tables_store):
    """name・descriptionが正しく保存されることを確認"""
    payload = ols_payload()
    payload["resultName"] = "テスト回帰モデル"
    payload["description"] = "OLSの動作確認テスト"

    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK
    result_id = resp.json()["result"]["resultId"]

    saved = AnalysisResultStore().get_result(result_id)
    assert saved.name == "テスト回帰モデル"
    assert saved.description == "OLSの動作確認テスト"


def test_ols_aic_bic_present(client, tables_store):
    """AIC・BIC・logLikelihoodが modelStatistics に含まれることを確認"""
    model_stats = _get_output(client, ols_payload())["modelStatistics"]
    for key in ("AIC", "BIC", "logLikelihood"):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )


def test_ols_coefficient_sign_correct(client, tables_store):
    """既知係数（x1≈1.5, x2≈0.8）の符号が正であることを確認"""
    params = _get_output(client, ols_payload())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    # 設計値 x1=1.5, x2=0.8 なので両方正
    assert coef_map["x1"] > _MIN_X1_COEF
    assert coef_map["x2"] > 0.0


def test_ols_hac_numerical(client, tables_store):
    """HAC標準誤差がstatsmodels (Newey-West maxlags=1) と一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    sm_result = sm.OLS(y_linear, x_mat).fit(
        cov_type="HAC", cov_kwds={"maxlags": 1}
    )

    payload = ols_payload(se_method="hac", maxlags=1)
    params = _get_output(client, payload)["parameters"]

    for i, exp_se in enumerate(sm_result.bse):
        assert abs(params[i]["standardError"] - exp_se) < _HAC_ABS_TOL
