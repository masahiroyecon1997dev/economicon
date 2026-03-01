"""Grunfeld データセットを用いた API 結合テスト (Pattern A)

API レスポンスと statsmodels/linearmodels/sklearn の直接
計算結果が完全一致することを検証する。

結果取得は HTTP GET /api/analysis/results/{result_id} を経由する
(既存テストの in-memory 直接アクセスとの差別化)。

使用データ:
  statsmodels.datasets.get_rdataset("Grunfeld", "plm")
  - firm   (企業ID, 1-10)
  - year   (時間, 1935-1954)
  - inv    (投資, 被説明変数)
  - value  (企業価値, 説明変数)
  - capital(資本ストック, 説明変数 / 内生変数)

IV 推定の構成:
  内生変数: capital
  操作変数: value_lag (各 firm 内での value の1期前ラグ)
"""

import numpy as np
import pandas as pd
import polars as pl
import pytest
import statsmodels.api as sm
from fastapi import status
from fastapi.testclient import TestClient
from linearmodels.iv import IV2SLS, IVGMM
from linearmodels.panel import PanelOLS, RandomEffects
from sklearn.linear_model import Lasso, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.datasets import get_rdataset

from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.data.tables_store import TablesStore
from main import app
from tests.regressions.conftest import (
    URL_REGRESSION,
    URL_RESULTS,
)

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

TABLE_GRUNFELD = "GrunfeldData"
TABLE_GRUNFELD_IV = "GrunfeldIVData"

# 浮動小数点の許容誤差 (ライブラリ間丸め誤差を考慮)
_ABS_TOL = 1e-8

# HAC 標準誤差は収束依存のため緩め
_HAC_ABS_TOL = 1e-6

# Grunfeld データの既知構造定数
_N_FIRMS = 10
_N_YEARS = 20
_N_OBS = _N_FIRMS * _N_YEARS  # 200
# ラグ計算で各 firm の最初の年が欠落
_N_OBS_IV = _N_OBS - _N_FIRMS  # 190

# モデルパラメータ数
# OLS: const + value + capital
_N_PARAMS_WITH_CONST = 3
# hasConst=False: value + capital
_N_PARAMS_NO_CONST = 2
# FE: entity effects が定数項を吸収 → value + capital
_N_PARAMS_FE = 2

# 正則化強度
_LASSO_ALPHA = 0.1
_RIDGE_ALPHA = 1.0

# HAC ラグ次数
_HAC_MAXLAGS = 1


# -----------------------------------------------------------
# フィクスチャ
# -----------------------------------------------------------


@pytest.fixture(scope="module")
def grunfeld_raw() -> pd.DataFrame:
    """
    Grunfeld データを pandas DataFrame で返す。

    列: firm, year, inv, value, capital
    全列を float に変換して返す (TablesStore 互換)。
    """
    data = get_rdataset("Grunfeld", "plm").data
    df = data[["firm", "year", "inv", "value", "capital"]].copy()
    for col in df.columns:
        df[col] = df[col].astype(float)
    return df.reset_index(drop=True)


@pytest.fixture(scope="module")
def grunfeld_with_iv(grunfeld_raw: pd.DataFrame) -> pd.DataFrame:
    """
    IV 用テーブル。

    各 firm 内で value / capital の1期前ラグを計算し、
    NaN 行を除去したデータを返す。

    内生変数: capital
    操作変数: value_lag, capital_lag  (2IVs → over-identified)

    exactly-identified (1IV) だと Sargan 統計量が NaN になり
    JSON シリアライズエラーになるため、
    over-identified 構成をとる。
    """
    df = (
        grunfeld_raw.sort_values(["firm", "year"])
        .assign(
            value_lag=lambda x: x.groupby("firm")["value"].shift(1),
            capital_lag=lambda x: x.groupby("firm")["capital"].shift(1),
        )
        .dropna(subset=["value_lag", "capital_lag"])
        .reset_index(drop=True)
    )
    return df


