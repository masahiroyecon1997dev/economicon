"""エンコーディングマッピング定数"""

# Polars コーデック名（pl.read_csv 等で使用）
POLARS_ENCODING_MAP: dict[str, str] = {
    "utf8": "utf8",
    "latin1": "latin1",
    "ascii": "ascii",
    "gbk": "gbk",
    "windows-1252": "windows-1252",
    "shift_jis": "cp932",
}

# Python 標準コーデック名（ファイル書き込み等で使用）
PYTHON_ENCODING_MAP: dict[str, str] = {
    "utf8": "utf-8",
    "latin1": "latin-1",
    "ascii": "ascii",
    "gbk": "gbk",
    "windows-1252": "windows-1252",
    "shift_jis": "cp932",
}
