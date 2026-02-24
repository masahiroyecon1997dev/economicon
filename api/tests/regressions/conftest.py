"""回帰分析テスト共通フィクスチャ"""

import numpy as np
import polars as pl
import pytest
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# データ生成定数
# -----------------------------------------------------------

_SEED = 42
_N_BASIC = 100
_N_ENTITIES = 10
_N_PERIODS = 5
_N_PANEL = _N_ENTITIES * _N_PERIODS  # 50
_N_IV = 200
_N_TOBIT = 150

# テーブル名
TABLE_BASIC = "BasicData"
TABLE_PANEL = "PanelData"
TABLE_IV = "IVData"
TABLE_TOBIT = "TobitData"
TABLE_STRING = "StringData"
TABLE_NAN = "NaNData"

# エンドポイント
URL_REGRESSION = "/api/analysis/regression"
URL_RESULTS = "/api/analysis/results"


# -----------------------------------------------------------
# 標準ペイロードビルダー
# -----------------------------------------------------------


def ols_payload(
    table=TABLE_BASIC,
    dep="y_linear",
    expl=None,
    *,
    has_const=True,
    se_method="nonrobust",
    **se_kwargs,
):
    """OLSリクエストペイロードを生成"""
    if expl is None:
        expl = ["x1", "x2"]
    se = {"method": se_method, **se_kwargs}
    payload = {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "hasConst": has_const,
        "analysis": {"method": "ols"},
        "standardError": se,
    }
    return payload


def logit_payload(
    table=TABLE_BASIC,
    dep="y_binary",
    expl=None,
    se_method="nonrobust",
):
    """Logitリクエストペイロードを生成"""
    if expl is None:
        expl = ["x1", "x2"]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "analysis": {"method": "logit"},
        "standardError": {"method": se_method},
    }


def probit_payload(
    table=TABLE_BASIC,
    dep="y_binary",
    expl=None,
    se_method="nonrobust",
):
    """Probitリクエストペイロードを生成"""
    if expl is None:
        expl = ["x1", "x2"]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "analysis": {"method": "probit"},
        "standardError": {"method": se_method},
    }


def tobit_payload(
    table=TABLE_TOBIT,
    dep="y",
    expl=None,
    left=0.0,
    right=None,
):
    """Tobitリクエストペイロードを生成"""
    if expl is None:
        expl = ["x"]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "analysis": {
            "method": "tobit",
            "leftCensoringLimit": left,
            "rightCensoringLimit": right,
        },
        "standardError": {"method": "nonrobust"},
    }


def fe_payload(  # noqa: PLR0913
    table=TABLE_PANEL,
    dep="y",
    expl=None,
    entity_col="entity_id",
    time_col=None,
    se_method="nonrobust",
):
    """固定効果モデルリクエストペイロードを生成"""
    if expl is None:
        expl = ["x1", "x2"]
    analysis = {
        "method": "fe",
        "entityIdColumn": entity_col,
    }
    if time_col:
        analysis["timeColumn"] = time_col
    se = {"method": se_method}
    if se_method == "cluster":
        se["groups"] = [entity_col]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "analysis": analysis,
        "standardError": se,
    }


def re_payload(
    table=TABLE_PANEL,
    dep="y",
    expl=None,
    entity_col="entity_id",
    se_method="nonrobust",
):
    """変量効果モデルリクエストペイロードを生成"""
    if expl is None:
        expl = ["x1", "x2"]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "analysis": {
            "method": "re",
            "entityIdColumn": entity_col,
        },
        "standardError": {"method": se_method},
    }


def iv_payload(  # noqa: PLR0913
    table=TABLE_IV,
    dep="y",
    expl=None,
    endog=None,
    instruments=None,
    se_method="nonrobust",
):
    """操作変数法リクエストペイロードを生成"""
    if expl is None:
        expl = ["x1"]
    if endog is None:
        endog = ["x2_endog"]
    if instruments is None:
        instruments = ["z1", "z2"]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "analysis": {
            "method": "iv",
            "endogenousVariables": endog,
            "instrumentalVariables": instruments,
        },
        "standardError": {"method": se_method},
    }