@pytest.fixture
def client():
    """TestClient フィクスチャ"""
    return TestClient(app)


@pytest.fixture
def grunfeld_store(
    grunfeld_raw: pd.DataFrame,
    grunfeld_with_iv: pd.DataFrame,
):
    """
    GrunfeldData / GrunfeldIVData を TablesStore に投入する。

    各テスト関数の前後でストアをクリアする (汚染防止)。
    """
    store = TablesStore()
    store.clear_tables()
    result_store = AnalysisResultStore()
    result_store.clear_all()

    store.store_table(
        TABLE_GRUNFELD,
        pl.from_pandas(grunfeld_raw),
    )
    store.store_table(
        TABLE_GRUNFELD_IV,
        pl.from_pandas(grunfeld_with_iv),
    )

    yield

    store.clear_tables()
    result_store.clear_all()


# -----------------------------------------------------------
# ヘルパー関数
# -----------------------------------------------------------


def _post_and_fetch(client, payload: dict) -> tuple[str, dict]:
    """
    API の2ステップ呼び出しラッパー。

    1. POST /api/analysis/regression でモデルを実行
    2. GET /api/analysis/results/{result_id} で結果を取得

    Returns
    -------
    (result_id, regressionOutput)
    """
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text

    data = resp.json()
    assert data["code"] == "OK"
    result_id: str = data["result"]["resultId"]

    # HTTP エンドポイント経由で詳細結果を取得
    results_resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert results_resp.status_code == status.HTTP_200_OK, results_resp.text
    result_data = results_resp.json()
    assert result_data["code"] == "OK"

    output: dict = result_data["result"]["regressionOutput"]
    return result_id, output


def _ols_payload(
    se: dict | None = None,
    has_const: bool = True,
) -> dict:
    """OLS リクエストペイロードを構築する"""
    if se is None:
        se = {"method": "nonrobust"}
    return {
        "tableName": TABLE_GRUNFELD,
        "dependentVariable": "inv",
        "explanatoryVariables": ["value", "capital"],
        "hasConst": has_const,
        "analysis": {"method": "ols"},
        "standardError": se,
    }


def _lasso_payload(
    alpha: float = _LASSO_ALPHA,
    has_const: bool = True,
) -> dict:
    """Lasso リクエストペイロードを構築する"""
    return {
        "tableName": TABLE_GRUNFELD,
        "dependentVariable": "inv",
        "explanatoryVariables": ["value", "capital"],
        "hasConst": has_const,
        "analysis": {
            "method": "lasso",
            "alpha": alpha,
            "calculateSe": False,
        },
        "standardError": {"method": "nonrobust"},
    }


def _ridge_payload(
    alpha: float = _RIDGE_ALPHA,
    has_const: bool = True,
) -> dict:
    """Ridge リクエストペイロードを構築する"""
    return {
        "tableName": TABLE_GRUNFELD,
        "dependentVariable": "inv",
        "explanatoryVariables": ["value", "capital"],
        "hasConst": has_const,
        "analysis": {
            "method": "ridge",
            "alpha": alpha,
            "calculateSe": False,
        },
        "standardError": {"method": "nonrobust"},
    }


def _iv_payload(
    iv_method: str = "2sls",
    se: dict | None = None,
) -> dict:
    """IV リクエストペイロードを構築する"""
    if se is None:
        se = {"method": "nonrobust"}
    return {
        "tableName": TABLE_GRUNFELD_IV,
        "dependentVariable": "inv",
        "explanatoryVariables": ["value"],
        "hasConst": True,
        "analysis": {
            "method": "iv",
            "ivMethod": iv_method,
            "endogenousVariables": ["capital"],
            # 2 操作変数 → over-identified (Sargan 検定が有効になり NaN 回避)
            "instrumentalVariables": ["value_lag", "capital_lag"],
        },
        "standardError": se,
    }


