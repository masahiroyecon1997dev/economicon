from __future__ import annotations

from pathlib import Path

from data_generators.grunfeld import load_grunfeld_panel

REPO_ROOT = Path(__file__).resolve().parents[2]
PARQUET_DIR = REPO_ROOT / "test" / "data" / "parquet"
CSV_DIR = REPO_ROOT / "test" / "data" / "csv"


def main() -> None:
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PARQUET_DIR / "plm_grunfeld.parquet"
    csv_path = CSV_DIR / "plm_grunfeld.csv"
    df = load_grunfeld_panel()
    df.to_parquet(output_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"Wrote {output_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()