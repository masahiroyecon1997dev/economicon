from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from benchmarks.grunfeld_real import bench_grunfeld_real
from benchmarks.helpers import NumpyEncoder

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPO_ROOT / "test" / "data" / "parquet" / "plm_grunfeld.parquet"
OUTPUT_PATH = (
    REPO_ROOT
    / "test"
    / "benchmarks"
    / "python"
    / "real"
    / "plm_grunfeld_gold.json"
)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(DATA_PATH)
    result = bench_grunfeld_real(df)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()