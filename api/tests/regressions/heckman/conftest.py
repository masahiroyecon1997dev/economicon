"""ヘックマン推定テスト専用フィクスチャ"""

import numpy as np
import polars as pl
import pytest

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore

TABLE_HECKMAN = "HeckmanData"
URL_HECKMAN = "/api/analysis/heckman-regression"

_N_HK = 500
_SEED_HK = 2024


@pytest.fixture(autouse=True)
def _heckman_data(tables_store: TablesStore) -> None:
    """HeckmanData を TablesStore に注入する（autouse）。

    親の tables_store フィクスチャが提供するストアに対して
    HeckmanData テーブルのみを追加する。グローバル RNG 状態に
    影響しない独立 Generator を使用する。
    """
    rng = np.random.default_rng(seed=_SEED_HK)
    education = rng.normal(12.0, 2.0, _N_HK)
    experience = rng.normal(5.0, 3.0, _N_HK)
    n_children = rng.poisson(1.5, _N_HK).astype(float)
    xb_sel = -0.5 + 0.3 * education + 0.2 * experience - 0.4 * n_children
    prob_sel = 1.0 / (1.0 + np.exp(-xb_sel))
    employed = (prob_sel > rng.uniform(size=_N_HK)).astype(float)
    wage = (
        2.0 + 0.5 * education + 0.3 * experience + rng.normal(0.0, 1.0, _N_HK)
    )
    df = pl.DataFrame(
        {
            "wage": wage,
            "employed": employed,
            "education": education,
            "experience": experience,
            "n_children": n_children,
        }
    )
    tables_store.store_table(TABLE_HECKMAN, df)


@pytest.fixture(autouse=True)
def _clear_results() -> None:  # type: ignore[return]
    """各テスト前後に AnalysisResultStore をクリアする。"""
    store = AnalysisResultStore()
    store.clear_all()
