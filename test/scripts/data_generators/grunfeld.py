from __future__ import annotations

import pandas as pd
from statsmodels.datasets import get_rdataset

GRUNFELD_COLUMNS = ["firm", "year", "inv", "value", "capital"]


def load_grunfeld_panel() -> pd.DataFrame:
    """Return the Grunfeld panel in a stable column order.

    The source is fetched once here and persisted to parquet so pytest no longer
    depends on runtime network access.
    """
    dataset = get_rdataset("Grunfeld", "plm")
    if dataset is None or dataset.data is None:
        raise RuntimeError("statsmodels Grunfeld dataset not found")

    df = dataset.data[GRUNFELD_COLUMNS].copy()
    return df.astype(float).reset_index(drop=True)