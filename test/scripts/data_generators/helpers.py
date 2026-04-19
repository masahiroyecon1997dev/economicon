from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "test" / "data"
CSV_DIR = DATA_DIR / "csv"
PARQUET_DIR = DATA_DIR / "parquet"

SEED = 2024

N_OLS = 300
N_ENTITIES = 10
N_PERIODS = 10
N_PANEL = N_ENTITIES * N_PERIODS
N_IV = 400
N_WLS = 320
N_GLS = 48
N_FGLS_HETERO = 320
N_FGLS_AR1 = 240
N_TOBIT = 300
N_HECKMAN = 600
N_RDD = 1000
N_DESC = 500
N_STAT_CI = 100
N_STAT_TEST = 50
N_STAT_TEST_SMALL = 30


def ensure_dirs() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)


def save_dataset(df: pd.DataFrame, name: str) -> None:
    csv_path = CSV_DIR / f"{name}.csv"
    parquet_path = PARQUET_DIR / f"{name}.parquet"

    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    print(f"  saved: {name}  (n={len(df)}, cols={list(df.columns)})")