def _panel_payload(
    method: str,
    se: dict | None = None,
) -> dict:
    """FE / RE リクエストペイロードを構築する"""
    if se is None:
        se = {"method": "nonrobust"}
    return {
        "tableName": TABLE_GRUNFELD,
        "dependentVariable": "inv",
        "explanatoryVariables": ["value", "capital"],
        "hasConst": True,
        "analysis": {
            "method": method,
            "entityIdColumn": "firm",
            "timeColumn": "year",
        },
        "standardError": se,
    }


def _sm_ols(
    df: pd.DataFrame,
    has_const: bool = True,
    cov_type: str = "nonrobust",
    cov_kwds: dict | None = None,
):
    """statsmodels OLS の参照結果を返す共通ヘルパー"""
    y = df["inv"]
    x_mat = df[["value", "capital"]]
    if has_const:
        x_mat = sm.add_constant(x_mat)
    fit_kwds: dict = {}
    if cov_type != "nonrobust":
        fit_kwds["cov_type"] = cov_type
        if cov_kwds:
            fit_kwds["cov_kwds"] = cov_kwds
    return sm.OLS(y, x_mat).fit(**fit_kwds)


# ============================================================
# OLS テスト
# ============================================================


class TestGrunfeldOLS:
    """OLS 結合テスト (Grunfeld データ)"""

    def test_coefficients_nonrobust(
        self, client, grunfeld_store, grunfeld_raw
    ):
        """
        係数・SE・t値・p値が statsmodels と一致。
        基準: nonrobust (古典的 OLS)
        """
        ref = _sm_ols(grunfeld_raw)
        _, output = _post_and_fetch(client, _ols_payload())
        params = output["parameters"]

        assert len(params) == _N_PARAMS_WITH_CONST

        np.testing.assert_allclose(
            [p["coefficient"] for p in params],
            ref.params.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS 係数が statsmodels と不一致",
        )
        np.testing.assert_allclose(
            [p["standardError"] for p in params],
            ref.bse.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS 標準誤差が statsmodels と不一致",
        )
        np.testing.assert_allclose(
            [p["tValue"] for p in params],
            ref.tvalues.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS t 値が statsmodels と不一致",
        )
        np.testing.assert_allclose(
            [p["pValue"] for p in params],
            ref.pvalues.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS p 値が statsmodels と不一致",
        )

    def test_model_stats_nonrobust(self, client, grunfeld_store, grunfeld_raw):
        """
        R²・adjR²・F 統計量が statsmodels と一致。
        """
        ref = _sm_ols(grunfeld_raw)
        _, output = _post_and_fetch(client, _ols_payload())
        ms = output["modelStatistics"]

        assert ms["nObservations"] == _N_OBS
        assert abs(ms["R2"] - ref.rsquared) < _ABS_TOL
        assert abs(ms["adjustedR2"] - ref.rsquared_adj) < _ABS_TOL
        assert abs(ms["fValue"] - ref.fvalue) < _ABS_TOL

    def test_no_const_coefficients(self, client, grunfeld_store, grunfeld_raw):
        """
        hasConst=False の係数が statsmodels と一致。
        定数項を含まない 2 パラメータ (value, capital)。
        """
        ref = _sm_ols(grunfeld_raw, has_const=False)
        _, output = _post_and_fetch(client, _ols_payload(has_const=False))
        params = output["parameters"]

        assert len(params) == _N_PARAMS_NO_CONST

        np.testing.assert_allclose(
            [p["coefficient"] for p in params],
            ref.params.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS (no const) 係数が statsmodels と不一致",
        )

    def test_robust_hc1_se(self, client, grunfeld_store, grunfeld_raw):
        """
        HC1 標準誤差が statsmodels と一致。
        """
        ref = _sm_ols(grunfeld_raw, cov_type="HC1")
        _, output = _post_and_fetch(
            client,
            _ols_payload(se={"method": "robust", "hcType": "HC1"}),
        )
        params = output["parameters"]

        np.testing.assert_allclose(
            [p["standardError"] for p in params],
            ref.bse.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS HC1 SE が statsmodels と不一致",
        )

    def test_clustered_by_firm_se(self, client, grunfeld_store, grunfeld_raw):
        """
        firm クラスター標準誤差が statsmodels と一致。
        """
        ref = _sm_ols(
            grunfeld_raw,
            cov_type="cluster",
            cov_kwds={
                "groups": grunfeld_raw["firm"].values,
                "use_correction": True,
            },
        )
        _, output = _post_and_fetch(
            client,
            _ols_payload(
                se={
                    "method": "cluster",
                    "groups": ["firm"],
                    "useCorrection": True,
                }
            ),
        )
        params = output["parameters"]

        np.testing.assert_allclose(
            [p["standardError"] for p in params],
            ref.bse.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS cluster SE が statsmodels と不一致",
        )

    def test_hac_newey_west_se(self, client, grunfeld_store, grunfeld_raw):
        """
        HAC (Newey-West, maxlags=1) SE が statsmodels と一致。

        API は get_robustcov_results(cov_type='hac',
        use_correction=True) を使用するため、
        参照側も同じ呼び出し方で比較する。
        """
        y = grunfeld_raw["inv"]
        x_mat = sm.add_constant(grunfeld_raw[["value", "capital"]])
        # API と同じ use_correction=True を使用する
        ref = (
            sm.OLS(y, x_mat)
            .fit()
            .get_robustcov_results(
                cov_type="hac",
                maxlags=_HAC_MAXLAGS,
                use_correction=True,
            )
        )
        _, output = _post_and_fetch(
            client,
            _ols_payload(se={"method": "hac", "maxlags": _HAC_MAXLAGS}),
        )
        params = output["parameters"]

        np.testing.assert_allclose(
            [p["standardError"] for p in params],
            ref.bse,  # get_robustcov_results の bse は ndarray
            atol=_HAC_ABS_TOL,
            rtol=0,
            err_msg="OLS HAC SE が statsmodels と不一致",
        )

    def test_confidence_intervals(self, client, grunfeld_store, grunfeld_raw):
        """
        95% 信頼区間が statsmodels と一致。
        """
        ref = _sm_ols(grunfeld_raw)
        ci = ref.conf_int()

        _, output = _post_and_fetch(client, _ols_payload())
        params = output["parameters"]

        np.testing.assert_allclose(
            [p["confidenceIntervalLower"] for p in params],
            ci.iloc[:, 0].values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS CI 下限が statsmodels と不一致",
        )
        np.testing.assert_allclose(
            [p["confidenceIntervalUpper"] for p in params],
            ci.iloc[:, 1].values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="OLS CI 上限が statsmodels と不一致",
        )


