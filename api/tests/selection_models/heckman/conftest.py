"""ヘックマン推定テスト専用フィクスチャ"""

from pathlib import Path

import polars as pl
import pytest

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore

TABLE_HECKMAN = "HeckmanData"
URL_HECKMAN = "/api/analysis/heckman-regression"

_DATA_DIR = Path(__file__).resolve().parents[4] / "test" / "data" / "csv"


@pytest.fixture(autouse=True)
def _heckman_data(tables_store: TablesStore) -> None:
    """HeckmanData を TablesStore に注入する（autouse）。

    synthetic_heckman.csv（wage, employed, educ, exp, kids）を読み込む。
    """
    df = pl.read_csv(_DATA_DIR / "synthetic_heckman.csv")
    tables_store.store_table(TABLE_HECKMAN, df)


@pytest.fixture(autouse=True)
def _clear_results() -> None:  # type: ignore[return]
    """各テスト前後に AnalysisResultStore をクリアする。"""
    store = AnalysisResultStore()
    store.clear_all()
