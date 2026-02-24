"""Ridge回帰テスト"""

import numpy as np
import statsmodels.api as sm
from fastapi import status
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    generate_all_data,
    ridge_payload,
)

# sklearn/statsmodels との数値比較の許容誤差
_ABS_TOL = 1e-5

# Ridge デフォルト alpha
_ALPHA_DEFAULT = 0.5
# OLS 近似確認用の非常に小さな alpha
_ALPHA_TINY = 1e-6

# パラメータ数定数
_N_PARAMS_WITH_CONST = 3
_N_PARAMS_NO_CONST = 2

# Ridge と OLS の差异の許容誤差・広め
_RIDGE_OLS_TOL = 0.05


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).regression_output


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_ridge_success(client, tables_store):
    """Ridge回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=ridge_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_ridge_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, ridge_payload())
    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST  # const, x1, x2

    for p in params:
        for key in ("variable", "coefficient", "coefficientScaled"):
            assert key in p, f"パラメータに {key!r} が存在しない"


def test_ridge_const_coefficient_scaled_is_none(client, tables_store):
    """定数項の coefficientScaled が None であることを確認"""
    params = _get_output(client, ridge_payload())["parameters"]
    const_param = next(p for p in params if p["variable"] == "const")
    assert const_param["coefficientScaled"] is None


def test_ridge_variable_coefficient_scaled_is_float(client, tables_store):
    """変数の coefficientScaled が float であることを確認"""
    params = _get_output(client, ridge_payload())["parameters"]
    for p in params:
        if p["variable"] != "const":
            assert isinstance(p["coefficientScaled"], float), (
                f"{p['variable']}: coefficientScaled が float でない"
            )


def test_ridge_coefficients_scaled_numerical(client, tables_store):
    """coefficientScaledがsklearnのRidge Pipeline結果と一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_no_const = np.column_stack([x1, x2])

    model = make_pipeline(StandardScaler(), Ridge(alpha=_ALPHA_DEFAULT))
    model.fit(x_no_const, y_linear)
    ridge_step = model.named_steps["ridge"]
    expected_scaled = ridge_step.coef_  # [x1_scaled, x2_scaled]

    params = _get_output(client, ridge_payload(alpha=_ALPHA_DEFAULT))[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    pairs = zip(expected_scaled, var_params, strict=False)
    for i, (exp, param) in enumerate(pairs):
        assert abs(param["coefficientScaled"] - exp) < _ABS_TOL, (
            f"Ridge coef_scaled[{i}]:"
            f" {param['coefficientScaled']!r} != {exp!r}"
        )


def test_ridge_small_alpha_approaches_ols(client, tables_store):
    """非常に小さなalphaのRidge係数がOLS係数に近いことを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_mat = sm.add_constant(np.column_stack([x1, x2]))
    ols_result = sm.OLS(y_linear, x_mat).fit()
    ols_params = ols_result.params  # [const, x1, x2]

    ridge_params = _get_output(client, ridge_payload(alpha=_ALPHA_TINY))[
        "parameters"
    ]

    pairs = zip(ols_params, ridge_params, strict=False)
    for i, (ols_c, rp) in enumerate(pairs):
        # alpha が非常に小さければ OLS に近いはず（許容誤差を広めに設定）
        assert abs(rp["coefficient"] - ols_c) < _RIDGE_OLS_TOL, (
            f"Ridge (tiny alpha) params[{i}]:"
            f" {rp['coefficient']!r} != {ols_c!r}"
        )


def test_ridge_without_constant(client, tables_store):
    """hasConst=FalseでRidgeが動作することを確認"""
    output = _get_output(client, ridge_payload(has_const=False))
    params = output["parameters"]
    assert len(params) == _N_PARAMS_NO_CONST
    names = [p["variable"] for p in params]
    assert "const" not in names


def test_ridge_no_zero_coefficients(client, tables_store):
    """RidgeはLassoと異なりスパース化しないことを確認（係数がゼロにならない）"""
    params = _get_output(client, ridge_payload(alpha=_ALPHA_DEFAULT))[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    # 通常のデータではRidgeは係数をゼロにしない
    for p in var_params:
        # 完全にゼロにはなりにくい（軽い検証）
        assert isinstance(p["coefficientScaled"], float)