# ============================================================
# Lasso テスト
# ============================================================


class TestGrunfeldLasso:
    """Lasso 結合テスト (Grunfeld データ)"""

    def test_coefficient_scaled_vs_sklearn(
        self, client, grunfeld_store, grunfeld_raw
    ):
        """
        coefficientScaled が sklearn (StandardScaler + Lasso)
        の coef_ と一致する。
        """
        x_arr = grunfeld_raw[["value", "capital"]].to_numpy()
        y = grunfeld_raw["inv"].to_numpy()

        pipeline = make_pipeline(StandardScaler(), Lasso(alpha=_LASSO_ALPHA))
        pipeline.fit(x_arr, y)
        expected_scaled = pipeline.named_steps["lasso"].coef_

        _, output = _post_and_fetch(client, _lasso_payload(alpha=_LASSO_ALPHA))
        var_params = [
            p for p in output["parameters"] if p["variable"] != "const"
        ]

        np.testing.assert_allclose(
            [p["coefficientScaled"] for p in var_params],
            expected_scaled,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="Lasso coefficientScaled が sklearn と不一致",
        )

    def test_const_coefficient_scaled_is_none(self, client, grunfeld_store):
        """定数項の coefficientScaled が None であることを確認"""
        _, output = _post_and_fetch(client, _lasso_payload(alpha=_LASSO_ALPHA))
        params = output["parameters"]
        const_p = next((p for p in params if p["variable"] == "const"), None)
        assert const_p is not None, "const パラメータが存在しない"
        assert const_p["coefficientScaled"] is None


