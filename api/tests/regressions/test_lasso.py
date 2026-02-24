"""Lasso回帰テスト"""

import numpy as np
from fastapi import status
from sklearn.linear_model import Lasso
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    generate_all_data,
    lasso_payload,
)

# sklearn との数値比較の許容誤差
_ABS_TOL = 1e-5

# Lasso デフォルト alpha
_ALPHA_DEFAULT = 0.1
# スパース性確認用の大きな alpha
_ALPHA_LARGE = 10.0

# パラメータ数定数
_N_PARAMS_WITH_CONST = 3
_N_PARAMS_NO_CONST = 2


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).regression_output


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_lasso_success(client, tables_store):
    """Lasso回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=lasso_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_lasso_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, lasso_payload())
    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST  # const, x1, x2

    for p in params:
        for key in ("variable", "coefficient", "coefficientScaled"):
            assert key in p, f"パラメータに {key!r} が存在しない"


def test_lasso_const_coefficient_scaled_is_none(client, tables_store):
    """定数項の coefficientScaled が None であることを確認"""
    params = _get_output(client, lasso_payload())["parameters"]
    const_param = next(p for p in params if p["variable"] == "const")
    assert const_param["coefficientScaled"] is None


def test_lasso_variable_coefficient_scaled_is_float(client, tables_store):
    """変数の coefficientScaled が float であることを確認"""
    params = _get_output(client, lasso_payload())["parameters"]
    for p in params:
        if p["variable"] != "const":
            assert isinstance(p["coefficientScaled"], float), (
                f"{p['variable']}: coefficientScaled が float でない"
            )


def test_lasso_coefficients_scaled_numerical(client, tables_store):
    """coefficientScaledがsklearnのLasso Pipeline結果と一致することを確認"""
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_no_const = np.column_stack([x1, x2])  # 定数項なし

    model = make_pipeline(StandardScaler(), Lasso(alpha=_ALPHA_DEFAULT))
    model.fit(x_no_const, y_linear)
    lasso_step = model.named_steps["lasso"]
    expected_scaled = lasso_step.coef_  # [x1_scaled, x2_scaled]

    params = _get_output(client, lasso_payload(alpha=_ALPHA_DEFAULT))[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    pairs = zip(expected_scaled, var_params, strict=False)
    for i, (exp, param) in enumerate(pairs):
        assert abs(param["coefficientScaled"] - exp) < _ABS_TOL, (
            f"Lasso coef_scaled[{i}]:"
            f" {param['coefficientScaled']!r} != {exp!r}"
        )


def test_lasso_large_alpha_sparsity(client, tables_store):
    """大きなalphaでLassoがスパース性を発揮することを確認"""
    params = _get_output(client, lasso_payload(alpha=_ALPHA_LARGE))[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    # 少なくとも1変数の係数が0に縮小されうることを確認
    # （厳密ゼロでなくても正則化効果）
    scaled_coefs = [abs(p["coefficientScaled"]) for p in var_params]
    # alpha=10 では係数が小さくなるはず（alpha=0.1 と比較）
    small_alpha_params = _get_output(
        client, lasso_payload(alpha=_ALPHA_DEFAULT)
    )["parameters"]
    small_var_params = [
        p for p in small_alpha_params if p["variable"] != "const"
    ]
    small_scaled = [abs(p["coefficientScaled"]) for p in small_var_params]

    for large, small in zip(scaled_coefs, small_scaled, strict=False):
        assert large <= small + _ABS_TOL, (
            f"alpha大 の係数 {large} が alpha小 の {small} より大きい"
        )


def test_lasso_without_constant(client, tables_store):
    """hasConst=FalseでLassoが動作することを確認"""
    output = _get_output(client, lasso_payload(has_const=False))
    params = output["parameters"]
    assert len(params) == _N_PARAMS_NO_CONST  # x1, x2 のみ
    names = [p["variable"] for p in params]
    assert "const" not in names


def test_lasso_calculate_se_true(client, tables_store):
    """calculateSe=TrueでLassoがstandardErrorを返すことを確認"""
    output = _get_output(client, lasso_payload(calculate_se=True))
    params = output["parameters"]
    for p in params:
        # 標準誤差があればfloat、なければNoneを許容
        assert "standardError" in p


def test_lasso_calculate_se_without_const(client, tables_store):
    """calculate_se=True + has_const=False のブートストラップパスを確認"""
    output = _get_output(
        client, lasso_payload(calculate_se=True, has_const=False)
    )
    params = output["parameters"]
    assert len(params) == _N_PARAMS_NO_CONST
    for p in params:
        assert "standardError" in p
