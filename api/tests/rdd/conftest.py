"""RDD 分析テスト共通フィクスチャ"""

from dataclasses import dataclass
from pathlib import Path

import polars as pl
import pytest
from fastapi.testclient import TestClient

from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# データパス
# -----------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parents[3] / "test" / "data" / "parquet"

TABLE_RDD = "RDDData"
TABLE_NO_LEFT = "RDDNoLeft"
TABLE_STRING = "RDDStringData"

URL_RDD = "/api/analysis/rdd"
URL_RESULT_DETAIL = "/api/analysis/results/{result_id}"


# -----------------------------------------------------------
# データ登録
# -----------------------------------------------------------


def _build_tables(tables_store: TablesStore) -> None:
    """Parquet から読み込んだテーブルを TablesStore に登録する。

    CSV では浮動小数点精度が欠落するため、rdrobust の数値答との比較には
    Parquet を使用する。
    """
    df = pl.read_parquet(_DATA_DIR / "synthetic_rdd.parquet")
    tables_store.store_table(TABLE_RDD, df)

    # 左側サンプルなし（running_var >= 0 のみ）
    tables_store.store_table(
        TABLE_NO_LEFT,
        df.filter(pl.col("running_var") >= 0.0),
    )

    # 文字列列のみのテーブル
    tables_store.store_table(
        TABLE_STRING,
        pl.DataFrame({"y": ["a"] * 20, "running_var": ["b"] * 20}),
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
    running: str = "running_var"
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