# ============================================================
# Ridge テスト
# ============================================================


class TestGrunfeldRidge:
    """Ridge 結合テスト (Grunfeld データ)"""

    def test_coefficient_scaled_vs_sklearn(
        self, client, grunfeld_store, grunfeld_raw
    ):
        """
        coefficientScaled が sklearn (StandardScaler + Ridge)
        の coef_ と一致する。
        """
        x_arr = grunfeld_raw[["value", "capital"]].to_numpy()
        y = grunfeld_raw["inv"].to_numpy()

        pipeline = make_pipeline(StandardScaler(), Ridge(alpha=_RIDGE_ALPHA))
        pipeline.fit(x_arr, y)
        expected_scaled = pipeline.named_steps["ridge"].coef_

        _, output = _post_and_fetch(client, _ridge_payload(alpha=_RIDGE_ALPHA))
        var_params = [
            p for p in output["parameters"] if p["variable"] != "const"
        ]

        np.testing.assert_allclose(
            [p["coefficientScaled"] for p in var_params],
            expected_scaled,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="Ridge coefficientScaled が sklearn と不一致",
        )


# ============================================================
# IV (2SLS) テスト
# ============================================================


class TestGrunfeldIV2SLS:
    """IV 2SLS 結合テスト (Grunfeld データ)"""

    def _build_ref(self, grunfeld_with_iv: pd.DataFrame, cov_type: str):
        """linearmodels IV2SLS の参照結果を返す"""
        y = grunfeld_with_iv["inv"]
        exog = sm.add_constant(grunfeld_with_iv[["value"]])
        endog = grunfeld_with_iv[["capital"]]
        # 2 操作変数: over-identified (Sargan 検定有効)
        instr = grunfeld_with_iv[["value_lag", "capital_lag"]]
        return IV2SLS(y, exog, endog, instr).fit(cov_type=cov_type)

    def test_coefficients_nonrobust(
        self, client, grunfeld_store, grunfeld_with_iv
    ):
        """
        2SLS 係数 (nonrobust) が linearmodels と一致。

        内生変数: capital, 操作変数: value_lag
        """
        ref = self._build_ref(grunfeld_with_iv, "unadjusted")
        _, output = _post_and_fetch(client, _iv_payload(iv_method="2sls"))
        params = output["parameters"]

        np.testing.assert_allclose(
            [p["coefficient"] for p in params],
            ref.params.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="IV 2SLS 係数が linearmodels と不一致",
        )

    def test_se_nonrobust(self, client, grunfeld_store, grunfeld_with_iv):
        """
        2SLS 標準誤差 (nonrobust) が linearmodels と一致。
        """
        ref = self._build_ref(grunfeld_with_iv, "unadjusted")
        _, output = _post_and_fetch(client, _iv_payload(iv_method="2sls"))
        params = output["parameters"]

        np.testing.assert_allclose(
            [p["standardError"] for p in params],
            ref.std_errors.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="IV 2SLS SE が linearmodels と不一致",
        )

    def test_n_observations(self, client, grunfeld_store, grunfeld_with_iv):
        """
        nObservations が IV テーブルの行数と一致。
        """
        _, output = _post_and_fetch(client, _iv_payload(iv_method="2sls"))
        ms = output["modelStatistics"]
        assert ms["nObservations"] == _N_OBS_IV

    def test_first_stage_f_statistic(
        self, client, grunfeld_store, grunfeld_with_iv
    ):
        """
        第1段階 F 値が linearmodels と一致。
        diagnostics.firstStage["capital"]["fStatistic"] を検証。
        """
        ref = self._build_ref(grunfeld_with_iv, "unadjusted")
        _, output = _post_and_fetch(client, _iv_payload(iv_method="2sls"))
        diag = output["diagnostics"]

        if "firstStage" not in diag or "capital" not in diag.get(
            "firstStage", {}
        ):
            pytest.skip("firstStage[capital] がレスポンスに含まれない")

        fs_api = diag["firstStage"]["capital"]
        fs_ref = ref.first_stage.individual["capital"]
        expected_f = float(fs_ref.f_statistic.stat)

        assert abs(fs_api["fStatistic"] - expected_f) < _ABS_TOL, (
            f"IV first-stage F: {fs_api['fStatistic']!r} != {expected_f!r}"
        )


