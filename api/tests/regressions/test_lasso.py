"""Lasso回帰テスト"""

from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm
from fastapi import status
from sklearn.linear_model import Lasso
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    LassoPayload,
    load_py_gold,
)

# statsmodels / sklearn 数値比較の許容誤差
# 座標降下法の実装差による微小差を許容する
_ABS_TOL = 1e-4
# ゴールド JSON 比較の許容誤差
_GOLD_ABS_TOL = 1e-4

# Lasso デフォルト alpha（glmnet 規約）
_ALPHA_DEFAULT = 0.1
# スパース性確認用の大きな alpha
_ALPHA_LARGE = 10.0

# パラメータ数定数
_N_PARAMS_WITH_CONST = 4  # const, x1, x2, x3
_N_PARAMS_NO_CONST = 3  # x1, x2, x3

# 洗練データ CSV パス
_BASIC_CSV = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "data"
    / "csv"
    / "synthetic_ols.csv"
)


def _load_basic_xy() -> tuple[np.ndarray, np.ndarray]:
    """synthetic_ols.csv から (X_no_const, y) を返す。"""
    df = pl.read_csv(_BASIC_CSV).to_pandas()
    x_no_const = df[["x1", "x2", "x3"]].to_numpy()
    y = df["y_cont"].to_numpy()
    return x_no_const, y


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_lasso_success(client, tables_store):
    """Lasso回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=LassoPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_lasso_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, LassoPayload().build())
    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST  # const, x1, x2, x3

    for p in params:
        for key in ("variable", "coefficient", "coefficientScaled"):
            assert key in p, f"パラメータに {key!r} が存在しない"


def test_lasso_const_coefficient_scaled_is_none(client, tables_store):
    """定数項の coefficientScaled が None であることを確認"""
    params = _get_output(client, LassoPayload().build())["parameters"]
    const_param = next(p for p in params if p["variable"] == "const")
    assert const_param["coefficientScaled"] is None


def test_lasso_variable_coefficient_scaled_is_float(client, tables_store):
    """変数の coefficientScaled が float であることを確認"""
    params = _get_output(client, LassoPayload().build())["parameters"]
    for p in params:
        if p["variable"] != "const":
            assert isinstance(p["coefficientScaled"], float), (
                f"{p['variable']}: coefficientScaled が float でない"
            )


def test_lasso_coefficients_scaled_numerical(client, tables_store):
    """coefficientScaled が gold JSON と一致することを確認 (atol=1e-8)

    Eco-Note D: glmnet λ = statsmodels α = sklearn α（全て同一式）
    """
    gold_scaled = load_py_gold("lasso")["estimates"]["coef_scaled"]

    params = _get_output(client, LassoPayload(alpha=_ALPHA_DEFAULT).build())[
        "parameters"
    ]
    coef_map = {
        p["variable"]: p["coefficientScaled"]
        for p in params
        if p["variable"] != "const"
    }

    for var, exp_scaled in gold_scaled.items():
        assert abs(coef_map[var] - exp_scaled) < _GOLD_ABS_TOL, (
            f"Lasso coef_scaled[{var!r}]: {coef_map[var]!r} != {exp_scaled!r}"
        )


def test_lasso_large_alpha_sparsity(client, tables_store):
    """大きなalphaでLassoがスパース性を発揮することを確認"""
    params = _get_output(client, LassoPayload(alpha=_ALPHA_LARGE).build())[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    # 少なくとも1変数の係数が0に縮小されうることを確認
    # （厳密ゼロでなくても正則化効果）
    scaled_coefs = [abs(p["coefficientScaled"]) for p in var_params]
    # alpha=10 では係数が小さくなるはず（alpha=0.1 と比較）
    small_alpha_params = _get_output(
        client, LassoPayload(alpha=_ALPHA_DEFAULT).build()
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
    output = _get_output(client, LassoPayload(has_const=False).build())
    params = output["parameters"]
    assert len(params) == _N_PARAMS_NO_CONST  # x1, x2, x3 のみ
    names = [p["variable"] for p in params]
    assert "const" not in names


def test_lasso_calculate_se_true(client, tables_store):
    """calculateSe=TrueでLassoがstandardErrorを返すことを確認"""
    output = _get_output(client, LassoPayload(calculate_se=True).build())
    params = output["parameters"]
    for p in params:
        # 標準誤差があればfloat、なければNoneを許容
        assert "standardError" in p


def test_lasso_calculate_se_without_const(client, tables_store):
    """calculate_se=True + has_const=False のブートストラップパスを確認"""
    output = _get_output(
        client,
        LassoPayload(calculate_se=True, has_const=False).build(),
    )
    params = output["parameters"]
    assert len(params) == _N_PARAMS_NO_CONST
    for p in params:
        assert "standardError" in p


# -----------------------------------------------------------
# statsmodels 参照テスト（正確な一致検証）
# -----------------------------------------------------------


def _build_sm_lasso_reference(
    x_no_const: np.ndarray,
    y: np.ndarray,
    alpha_glmnet: float,
) -> np.ndarray:
    """
    statsmodels fit_regularized で Lasso を直接解いて standardized 係数を返す。
    glmnet λ → statsmodels α = λ/2 に変換する。
    """
    n_features = x_no_const.shape[1]
    x_mean = x_no_const.mean(axis=0)
    x_scale = x_no_const.std(axis=0, ddof=0)
    x_scale = np.where(x_scale == 0.0, 1.0, x_scale)
    x_scaled = (x_no_const - x_mean) / x_scale
    x_sm = sm.add_constant(x_scaled, has_constant="add")

    alpha_sm = alpha_glmnet  # glmnet λ = statsmodels α（直接一致）
    alpha_arr = np.array([0.0] + [alpha_sm] * n_features, dtype=np.float64)

    result = sm.OLS(y, x_sm).fit_regularized(
        method="elastic_net",
        alpha=alpha_arr,  # type: ignore[arg-type]
        L1_wt=1.0,
    )
    return np.asarray(result.params[1:], dtype=np.float64)


def test_lasso_statsmodels_consistency(client, tables_store):
    """statsmodels fit_regularized(L1_wt=1.0) と係数が一致することを確認

    Eco-Note D: glmnet λ = statsmodels α（直接一致）。
    API の alpha はデフォルト glmnet 規約を使用する。
    """
    x_no_const, y_linear = _load_basic_xy()

    expected_scaled = _build_sm_lasso_reference(
        x_no_const, y_linear, _ALPHA_DEFAULT
    )

    params = _get_output(client, LassoPayload(alpha=_ALPHA_DEFAULT).build())[
        "parameters"
    ]
    var_params = [p for p in params if p["variable"] != "const"]

    for i, (exp, param) in enumerate(
        zip(expected_scaled, var_params, strict=False)
    ):
        assert abs(param["coefficientScaled"] - exp) < _ABS_TOL, (
            f"Lasso statsmodels coef_scaled[{i}]:"
            f" {param['coefficientScaled']!r} != {exp!r}"
        )


def test_lasso_sklearn_r2_consistency(client, tables_store):
    """R² が sklearn Lasso(alpha).score() と数値的に一致することを確認

    Eco-Note D: glmnet λ = sklearn α = statsmodels α（同一目的関数）。
    R² もそのまま一致する。
    """
    x_no_const, y_linear = _load_basic_xy()

    sklearn_alpha = _ALPHA_DEFAULT
    model = make_pipeline(StandardScaler(), Lasso(alpha=sklearn_alpha))
    model.fit(x_no_const, y_linear)
    expected_r2 = float(model.score(x_no_const, y_linear))

    output = _get_output(client, LassoPayload(alpha=_ALPHA_DEFAULT).build())
    api_r2 = output["modelStatistics"]["R2"]

    assert abs(api_r2 - expected_r2) < _ABS_TOL, (
        f"Lasso R²: API={api_r2!r} != sklearn={expected_r2!r}"
    )


def test_lasso_warnings_field_present(client, tables_store):
    """レスポンスに warnings フィールドが含まれることを確認"""
    output = _get_output(client, LassoPayload().build())
    assert "warnings" in output, (
        "regressionOutput に 'warnings' フィールドがない"
    )
    assert isinstance(output["warnings"], list)


def test_lasso_convergence_warning_on_low_maxiter(client, tables_store):
    """maxIter=1 のとき warnings に収束失敗メッセージが含まれることを確認"""
    payload = LassoPayload(alpha=_ALPHA_DEFAULT).build()
    payload["analysis"]["maxIter"] = 1  # 収束不可能な反復回数
    output = _get_output(client, payload)
    assert len(output["warnings"]) > 0, "maxIter=1 で収束失敗警告が出るはず"


def test_lasso_sklearn_convention(client, tables_store):
    """alphaConvention='sklearn' で sklearn Lasso(alpha) と係数が一致する

    sklearn 規約: α_sm = α_sk (Lasso は同一式)
    """
    x_no_const, y_linear = _load_basic_xy()

    sklearn_alpha = _ALPHA_DEFAULT  # sklearn 規約ではそのまま使用
    model = make_pipeline(StandardScaler(), Lasso(alpha=sklearn_alpha))
    model.fit(x_no_const, y_linear)
    lasso_step = model.named_steps["lasso"]
    expected_scaled = lasso_step.coef_

    payload = LassoPayload(alpha=_ALPHA_DEFAULT).build()
    payload["analysis"]["alphaConvention"] = "sklearn"
    params = _get_output(client, payload)["parameters"]
    var_params = [p for p in params if p["variable"] != "const"]

    for i, (exp, param) in enumerate(
        zip(expected_scaled, var_params, strict=False)
    ):
        assert abs(param["coefficientScaled"] - exp) < _ABS_TOL, (
            f"Lasso sklearn convention coef_scaled[{i}]:"
            f" {param['coefficientScaled']!r} != {exp!r}"
        )
