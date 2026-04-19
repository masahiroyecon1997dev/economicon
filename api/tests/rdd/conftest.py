"""RDD 分析テスト共通フィクスチャ"""

from dataclasses import dataclass

import numpy as np
import polars as pl
import pytest
from fastapi.testclient import TestClient

from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# データ生成定数
# -----------------------------------------------------------

_SEED = 42
_N = 500

TABLE_RDD = "RDDData"
TABLE_NO_LEFT = "RDDNoLeft"
TABLE_STRING = "RDDStringData"

URL_RDD = "/api/analysis/rdd"
URL_RESULT_DETAIL = "/api/analysis/results/{result_id}"


# -----------------------------------------------------------
# データ生成
# -----------------------------------------------------------


def generate_rdd_data(
    n: int = _N,
    seed: int = _SEED,
    true_effect: float = 1.5,
    cutoff: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    シャープ RDD の DGP（データ生成過程）。

    y = 1 + 2*x + true_effect * 1[x >= cutoff] + ε
    x ~ Uniform(-1, 1), ε ~ N(0, 0.5²)
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1.0, 1.0, n)
    treatment = (x >= cutoff).astype(float)
    y = 1.0 + 2.0 * x + true_effect * treatment + rng.normal(0, 0.5, n)
    return y, x


def _build_tables(tables_store: TablesStore) -> None:
    """テスト用テーブルを TablesStore に登録する。"""
    y, x = generate_rdd_data()
    df = pl.DataFrame({"y": y, "x": x})
    tables_store.store_table(TABLE_RDD, df)

    # 左側サンプルなし（全観測が cutoff=0 以上）
    tables_store.store_table(
        TABLE_NO_LEFT,
        pl.DataFrame({"y": y[x >= 0.0], "x": x[x >= 0.0]}),
    )

    # 文字列列のみのテーブル
    tables_store.store_table(
        TABLE_STRING,
        pl.DataFrame({"y": ["a"] * 20, "x": ["b"] * 20}),
    )


# -----------------------------------------------------------
# pytest フィクスチャ
# -----------------------------------------------------------


@pytest.fixture(scope="module")
def tables_store():
    ts = TablesStore()
    _build_tables(ts)
    return ts


@pytest.fixture(scope="module")
def client(tables_store):  # noqa: ARG001
    with TestClient(app) as c:
        yield c


# -----------------------------------------------------------
# ペイロードビルダー
# -----------------------------------------------------------


@dataclass
class RDDPayload:
    """RDDリクエストペイロード"""

    table: str = TABLE_RDD
    outcome: str = "y"
    running: str = "x"
    cutoff: float = 0.0
    kernel: str = "triangular"
    bw_select: str = "mserd"
    h: float | None = None
    p: int = 1
    vce: str = "hc1"
    confidence_level: float = 0.95
    n_bins: int = 30
    placebo_cutoffs: list[float] | None = None
    result_name: str = ""
    description: str = ""

    def build(self) -> dict:
        payload: dict = {
            "tableName": self.table,
            "resultName": self.result_name,
            "description": self.description,
            "outcomeVariable": self.outcome,
            "runningVariable": self.running,
            "cutoff": self.cutoff,
            "kernel": self.kernel,
            "bwSelect": self.bw_select,
            "p": self.p,
            "vce": self.vce,
            "confidenceLevel": self.confidence_level,
            "nBins": self.n_bins,
        }
        if self.h is not None:
            payload["h"] = self.h
        if self.placebo_cutoffs is not None:
            payload["placeboCutoffs"] = self.placebo_cutoffs
        return payload