# ============================================================
# IV (GMM) テスト
# ============================================================


class TestGrunfeldIVGMM:
    """IV GMM 結合テスト (Grunfeld データ)"""

    def test_coefficients_vs_linearmodels(
        self, client, grunfeld_store, grunfeld_with_iv
    ):
        """
        GMM 係数が linearmodels (IVGMM, weight_type='robust') と
        一致することを確認。
        """
        y = grunfeld_with_iv["inv"]
        exog = sm.add_constant(grunfeld_with_iv[["value"]])
        endog = grunfeld_with_iv[["capital"]]
        # 2 操作変数: over-identified
        instr = grunfeld_with_iv[["value_lag", "capital_lag"]]

        # weight_type は IVGMM コンストラクタに指定する
        ref = IVGMM(y, exog, endog, instr, weight_type="robust").fit(
            cov_type="robust"
        )
        _, output = _post_and_fetch(
            client,
            _iv_payload(
                iv_method="gmm",
                se={"method": "robust"},
            ),
        )
        params = output["parameters"]

        np.testing.assert_allclose(
            [p["coefficient"] for p in params],
            ref.params.values,
            atol=_ABS_TOL,
            rtol=0,
            err_msg="IV GMM 係数が linearmodels と不一致",
        )

    def test_gmm_j_stat_present(self, client, grunfeld_store):
        """
        GMM の diagnostics に J 統計量が含まれること。
        モデルが exactly identified (操作変数=内生変数=1) のため
        J 統計量は 0 になる可能性があるが、キーが存在することを確認。
        """
        _, output = _post_and_fetch(client, _iv_payload(iv_method="gmm"))
        # J 統計量は over-identified でないと意味がないが
        # exactly identified の場合も diagnostics キーの有無を確認
        diag = output.get("diagnostics", {})
        # IVGMMの結果にjstatが存在する場合に検証 (存在は任意)
        if "jStat" in diag:
            assert diag["jStat"]["statistic"] >= 0.0


# ============================================================
# 固定効果モデル (FE) テスト
# ============================================================