def lasso_payload(  # noqa: PLR0913
    table=TABLE_BASIC,
    dep="y_linear",
    expl=None,
    alpha=0.1,
    has_const=True,
    calculate_se=False,
):
    """Lassoリクエストペイロードを生成"""
    if expl is None:
        expl = ["x1", "x2"]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "hasConst": has_const,
        "analysis": {
            "method": "lasso",
            "alpha": alpha,
            "calculateSe": calculate_se,
        },
        "standardError": {"method": "nonrobust"},
    }


def ridge_payload(  # noqa: PLR0913
    table=TABLE_BASIC,
    dep="y_linear",
    expl=None,
    alpha=0.5,
    has_const=True,
    calculate_se=False,
):
    """Ridgeリクエストペイロードを生成"""
    if expl is None:
        expl = ["x1", "x2"]
    return {
        "tableName": table,
        "dependentVariable": dep,
        "explanatoryVariables": expl,
        "hasConst": has_const,
        "analysis": {
            "method": "ridge",
            "alpha": alpha,
            "calculateSe": calculate_se,
        },
        "standardError": {"method": "nonrobust"},
    }


# -----------------------------------------------------------
# 生データ生成（数値検証に使う）
# -----------------------------------------------------------


def generate_basic_data():
    """
    fixtureと完全に同じシード・順序で BasicData の生データを返す
    """
    np.random.seed(_SEED)
    x1 = np.random.normal(0, 1, _N_BASIC)
    x2 = np.random.normal(0, 1, _N_BASIC)
    y_linear = 2.0 + 1.5 * x1 + 0.8 * x2 + np.random.normal(0, 0.5, _N_BASIC)
    # y_binary の生成（RNGを消費するため必須）
    lc = -1 + 0.5 * x1 + 1.2 * x2
    prob = 1 / (1 + np.exp(-lc))
    y_binary = np.random.binomial(1, prob, _N_BASIC)
    return x1, x2, y_linear, y_binary


def generate_panel_data():
    """
    fixtureと完全に同じシード・順序で PanelData の生データを返す

    generate_basic_data()の後続のRNGを想定して呼ぶこと
    （独立した seed では呼ばないこと）
    """
    n_total = _N_PANEL
    entity_ids = np.repeat(range(1, _N_ENTITIES + 1), _N_PERIODS)
    time_ids = np.tile(range(1, _N_PERIODS + 1), _N_ENTITIES)
    entity_effects = np.random.normal(0, 2, _N_ENTITIES)
    entity_effects_exp = np.repeat(entity_effects, _N_PERIODS)
    x1_panel = np.random.normal(0, 1, n_total)
    x2_panel = np.random.normal(0, 1, n_total)
    error = np.random.normal(0, 1, n_total)
    y_panel = (
        2.0 + 1.5 * x1_panel + (-0.8) * x2_panel + entity_effects_exp + error
    )
    return entity_ids, time_ids, x1_panel, x2_panel, y_panel


def generate_iv_data():
    """
    fixtureと完全に同じシード・順序で IVData の生データを返す

    generate_basic_data(), generate_panel_data()の後続RNGを想定
    """
    z1 = np.random.normal(0, 1, _N_IV)
    z2 = np.random.normal(0, 1, _N_IV)
    x1_iv = np.random.normal(0, 1, _N_IV)
    x2_endog = 0.5 * z1 + 0.3 * z2 + np.random.normal(0, 0.5, _N_IV)
    y_iv = 1.0 + 0.5 * x1_iv + 1.0 * x2_endog + np.random.normal(0, 1, _N_IV)
    return x1_iv, x2_endog, z1, z2, y_iv


def generate_all_data():
    """全テーブルの生データを一括生成（seed=42 で固定）"""
    np.random.seed(_SEED)
    basic = generate_basic_data()
    panel = generate_panel_data()
    iv = generate_iv_data()
    return basic, panel, iv


