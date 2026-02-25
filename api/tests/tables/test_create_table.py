import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ─────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────
MAX_TABLE_NAME_LENGTH = 128
DEFAULT_ROW_COUNT = 3
DEFAULT_COLUMN_NAMES = ["A", "B"]

# ベースペイロード（正常系共通）
_BASE_PAYLOAD: dict = {
    "tableName": "NewTable",
    "rowCount": DEFAULT_ROW_COUNT,
    "columnNames": DEFAULT_COLUMN_NAMES,
}

# model_validatorのエラーメッセージ（filePath未指定時にrowCountが必須）
_MSG_ROW_REQUIRED = (
    "Value error, row_count is required when file_path is not specified"
)
# エンコーディングバリデーションエラーメッセージ
_ENCODING_ERROR = (
    "csvEncodingは次のいずれかである必要があります: "
    "'utf8', 'latin1', 'ascii', 'gbk', 'windows-1252' or 'shift_jis'"
)


# ─────────────────────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────────────────────
def test_create_table_success(client, tables_store):
    """テーブルを正常に作成できる"""
    response = client.post("/api/table/create", json=_BASE_PAYLOAD)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "NewTable"
    df = tables_store.get_table("NewTable").table
    assert df.shape == (DEFAULT_ROW_COUNT, len(DEFAULT_COLUMN_NAMES))
    assert df.columns == DEFAULT_COLUMN_NAMES
    assert df["A"].to_list() == [None] * DEFAULT_ROW_COUNT


# ─────────────────────────────────────────────────────────────
# 異常系 400：重複テーブル名
# ─────────────────────────────────────────────────────────────
def test_create_table_duplicate_table_name(client, tables_store):
    """既存テーブル名と重複する場合は 400 DATA_ALREADY_EXISTS"""
    client.post("/api/table/create", json=_BASE_PAYLOAD)
    response = client.post("/api/table/create", json=_BASE_PAYLOAD)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert response_data["message"] == "tableName 'NewTable'は既に存在します。"
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（空・0値・型不正）
# ─────────────────────────────────────────────────────────────
def test_create_table_pydantic_empty_table_name(client, tables_store):
    """tableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": ""}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


def test_create_table_pydantic_zero_row_count(client, tables_store):
    """rowCountが0の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": 0}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは1以上で入力してください。"
    assert response_data["details"] == ["rowCountは1以上で入力してください。"]


def test_create_table_pydantic_negative_row_count(client, tables_store):
    """rowCountが負の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": -1}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは1以上で入力してください。"
    assert response_data["details"] == ["rowCountは1以上で入力してください。"]


def test_create_table_pydantic_row_count_string(client, tables_store):
    """rowCountが文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": "A"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは整数で入力してください。"
    assert response_data["details"] == ["rowCountは整数で入力してください。"]


def test_create_table_pydantic_empty_column_names(client, tables_store):
    """columnNamesが空リストの場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "columnNames": []}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "columnNamesは1件以上ある必要があります。"
    )
    assert response_data["details"] == [
        "columnNamesは1件以上ある必要があります。"
    ]


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（必須項目欠損）
# ─────────────────────────────────────────────────────────────
def test_create_table_pydantic_missing_table_name(client, tables_store):
    """tableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "tableName"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "tableNameは必須です。"
    assert response_data["details"] == ["tableNameは必須です。"]


def test_create_table_pydantic_missing_row_count(client, tables_store):
    """rowCountが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "rowCount"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == _MSG_ROW_REQUIRED
    assert response_data["details"] == [_MSG_ROW_REQUIRED]


def test_create_table_pydantic_missing_column_names(client, tables_store):
    """columnNamesが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "columnNames"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "columnNamesは必須です。"
    assert response_data["details"] == ["columnNamesは必須です。"]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N7）