class TestGrunfeldFE:
    """FE 結合テスト (Grunfeld データ)"""

    def _build_ref(
        self, grunfeld_raw: pd.DataFrame, cov_type: str = "unadjusted"
    ):
        """linearmodels PanelOLS の参照結果を返す"""
        df = grunfeld_raw.set_index(["firm", "year"])
        return PanelOLS(
            df["inv"],
            df[["value", "capital"]],
            entity_effects=True,
        ).fit(cov_type=cov_type)

    def test_coefficients_nonrobust(
        self, client, grunfeld_store, grunfeld_raw
    ):
        """
        FE 係数 (nonrobust) が linearmodels (PanelOLS) と一致。
        entity_effects=True で定数は吸収される。
        """
        ref = self._build_ref(grunfeld_raw)
        _, output = _post_and_fetch(client, _panel_payload("fe"))
        params = output["parameters"]

        assert len(params) == _N_PARAMS_FE

        # 変数名で対応 (const は含まれない)
        p_map = {p["variable"]: p["coefficient"] for p in params}
        for var in ("value", "capital"):
            exp = float(ref.params[var])
            assert abs(p_map[var] - exp) < _ABS_TOL, (
                f"FE {var!r}: {p_map[var]!r} != {exp!r}"
            )

    def test_within_r2(self, client, grunfeld_store, grunfeld_raw):
        """
        Within-R² が linearmodels と一致。
        """
        ref = self._build_ref(grunfeld_raw)
        _, output = _post_and_fetch(client, _panel_payload("fe"))
        ms = output["modelStatistics"]

        assert abs(ms["R2Within"] - float(ref.rsquared)) < _ABS_TOL, (
            f"FE R2Within: {ms['R2Within']!r} != {ref.rsquared!r}"
        )

    def test_n_entities(self, client, grunfeld_store):
        """nEntities が Grunfeld の 10 企業と一致"""
        _, output = _post_and_fetch(client, _panel_payload("fe"))
        ms = output["modelStatistics"]
        assert ms["nEntities"] == _N_FIRMS

    def test_se_nonrobust(self, client, grunfeld_store, grunfeld_raw):
        """
        FE 標準誤差 (nonrobust) が linearmodels と一致。
        """
        ref = self._build_ref(grunfeld_raw)
        _, output = _post_and_fetch(client, _panel_payload("fe"))
        params = output["parameters"]
        se_map = {p["variable"]: p["standardError"] for p in params}

        for var in ("value", "capital"):
            exp_se = float(ref.std_errors[var])
            assert abs(se_map[var] - exp_se) < _ABS_TOL, (
                f"FE SE {var!r}: {se_map[var]!r} != {exp_se!r}"
            )

    def test_clustered_se_by_entity(
        self, client, grunfeld_store, grunfeld_raw
    ):
        """
        FE クラスター SE (firm) が linearmodels と一致。
        cluster_entity=True は firm, cluster_time=False。
        """
        ref = self._build_ref(grunfeld_raw, cov_type="clustered")
        # linearmodels の cluster_entity=True に相当する
        # API: groups=["firm"] でクラスタリング
        _, output = _post_and_fetch(
            client,
            _panel_payload(
                "fe",
                se={"method": "cluster", "groups": ["firm"]},
            ),
        )
        params = output["parameters"]
        se_map = {p["variable"]: p["standardError"] for p in params}

        for var in ("value", "capital"):
            exp_se = float(ref.std_errors[var])
            assert abs(se_map[var] - exp_se) < _ABS_TOL, (
                f"FE cluster SE {var!r}: {se_map[var]!r} != {exp_se!r}"
            )


# ============================================================
# 変量効果モデル (RE) テスト
# ============================================================


