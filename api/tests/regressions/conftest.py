"""回帰分析テスト共通フィクスチャ"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl
import pytest
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# パス定数
# -----------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parents[3] / "test" / "data" / "csv"
_BENCH_PY_DIR = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "benchmarks"
    / "python"
    / "synthetic"
)

# -----------------------------------------------------------
# テーブル名
# -----------------------------------------------------------

TABLE_BASIC = "BasicData"
TABLE_PANEL = "PanelData"
TABLE_IV = "IVData"
TABLE_TOBIT = "TobitData"
TABLE_WLS = "WLSData"
TABLE_GLS_DATA = "GLSData"
TABLE_GLS_SIGMA = "SigmaMatrix"
TABLE_FGLS_HETERO = "FGLSHeteroskedasticData"
TABLE_FGLS_AR1 = "FGLSAR1Data"
TABLE_PANEL_IV = "PanelIVData"
TABLE_STRING = "StringData"
TABLE_NAN = "NaNData"

# GLS 合成データの行数
_N_GLS = 48

# エンドポイント
URL_REGRESSION = "/api/analysis/regression"
URL_RESULTS = "/api/analysis/results"
URL_RESULT_DETAIL = "/api/analysis/results/{result_id}"


# -----------------------------------------------------------
# Gold JSON ローダー
# -----------------------------------------------------------


def load_py_gold(model: str) -> dict:
    """ベンチマーク gold JSON を読み込んで返す。

    Parameters
    ----------
    model:
        ファイル名の ``synthetic_{model}_gold.json`` の ``model`` 部分。
    """
    path = _BENCH_PY_DIR / f"synthetic_{model}_gold.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# -----------------------------------------------------------
# 標準ペイロードビルダー（dataclass）
# -----------------------------------------------------------


@dataclass
class OlsPayload:
    """OLSリクエストペイロード"""

    table: str = TABLE_BASIC
    dep: str = "y_cont"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2", "x3"])
    has_const: bool = True
    se_method: str = "nonrobust"
    se_extra: dict = field(default_factory=dict)

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        se = {"method": self.se_method, **self.se_extra}
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "hasConst": self.has_const,
            "analysis": {"method": "ols"},
            "standardError": se,
        }


@dataclass
class LogitPayload:
    """Logitリクエストペイロード"""

    table: str = TABLE_BASIC
    dep: str = "y_binary"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2", "x3"])
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "analysis": {"method": "logit"},
            "standardError": {"method": self.se_method},
        }


@dataclass
class ProbitPayload:
    """Probitリクエストペイロード"""

    table: str = TABLE_BASIC
    dep: str = "y_binary"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2", "x3"])
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "analysis": {"method": "probit"},
            "standardError": {"method": self.se_method},
        }


@dataclass
class TobitPayload:
    """Tobitリクエストペイロード"""

    table: str = TABLE_TOBIT
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2"])
    left: float = 0.0
    right: float | None = None

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "analysis": {
                "method": "tobit",
                "leftCensoringLimit": self.left,
                "rightCensoringLimit": self.right,
            },
            "standardError": {"method": "nonrobust"},
        }


@dataclass
class FePayload:
    """固定効果モデルリクエストペイロード"""

    table: str = TABLE_PANEL
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2"])
    entity_col: str = "entity_id"
    time_col: str | None = None
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        analysis: dict = {
            "method": "fe",
            "entityIdColumn": self.entity_col,
        }
        if self.time_col:
            analysis["timeColumn"] = self.time_col
        se: dict[str, str | list[str]] = {"method": self.se_method}
        if self.se_method == "cluster":
            se["groups"] = [self.entity_col]
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "analysis": analysis,
            "standardError": se,
        }


@dataclass
class RePayload:
    """変量効果モデルリクエストペイロード"""

    table: str = TABLE_PANEL
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2"])
    entity_col: str = "entity_id"
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "analysis": {
                "method": "re",
                "entityIdColumn": self.entity_col,
            },
            "standardError": {"method": self.se_method},
        }


@dataclass
class IvPayload:
    """操作変数法リクエストペイロード"""

    table: str = TABLE_IV
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x_exog"])
    endog: list[str] = field(default_factory=lambda: ["x_endog"])
    instruments: list[str] = field(default_factory=lambda: ["z1", "z2"])
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "analysis": {
                "method": "iv",
                "endogenousVariables": self.endog,
                "instrumentalVariables": self.instruments,
            },
            "standardError": {"method": self.se_method},
        }


@dataclass
class WlsPayload:
    """WLSリクエストペイロード"""

    table: str = TABLE_WLS
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2", "x3"])
    weights_col: str = "weights"
    has_const: bool = True
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "hasConst": self.has_const,
            "analysis": {
                "method": "wls",
                "weightsColumn": self.weights_col,
            },
            "standardError": {"method": self.se_method},
        }


@dataclass
class GlsPayload:
    """GLSリクエストペイロード"""

    table: str = TABLE_GLS_DATA
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2"])
    sigma_table: str = TABLE_GLS_SIGMA
    has_const: bool = True
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "hasConst": self.has_const,
            "analysis": {
                "method": "gls",
                "sigmaTableName": self.sigma_table,
            },
            "standardError": {"method": self.se_method},
        }


@dataclass
class FglsPayload:
    """FGLSリクエストペイロード"""

    table: str = TABLE_FGLS_HETERO
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2", "x3"])
    fgls_method: str = "heteroskedastic"
    max_iter: int = 10
    has_const: bool = True
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "hasConst": self.has_const,
            "analysis": {
                "method": "fgls",
                "fglsMethod": self.fgls_method,
                "maxIter": self.max_iter,
            },
            "standardError": {"method": self.se_method},
        }


@dataclass
class PanelIvPayload:
    """PanelIV (feiv) リクエストペイロード"""

    table: str = TABLE_PANEL_IV
    dep: str = "y"
    expl: list[str] = field(default_factory=lambda: ["x1"])
    endog: list[str] = field(default_factory=lambda: ["x2"])
    instruments: list[str] = field(default_factory=lambda: ["z1", "z2"])
    entity_col: str = "entity_id"
    time_col: str | None = "time_id"
    se_method: str = "nonrobust"

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        analysis: dict = {
            "method": "feiv",
            "entityIdColumn": self.entity_col,
            "endogenousVariables": self.endog,
            "instrumentalVariables": self.instruments,
        }
        if self.time_col:
            analysis["timeColumn"] = self.time_col
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "analysis": analysis,
            "standardError": {"method": self.se_method},
        }


@dataclass
class LassoPayload:
    """Lassoリクエストペイロード"""

    table: str = TABLE_BASIC
    dep: str = "y_cont"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2", "x3"])
    alpha: float = 0.1
    has_const: bool = True
    calculate_se: bool = False

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "hasConst": self.has_const,
            "analysis": {
                "method": "lasso",
                "alpha": self.alpha,
                "calculateSe": self.calculate_se,
            },
            "standardError": {"method": "nonrobust"},
        }


@dataclass
class RidgePayload:
    """Ridgeリクエストペイロード"""

    table: str = TABLE_BASIC
    dep: str = "y_cont"
    expl: list[str] = field(default_factory=lambda: ["x1", "x2", "x3"])
    alpha: float = 0.5
    has_const: bool = True
    calculate_se: bool = False

    def build(self) -> dict:
        """リクエストペイロード辞書を構築する"""
        return {
            "tableName": self.table,
            "dependentVariable": self.dep,
            "explanatoryVariables": self.expl,
            "hasConst": self.has_const,
            "analysis": {
                "method": "ridge",
                "alpha": self.alpha,
                "calculateSe": self.calculate_se,
            },
            "standardError": {"method": "nonrobust"},
        }


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

    # --- BasicData (synthetic_ols.csv: y_cont, y_binary, x1, x2, x3) ---
    df_basic = pl.read_csv(_DATA_DIR / "synthetic_ols.csv")
    manager.store_table(TABLE_BASIC, df_basic)

    # --- WLSData (synthetic_wls.csv: y, x1, x2, x3, sigma2, weights) ---
    df_wls = pl.read_csv(_DATA_DIR / "synthetic_wls.csv")
    manager.store_table(TABLE_WLS, df_wls)

    # --- PanelData
    # (synthetic_panel.csv: entity_id, time_id, y, x1, x2 / 100行) ---
    df_panel = pl.read_csv(_DATA_DIR / "synthetic_panel.csv")
    manager.store_table(TABLE_PANEL, df_panel)

    # --- PanelIVData (PanelData + full-rank instrument columns) ---
    df_panel_iv = df_panel.with_columns(
        [
            (
                pl.col("x2") * 0.8
                + pl.col("time_id") * 0.2
            ).alias("z1"),
            (
                pl.col("x2") * pl.col("x2")
                + pl.col("x1") * 0.3
                + pl.col("time_id") * 0.1
            ).alias("z2"),
        ]
    )
    manager.store_table(TABLE_PANEL_IV, df_panel_iv)

    # --- IVData
    # (synthetic_iv.csv: y, x_exog, x_endog, z1, z2 / 400行) ---
    df_iv = pl.read_csv(_DATA_DIR / "synthetic_iv.csv")
    manager.store_table(TABLE_IV, df_iv)

    # --- TobitData
    # (synthetic_tobit.csv: y, x1, x2) ---
    df_tobit = pl.read_csv(_DATA_DIR / "synthetic_tobit.csv")
    manager.store_table(TABLE_TOBIT, df_tobit)

    # --- GLSData / SigmaMatrix ---
    df_gls = pl.read_csv(_DATA_DIR / "synthetic_gls_data.csv")
    manager.store_table(TABLE_GLS_DATA, df_gls)

    df_sigma = pl.read_csv(_DATA_DIR / "synthetic_gls_sigma.csv")
    manager.store_table(TABLE_GLS_SIGMA, df_sigma)

    # --- FGLS datasets ---
    df_fgls_hetero = pl.read_csv(_DATA_DIR / "synthetic_fgls_hetero.csv")
    manager.store_table(TABLE_FGLS_HETERO, df_fgls_hetero)

    df_fgls_ar1 = pl.read_csv(_DATA_DIR / "synthetic_fgls_ar1.csv")
    manager.store_table(TABLE_FGLS_AR1, df_fgls_ar1)

    # --- StringData (dtype検証用) ---
    df_string = pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Dave", "Eve"],
            "score": [80.0, 90.0, 70.0, 85.0, 95.0],
        }
    )
    manager.store_table(TABLE_STRING, df_string)

    # --- NaNData (欠損値処理検証用) ---
    x_nan: list[float | None] = [
        1.0,
        2.0,
        None,
        4.0,
        5.0,
        6.0,
        7.0,
        8.0,
        9.0,
        10.0,
    ]
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