# ─────────────────────────────────────────────────────────────
def test_n1_table_name_japanese(client, tables_store):
    """N1: tableNameに日本語を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "日本語テーブル"}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n2_table_name_emoji(client, tables_store):
    """N2: tableNameに絵文字を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "Table🎲"}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n3_table_name_surrounding_spaces(client, tables_store):
    """N3: tableNameの前後スペースはトリムされ正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "  NewTable2  "}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n4_table_name_max_length(client, tables_store):
    """N4: tableNameが最大文字数（128文字）でも正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "a" * MAX_TABLE_NAME_LENGTH}
    response = client.post("/api/table/create", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n5_table_name_exceeds_max_length(client, tables_store):
    """N5: tableNameが最大文字数を超えると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": "a" * (MAX_TABLE_NAME_LENGTH + 1)}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"tableNameは{MAX_TABLE_NAME_LENGTH}文字以内で入力してください。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_n6_table_name_with_tab(client, tables_store):
    """N6: tableNameにタブ文字が含まれると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": "Tab\tTable"}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "tableNameに使用できない文字が含まれています。"
    )
    assert response_data["details"] == [
        "tableNameに使用できない文字が含まれています。"
    ]


def test_n7_table_name_only_spaces(client, tables_store):
    """
    N7:
    tableNameがスペースのみの場合、トリム後に空になり 422 VALIDATION_ERROR
    """
    payload = {**_BASE_PAYLOAD, "tableName": "   "}
    response = client.post("/api/table/create", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


# ─────────────────────────────────────────────────────────────
# ファイル添付テスト用ヘルパー
# ─────────────────────────────────────────────────────────────
_URL_CREATE = "/api/table/create"

# has_header=False: ヘッダ行込みで3行
_CSV_WITH_HEADER_FALSE = 3
# has_header=True: ヘッダスキップで2行
_CSV_WITH_HEADER_TRUE = 2
# rowCountトリムテスト: 目標行数=3、最終行の整数値=3
_TRIM_ROWS = 3
_TRIM_LAST_VALUE = 3
# rowCountパディングテスト: 目標行数=4、追加Null行数=2
_PAD_ROWS = 4
_PAD_NULL_COUNT = 2
# Excelデータ行数=2、Parquetデータ行数=3
_EXCEL_DATA_ROWS = 2
_PARQUET_DATA_ROWS = 3


def _file_payload(
    file_path: str,
    *,
    table_name: str = "FileTable",
    column_names: list[str] | None = None,
    has_header: bool = False,
    row_count: int | None = None,
) -> dict:
    """ファイル添付リクエストペイロードを生成するヘルパー"""
    payload: dict = {
        "tableName": table_name,
        "columnNames": (
            column_names if column_names is not None else ["A", "B"]
        ),
        "filePath": file_path,
        "hasHeader": has_header,
    }
    if row_count is not None:
        payload["rowCount"] = row_count
    return payload


# ─────────────────────────────────────────────────────────────
# ファイル添付テスト：正常系
# ─────────────────────────────────────────────────────────────


def test_file_csv_column_names_applied(client, tables_store, tmp_path):
    """CSVをhas_header=Falseで読み込み、column_namesが適用される"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("H1,H2\n1,2\n3,4\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(str(csv_file), column_names=["A", "B"]),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    assert df.columns == ["A", "B"]


def test_file_has_header_false_first_row_is_data(
    client, tables_store, tmp_path
):
    """has_header=Falseのとき元ヘッダ行がデータ1行目として含まれる"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("H1,H2\n1,2\n3,4\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["A", "B"],
            has_header=False,
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    # has_header=False: ヘッダ行込みで3行
    assert df.height == _CSV_WITH_HEADER_FALSE
    # 1行目は元ヘッダ行の値
    assert df["A"][0] == "H1"


def test_file_has_header_true_header_skipped(client, tables_store, tmp_path):
    """has_header=Trueのときヘッダ行がスキップされデータ行数のみ返る"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("H1,H2\n1,2\n3,4\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["A", "B"],
            has_header=True,
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    # has_header=True: データ行のみ2行
    assert df.height == _CSV_WITH_HEADER_TRUE
    expected_cell_value = 1
    # ヘッダ行がスキップされ、1行目がデータの先頭になる
    assert df["A"][0] == expected_cell_value


def test_file_column_names_fewer_than_file(client, tables_store, tmp_path):
    """column_namesがファイル列数より少ない → 超過列はPolars自動命名"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["A", "B"],
            has_header=False,
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    # 指定分はリネーム、残りはPolarsの自動命名（"column_N"形式）
    assert df.columns[0] == "A"
    assert df.columns[1] == "B"
    assert df.columns[2].startswith("column_")


def test_file_column_names_more_than_file(client, tables_store, tmp_path):
    """column_namesがファイル列数より多い → 超過分はNone埋め列として追加"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["A", "B", "C"],
            has_header=False,
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    assert df.columns == ["A", "B", "C"]
    # 超過列 C はすべて Null
    assert df["C"].is_null().all()


def test_file_row_count_omit_uses_file_rows(client, tables_store, tmp_path):
    """rowCount省略時はファイルの行数がそのまま使われる"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("1,10\n2,20\n3,30\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["x", "y"],
            has_header=False,
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    assert df.height == _TRIM_ROWS  # CSV3行がそのまま読込


def test_file_row_count_trim(client, tables_store, tmp_path):
    """rowCountがファイル行数より少ない → 超過行は切り捨てられる"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("1,10\n2,20\n3,30\n4,40\n5,50\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["x", "y"],
            has_header=False,
            row_count=3,
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    assert df.height == _TRIM_ROWS
    assert df["x"][-1] == _TRIM_LAST_VALUE


def test_file_row_count_padding(client, tables_store, tmp_path):
    """rowCountがファイル行数より多い → 不足分はNull埋めになる"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("r1,v1\nr2,v2\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["x", "y"],
            has_header=False,
            row_count=4,
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    assert df.height == _PAD_ROWS
    # 追加された2行はNull
    assert df["x"].is_null().sum() == _PAD_NULL_COUNT


def test_file_excel_basic(client, tables_store, tmp_path):
    """Excelファイルを添付して正常読み込みできる"""
    xlsx_file = tmp_path / "sample.xlsx"
    pl.DataFrame({"col0": [1, 2], "col1": [10, 20]}).write_excel(xlsx_file)
    # シート名なし: pl.read_excel(path) が呼ばれデフォルトでヘッダあり読込
    resp = client.post(
        _URL_CREATE,
        json={
            "tableName": "ExcelTable",
            "columnNames": ["A", "B"],
            "filePath": str(xlsx_file),
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("ExcelTable").table
    assert df.columns == ["A", "B"]
    assert df.height == _EXCEL_DATA_ROWS


def test_file_parquet_basic(client, tables_store, tmp_path):
    """Parquetファイルを添付して正常読み込みできる"""
    parquet_file = tmp_path / "sample.parquet"
    pl.DataFrame({"orig_a": [1, 2, 3], "orig_b": [4, 5, 6]}).write_parquet(
        parquet_file
    )
    resp = client.post(
        _URL_CREATE,
        json={
            "tableName": "ParquetTable",
            "columnNames": ["A", "B"],
            "filePath": str(parquet_file),
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("ParquetTable").table
    assert df.columns == ["A", "B"]
    assert df.height == _PARQUET_DATA_ROWS


# ─────────────────────────────────────────────────────────────
# ファイル添付テスト：異常系
# ─────────────────────────────────────────────────────────────


def test_file_path_not_found(client, tables_store, tmp_path):
    """存在しないファイルパスは 400 PATH_NOT_FOUND"""
    nonexistent = str(tmp_path / "nonexistent.csv")
    resp = client.post(_URL_CREATE, json=_file_payload(nonexistent))
    data = resp.json()
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == ErrorCode.PATH_NOT_FOUND


def test_file_invalid_extension(client, tables_store, tmp_path):
    """未対応の拡張子 (.txt) は 400 INVALID_FILE_TYPE"""
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("a,b\n1,2\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(str(txt_file)),
    )
    data = resp.json()
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == ErrorCode.INVALID_FILE_TYPE


# ─────────────────────────────────────────────────────────────
# ファイル添付テスト：冪等性
# ─────────────────────────────────────────────────────────────


def test_file_invalid_path_idempotent(client, tables_store, tmp_path):
    """同一の存在しないパスで連続リクエスト → message が完全一致する"""
    nonexistent = str(tmp_path / "missing.csv")
    resp1 = client.post(
        _URL_CREATE,
        json=_file_payload(nonexistent, table_name="Table1"),
    )
    resp2 = client.post(
        _URL_CREATE,
        json=_file_payload(nonexistent, table_name="Table2"),
    )
    assert resp1.json()["message"] == resp2.json()["message"]


# ─────────────────────────────────────────────────────────────
# ファイル添付テスト：カバレッジ補完
# ─────────────────────────────────────────────────────────────


def test_file_excel_with_sheet_name(client, tables_store, tmp_path):
    """Excelシート名を指定した場合のhas_header読み込みパス"""
    xlsx_file = tmp_path / "sample.xlsx"
    pl.DataFrame({"col0": [1, 2], "col1": [10, 20]}).write_excel(
        xlsx_file, worksheet="Sheet1"
    )
    resp = client.post(
        _URL_CREATE,
        json={
            "tableName": "ExcelSheetTable",
            "columnNames": ["A", "B"],
            "filePath": str(xlsx_file),
            "excelSheetName": "Sheet1",
            "hasHeader": True,
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("ExcelSheetTable").table
    assert df.columns == ["A", "B"]
    assert df.height == _EXCEL_DATA_ROWS


def test_file_row_count_exact_match(client, tables_store, tmp_path):
    """rowCount == ファイル行数のとき行数調整なしでそのまま返る"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("1,10\n2,20\n3,30\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["x", "y"],
            has_header=False,
            row_count=_TRIM_ROWS,  # ファイル行数と同じ3行を指定
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    df = tables_store.get_table("FileTable").table
    assert df.height == _TRIM_ROWS


# ─────────────────────────────────────────────────────────────
# エンコーディングテスト（異常系: 422）
# ─────────────────────────────────────────────────────────────


def test_file_csv_encoding_invalid_value(client, tables_store, tmp_path):
    """csvEncoding に不正な値を指定すると 422 VALIDATION_ERROR"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("1,10\n2,20\n3,30\n", encoding="utf-8")
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["A", "B"],
            has_header=False,
        )
        | {"csvEncoding": "invalid-enc"},
    )
    data = resp.json()
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert data["code"] == ErrorCode.VALIDATION_ERROR
    assert data["message"] == _ENCODING_ERROR
    assert data["details"] == [_ENCODING_ERROR]


# ─────────────────────────────────────────────────────────────
# エンコーディングテスト（正常系）
# ─────────────────────────────────────────────────────────────


def test_file_csv_encoding_shift_jis_success(client, tables_store, tmp_path):
    """
    Shift-JIS エンコードの CSV を csvEncoding=shift_jis
    で正常に読み込める
    """
    csv_file = tmp_path / "sjis.csv"
    csv_file.write_bytes("山田,10\n田中,20\n鈴木,30\n".encode("shift_jis"))
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["名前", "値"],
            has_header=False,
            row_count=3,
        )
        | {"csvEncoding": "shift_jis"},
    )
    data = resp.json()
    assert resp.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table("FileTable").table
    assert df["名前"].to_list() == ["山田", "田中", "鈴木"]
    assert df["値"].to_list() == [10, 20, 30]


def test_file_csv_encoding_latin1_success(client, tables_store, tmp_path):
    """latin1 エンコードの CSV を csvEncoding=latin1 で正常に読み込める"""
    csv_file = tmp_path / "latin1.csv"
    csv_file.write_bytes(
        "K\xf6ln,1\nM\xfcnchen,2\n\xd6stersund,3\n".encode("latin1")
    )
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["都市", "番号"],
            has_header=False,
            row_count=3,
        )
        | {"csvEncoding": "latin1"},
    )
    data = resp.json()
    assert resp.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"
    df = tables_store.get_table("FileTable").table
    assert "Köln" in df["都市"].to_list()
    assert "München" in df["都市"].to_list()


def test_file_csv_encoding_mismatch_shift_jis_as_utf8(
    client, tables_store, tmp_path
):
    """
    Shift-JIS ファイルを csvEncoding=utf8 で読み込むと
    500 CREATE_TABLE_ERROR
    """
    csv_file = tmp_path / "sjis.csv"
    csv_file.write_bytes("山田,10\n田中,20\n鈴木,30\n".encode("shift_jis"))
    resp = client.post(
        _URL_CREATE,
        json=_file_payload(
            str(csv_file),
            column_names=["名前", "値"],
            has_header=False,
            row_count=3,
        )
        | {"csvEncoding": "utf8"},
    )
    data = resp.json()
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert data["code"] == ErrorCode.CREATE_TABLE_ERROR
    assert (
        data["message"]
        == "テーブルの作成処理中に予期しないエラーが発生しました"
    )