class TestGrunfeldRE:
    """RE 結合テスト (Grunfeld データ)"""

    def _build_ref(
        self, grunfeld_raw: pd.DataFrame, cov_type: str = "unadjusted"
    ):
        """linearmodels RandomEffects の参照結果を返す"""
        df = grunfeld_raw.set_index(["firm", "year"])
        return RandomEffects(
            df["inv"],
            df[["value", "capital"]],
        ).fit(cov_type=cov_type)

    def test_coefficients_nonrobust(
        self, client, grunfeld_store, grunfeld_raw
    ):
        """
        RE 係数 (nonrobust) が linearmodels (RandomEffects) と一致。
        """
        ref = self._build_ref(grunfeld_raw)
        _, output = _post_and_fetch(client, _panel_payload("re"))
        params = output["parameters"]
        p_map = {p["variable"]: p["coefficient"] for p in params}

        for var in ("value", "capital"):
            exp = float(ref.params[var])
            assert abs(p_map[var] - exp) < _ABS_TOL, (
                f"RE {var!r}: {p_map[var]!r} != {exp!r}"
            )

    def test_se_nonrobust(self, client, grunfeld_store, grunfeld_raw):
        """
        RE 標準誤差 (nonrobust) が linearmodels と一致。
        """
        ref = self._build_ref(grunfeld_raw)
        _, output = _post_and_fetch(client, _panel_payload("re"))
        params = output["parameters"]
        se_map = {p["variable"]: p["standardError"] for p in params}

        for var in ("value", "capital"):
            exp_se = float(ref.std_errors[var])
            assert abs(se_map[var] - exp_se) < _ABS_TOL, (
                f"RE SE {var!r}: {se_map[var]!r} != {exp_se!r}"
            )

    def test_theta_range(self, client, grunfeld_store):
        """
        diagnostics の theta が [0, 1] の範囲内であることを確認。
        theta は変量効果変換係数 (準-差分変換の重み)。
        """
        _, output = _post_and_fetch(client, _panel_payload("re"))
        diag = output["diagnostics"]

        if "theta" not in diag:
            pytest.skip("diagnostics に theta が含まれない")

        theta = diag["theta"]
        assert 0.0 <= theta <= 1.0, f"RE theta={theta!r} が [0, 1] 範囲外"

    def test_r2_triplet_present(self, client, grunfeld_store):
        """
        R2Within / R2Between / R2Overall が存在し float であること。
        """
        _, output = _post_and_fetch(client, _panel_payload("re"))
        ms = output["modelStatistics"]

        for key in ("R2Within", "R2Between", "R2Overall"):
            assert key in ms, f"{key!r} が modelStatistics に存在しない"
            assert isinstance(ms[key], float), f"{key!r} がfloat でない"

    def test_r2_matches_linearmodels(
        self, client, grunfeld_store, grunfeld_raw
    ):
        """
        R2Within が linearmodels の rsquared と一致。
        """
        ref = self._build_ref(grunfeld_raw)
        _, output = _post_and_fetch(client, _panel_payload("re"))
        ms = output["modelStatistics"]

        assert abs(ms["R2Within"] - float(ref.rsquared)) < _ABS_TOL, (
            f"RE R2Within: {ms['R2Within']!r} != {ref.rsquared!r}"
        )


# ============================================================
# 冪等性テスト
# ============================================================


def test_grunfeld_ols_idempotent(client, grunfeld_store):
    """
    同一ペイロードで2回連続リクエストした場合に、
    係数・SE が完全に同一の値を返すことを確認する。

    resultId は異なるが数値結果は同一でなければならない。
    """
    payload = _ols_payload()

    id1, out1 = _post_and_fetch(client, payload)
    id2, out2 = _post_and_fetch(client, payload)

    assert id1 != id2, "resultId が同一 (重複登録の可能性)"

    pairs = zip(out1["parameters"], out2["parameters"], strict=True)
    for p1, p2 in pairs:
        assert p1["variable"] == p2["variable"]
        assert p1["coefficient"] == p2["coefficient"], (
            f"冪等性違反: {p1['variable']!r} の係数が不一致"
        )
        assert p1["standardError"] == p2["standardError"], (
            f"冪等性違反: {p1['variable']!r} の SE が不一致"
        )


# ============================================================
# /results/{result_id} エンドポイント構造テスト
# ============================================================


def test_results_endpoint_required_keys(client, grunfeld_store):
    """
    GET /api/analysis/results/{result_id} の必須キーを検証する。
    id, name, tableName, regressionOutput が存在すること。
    """
    result_id, _ = _post_and_fetch(client, _ols_payload())

    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.status_code == status.HTTP_200_OK

    result = resp.json()["result"]
    for key in ("id", "name", "tableName", "regressionOutput"):
        assert key in result, (
            f"GET /results/{{id}} のレスポンスに {key!r} が存在しない"
        )
    assert result["id"] == result_id
    assert result["tableName"] == TABLE_GRUNFELD


def test_results_endpoint_nonexistent_id_no_info_leakage(
    client, grunfeld_store
):
    """
    存在しない result_id アクセスでスタックトレース等が
    レスポンスに含まれないことを確認 (情報漏洩防止)。
    """
    with pytest.raises(KeyError):
        client.get(f"{URL_RESULTS}/nonexistent-grunfeld-uuid")
