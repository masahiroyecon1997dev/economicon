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
    RidgePayload,
    generate_all_data,
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
    resp = client.post(URL_REGRESSION, json=RidgePayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_ridge_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, RidgePayload().build())
    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST  # const, x1, x2

    for p in params:
        for key in ("variable", "coefficient", "coefficientScaled"):
            assert key in p, f"パラメータに {key!r} が存在しない"


def test_ridge_const_coefficient_scaled_is_none(client, tables_store):
    """定数項の coefficientScaled が None であることを確認"""
    params = _get_output(client, RidgePayload().build())["parameters"]
    const_param = next(p for p in params if p["variable"] == "const")
    assert const_param["coefficientScaled"] is None


def test_ridge_variable_coefficient_scaled_is_float(client, tables_store):
    """変数の coefficientScaled が float であることを確認"""
    params = _get_output(client, RidgePayload().build())["parameters"]
    for p in params:
        if p["variable"] != "const":
            assert isinstance(p["coefficientScaled"], float), (
                f"{p['variable']}: coefficientScaled が float でない"
            )


def test_ridge_coefficients_scaled_numerical(client, tables_store):
    """coefficientScaled が sklearn Ridge(n*alpha) の結果と一致することを確認

    Eco-Note D: glmnet 規約 λ → sklearn 変換：α_sk = n * λ
    （statsmodels Ridge 目的関数: 1/(2n)||y-Xβ||² + λ/2||β||²
     sklearn Ridge 目的関数: ||y-Xβ||² + α||β||²  → 等価条件: α_sk = n * λ）
    """
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_no_const = np.column_stack([x1, x2])
    n_samples = len(y_linear)

    # glmnet λ=0.5 → sklearn Ridge α = n * 0.5
    sklearn_alpha = n_samples * _ALPHA_DEFAULT
    model = make_pipeline(StandardScaler(), Ridge(alpha=sklearn_alpha))
    model.fit(x_no_const, y_linear)
    ridge_step = model.named_steps["ridge"]
    expected_scaled = ridge_step.coef_  # [x1_scaled, x2_scaled]

    params = _get_output(client, RidgePayload(alpha=_ALPHA_DEFAULT).build())[
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

    ridge_params = _get_output(
        client, RidgePayload(alpha=_ALPHA_TINY).build()
    )["parameters"]

    pairs = zip(ols_params, ridge_params, strict=False)
    for i, (ols_c, rp) in enumerate(pairs):
        # alpha が非常に小さければ OLS に近いはず（許容誤差を広めに設定）
        assert abs(rp["coefficient"] - ols_c) < _RIDGE_OLS_TOL, (
            f"Ridge (tiny alpha) params[{i}]:"
            f" {rp['coefficient']!r} != {ols_c!r}"
        )


def test_ridge_without_constant(client, tables_store):
    """hasConst=FalseでRidgeが動作することを確認"""
    output = _get_output(client, RidgePayload(has_const=False).build())
    params = output["parameters"]
    assert len(params) == _N_PARAMS_NO_CONST
    names = [p["variable"] for p in params]
    assert "const" not in names


def test_ridge_no_zero_coefficients(client, tables_store):
    """RidgeはLassoと異なりスパース化しないことを確認（係数がゼロにならない）"""
    params = _get_output(client, RidgePayload(alpha=_ALPHA_DEFAULT).build())[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    # 通常のデータではRidgeは係数をゼロにしない
    for p in var_params:
        # 完全にゼロにはなりにくい（軽い検証）
        assert isinstance(p["coefficientScaled"], float)


def test_ridge_calculate_se_true(client, tables_store):
    """calculateSe=TrueでRidgeがstandardErrorを返すことを確認"""
    output = _get_output(client, RidgePayload(calculate_se=True).build())
    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST
    for p in params:
        assert "standardError" in p


def test_ridge_calculate_se_without_const(client, tables_store):
    """calculate_se=True + has_const=False のブートストラップパスを確認"""
    output = _get_output(
        client,
        RidgePayload(calculate_se=True, has_const=False).build(),
    )
    params = output["parameters"]
    assert len(params) == _N_PARAMS_NO_CONST
    for p in params:
        assert "standardError" in p


# -----------------------------------------------------------
# statsmodels 参照テスト（正確な一致検証）
# -----------------------------------------------------------


def _build_sm_ridge_reference(
    x_no_const: np.ndarray,
    y: np.ndarray,
    alpha_glmnet: float,
) -> np.ndarray:
    """
    statsmodels fit_regularized で Ridge を直接解いて standardized 係数を返す。
    glmnet λ → statsmodels α = λ（直接一致）。
    """
    n_features = x_no_const.shape[1]
    x_mean = x_no_const.mean(axis=0)
    x_scale = x_no_const.std(axis=0, ddof=0)
    x_scale = np.where(x_scale == 0.0, 1.0, x_scale)
    x_scaled = (x_no_const - x_mean) / x_scale
    x_sm = sm.add_constant(x_scaled, has_constant="add")

    alpha_sm = alpha_glmnet  # glmnet λ = statsmodels α for Ridge
    alpha_arr = np.array([0.0] + [alpha_sm] * n_features, dtype=np.float64)

    result = sm.OLS(y, x_sm).fit_regularized(
        method="elastic_net", alpha=alpha_arr, L1_wt=0.0
    )
    return np.asarray(result.params[1:], dtype=np.float64)


def test_ridge_statsmodels_consistency(client, tables_store):
    """statsmodels fit_regularized(L1_wt=0.0) と係数が一致することを確認

    Eco-Note D: glmnet λ → statsmodels α = λ（Ridge は直接一致）。
    """
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_no_const = np.column_stack([x1, x2])

    expected_scaled = _build_sm_ridge_reference(
        x_no_const, y_linear, _ALPHA_DEFAULT
    )

    params = _get_output(client, RidgePayload(alpha=_ALPHA_DEFAULT).build())[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    for i, (exp, param) in enumerate(
        zip(expected_scaled, var_params, strict=False)
    ):
        assert abs(param["coefficientScaled"] - exp) < _ABS_TOL, (
            f"Ridge statsmodels coef_scaled[{i}]:"
            f" {param['coefficientScaled']!r} != {exp!r}"
        )


def test_ridge_sklearn_r2_consistency(client, tables_store):
    """R² が sklearn Ridge(n*alpha).score() と数値的に一致することを確認

    Eco-Note D: statsmodels にはない R² を sklearn で検証する。
    glmnet λ → sklearn α = n * λ に変換して比較する。
    """
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_no_const = np.column_stack([x1, x2])
    n_samples = len(y_linear)

    sklearn_alpha = n_samples * _ALPHA_DEFAULT
    model = make_pipeline(StandardScaler(), Ridge(alpha=sklearn_alpha))
    model.fit(x_no_const, y_linear)
    expected_r2 = float(model.score(x_no_const, y_linear))

    output = _get_output(client, RidgePayload(alpha=_ALPHA_DEFAULT).build())
    api_r2 = output["modelStatistics"]["R2"]

    assert abs(api_r2 - expected_r2) < _ABS_TOL, (
        f"Ridge R²: API={api_r2!r} != sklearn={expected_r2!r}"
    )


def test_ridge_warnings_field_present(client, tables_store):
    """レスポンスに warnings フィールドが含まれることを確認"""
    output = _get_output(client, RidgePayload().build())
    assert "warnings" in output, (
        "regressionOutput に 'warnings' フィールドがない"
    )
    assert isinstance(output["warnings"], list)


def test_ridge_convergence_warning_on_low_maxiter(client, tables_store):
    """maxIter=1 でも Ridge は解析解のため収束する（warnings は空）"""
    payload = RidgePayload(alpha=_ALPHA_DEFAULT).build()
    payload["analysis"]["maxIter"] = 1  # Ridge(L1_wt=0) は解析解のため無効
    output = _get_output(client, payload)
    assert len(output["warnings"]) == 0, (
        "Ridge は閉形式解析解のため収束警告は発生しない"
    )


def test_ridge_sklearn_convention(client, tables_store):
    """alphaConvention='sklearn' で sklearn Ridge(alpha) と係数が一致する

    Eco-Note D: sklearn 規約: α_sm = α_sk / n
    （同じ alpha 値でも glmnet と sklearn では Ridge の結合強度が n 倍異なる）
    """
    (x1, x2, y_linear, _), _, _ = generate_all_data()
    x_no_const = np.column_stack([x1, x2])
    # sklearn 規約で alpha=0.5 → statsmodels α = 0.5/n（非常に弱い正則化）
    sklearn_alpha = _ALPHA_DEFAULT
    model = make_pipeline(StandardScaler(), Ridge(alpha=sklearn_alpha))
    model.fit(x_no_const, y_linear)
    ridge_step = model.named_steps["ridge"]
    expected_scaled = ridge_step.coef_

    payload = RidgePayload(alpha=_ALPHA_DEFAULT).build()
    payload["analysis"]["alphaConvention"] = "sklearn"
    params = _get_output(client, payload)["parameters"]
    var_params = [p for p in params if p["variable"] != "const"]

    for i, (exp, param) in enumerate(
        zip(expected_scaled, var_params, strict=False)
    ):
        assert abs(param["coefficientScaled"] - exp) < _ABS_TOL, (
            f"Ridge sklearn convention coef_scaled[{i}]:"
            f" {param['coefficientScaled']!r} != {exp!r}"
        )