# -----------------------------------------------------------
# フィクスチャ
# -----------------------------------------------------------


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ（全テーブルを事前ロード）"""
    manager = TablesStore()
    manager.clear_tables()

    result_store = AnalysisResultStore()
    result_store.clear_all()

    np.random.seed(_SEED)

    # --- BasicData ---
    x1 = np.random.normal(0, 1, _N_BASIC)
    x2 = np.random.normal(0, 1, _N_BASIC)
    y_linear = 2.0 + 1.5 * x1 + 0.8 * x2 + np.random.normal(0, 0.5, _N_BASIC)
    lc = -1 + 0.5 * x1 + 1.2 * x2
    prob = 1 / (1 + np.exp(-lc))
    y_binary = np.random.binomial(1, prob, _N_BASIC)
    df_basic = pl.DataFrame(
        {
            "y_linear": y_linear,
            "y_binary": y_binary.astype(float),
            "x1": x1,
            "x2": x2,
        }
    )
    manager.store_table(TABLE_BASIC, df_basic)

    # --- PanelData ---
    entity_ids = np.repeat(range(1, _N_ENTITIES + 1), _N_PERIODS)
    time_ids = np.tile(range(1, _N_PERIODS + 1), _N_ENTITIES)
    entity_effects = np.random.normal(0, 2, _N_ENTITIES)
    entity_exp = np.repeat(entity_effects, _N_PERIODS)
    x1_panel = np.random.normal(0, 1, _N_PANEL)
    x2_panel = np.random.normal(0, 1, _N_PANEL)
    error = np.random.normal(0, 1, _N_PANEL)
    y_panel = 2.0 + 1.5 * x1_panel + (-0.8) * x2_panel + entity_exp + error
    df_panel = pl.DataFrame(
        {
            "entity_id": entity_ids.astype(float),
            "time_id": time_ids.astype(float),
            "y": y_panel,
            "x1": x1_panel,
            "x2": x2_panel,
        }
    )
    manager.store_table(TABLE_PANEL, df_panel)

    # --- IVData ---
    z1 = np.random.normal(0, 1, _N_IV)
    z2 = np.random.normal(0, 1, _N_IV)
    x1_iv = np.random.normal(0, 1, _N_IV)
    x2_endog = 0.5 * z1 + 0.3 * z2 + np.random.normal(0, 0.5, _N_IV)
    y_iv = 1.0 + 0.5 * x1_iv + 1.0 * x2_endog + np.random.normal(0, 1, _N_IV)
    df_iv = pl.DataFrame(
        {
            "y": y_iv,
            "x1": x1_iv,
            "x2_endog": x2_endog,
            "z1": z1,
            "z2": z2,
        }
    )
    manager.store_table(TABLE_IV, df_iv)

    # --- TobitData ---
    x_tobit = np.random.normal(0, 1, _N_TOBIT)
    latent_y = 1.0 + 2.0 * x_tobit + np.random.normal(0, 1, _N_TOBIT)
    y_tobit = np.maximum(0, latent_y)
    df_tobit = pl.DataFrame({"y": y_tobit, "x": x_tobit})
    manager.store_table(TABLE_TOBIT, df_tobit)

    # --- StringData (dtype検証用) ---
    df_string = pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Dave", "Eve"],
            "score": [80.0, 90.0, 70.0, 85.0, 95.0],
        }
    )
    manager.store_table(TABLE_STRING, df_string)

    # --- NaNData (欠損値処理検証用) ---
    x_nan = [1.0, 2.0, None, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    df_nan = pl.DataFrame(
        {
            "y": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            "x1": x_nan,
            "x2": [0.5, 1.0, 1.5, 2.0, None, 3.0, 3.5, 4.0, 4.5, 5.0],
        }
    )
    manager.store_table(TABLE_NAN, df_nan)

    yield manager
    manager.clear_tables()
    result_store.clear_all()


@pytest.fixture
def result_store():
    """AnalysisResultStoreのフィクスチャ"""
    store = AnalysisResultStore()
    store.clear_all()
    yield store
    store.clear_all()
