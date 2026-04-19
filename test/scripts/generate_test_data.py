import os

import statsmodels.api as sm
import wooldridge as woo
from palmerpenguins import load_penguins

# 出力先ディレクトリの作成
OUTPUT_DIR = "../data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_DIR_CSV = os.path.join(OUTPUT_DIR, "csv")
os.makedirs(OUTPUT_DIR_CSV, exist_ok=True)
OUTPUT_DIR_PARQUET = os.path.join(OUTPUT_DIR, "parquet")
os.makedirs(OUTPUT_DIR_PARQUET, exist_ok=True)


def save_dataset(df, package_name, dataset_name):
    """CSVとParquetの両方で保存するヘルパー関数"""
    base_name = f"{package_name}_{dataset_name}"

    # CSV保存 (Excel等での閲覧を考慮し、encodingを指定)
    csv_path = os.path.join(OUTPUT_DIR_CSV, f"{base_name}.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")

    # Parquet保存 (型を厳密に保持)
    parquet_path = os.path.join(OUTPUT_DIR_PARQUET, f"{base_name}.parquet")
    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    print(f"Saved: {base_name}")


# --- 1. Wooldridge datasets ---
woo_list = ["wage1", "hprice1", "vote1"]
for name in woo_list:
    df = woo.data(name)
    save_dataset(df, "wooldridge", name)

# --- 2. AER / R datasets (via statsmodels) ---
# (データ名, パッケージ名) のタプル
r_datasets = [("Journals", "AER"), ("Fatalities", "AER"), ("mtcars", "datasets")]
for d_name, p_name in r_datasets:
    # get_rdataset は .data 属性に DataFrame を保持している
    df = sm.datasets.get_rdataset(d_name, p_name).data
    # パッケージ名は小文字で統一
    save_dataset(df, p_name.lower(), d_name.lower())

# --- 3. Palmer Penguins ---
penguins = load_penguins()
save_dataset(penguins, "palmerpenguins", "penguins")

print("\nAll test data generated successfully!")
