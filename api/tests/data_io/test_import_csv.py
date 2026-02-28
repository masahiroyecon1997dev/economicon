import os
import shutil
import tempfile

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# テストデータの定数
_SEMCOL_N_COLS = 3  # セミコロン区切りテストの列数
_SEMCOL_N_ROWS = 2  # セミコロン区切りテストの行数
_BOM_N_COLS = 2  # BOM テストの列数
_BOM_N_ROWS = 2  # BOM テストの行数
_MAX_TABLE_NAME_LEN = 128  # テーブル名の最大文字数
_ENCODING_ERROR = (
    "encodingは次のいずれかである必要があります: "
    "'utf8', 'latin1', 'ascii', 'gbk', 'windows-1252' or 'shift_jis'"
)
_SJIS_EXPECTED_NAMES = ["\u5c71\u7530", "\u7530\u4e2d", "\u9234\u6728"]
_LATIN1_EXPECTED_CITY = "K\xf6ln"
_WINDOWS1252_EXPECTED_WORD = "r\xe9sum\xe9"
_ASCII_EXPECTED_KEY = "hello"
_CSV_IMPORT_ERROR_MSG = "Failed to parse CSV file: Invalid format or encoding."


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    # テスト用のCSVファイルパス
    test_data = pl.DataFrame(
        {
            "col_1": [1, 2, 3],
            "col_2": [10.1, 20.2, 30.3],
            "col_3": ["A", "B", "C"],
        }
    )
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    test_data.write_csv(f"{test_dir}/TestDataComma.csv", separator=",")
    test_data.write_csv(f"{test_dir}/TestDataTab1.tsv", separator="\t")
    with open(f"{test_dir}/Empty.csv", "w", encoding="utf-8"):
        pass
    test_data.write_excel(f"{test_dir}/TestDataXlsx.xlsx")
    yield manager, test_dir
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)


def test_import_csv_comma_separator(client, prepared_data):
    """
    カンマ区切りのCSVファイルをパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_comma, encoding="utf8")
    # APIリクエスト
    request_data = {
        "filePath": test_csv_comma,
        "tableName": "TestCommaTable",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestCommaTable" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestCommaTable").table
    assert expected_data.equals(df)


def test_import_csv_tab_separator(client, prepared_data):
    """
    タブ区切りのファイルをCSVとしてパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_tab = f"{test_dir}/TestDataTab1.tsv"
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_tab, separator="\t", encoding="utf8")
    # APIリクエスト
    request_data = {
        "filePath": test_csv_tab,
        "tableName": "TestTabTable",
        "separator": "\t",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestTabTable" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestTabTable").table
    assert expected_data.equals(df)


def test_import_csv_custom_separator(client, prepared_data):
    """
    セミコロン区切りのCSVファイルのテスト（テストファイルを作成）
    """
    tables_store, test_dir = prepared_data
    # 一時的なセミコロン区切りファイルを作成
    temp_data = "col1;col2;col3\n1;2;3\n4;5;6\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        f.write(temp_data)
        temp_path = f.name
    try:
        # APIリクエスト
        request_data = {
            "filePath": temp_path,
            "tableName": "TestSemicolonTable",
            "separator": ";",
        }
        response = client.post("/api/data/import", json=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert "OK" == response_data["code"]
        assert "TestSemicolonTable" == response_data["result"]["tableName"]
        # データの検証
        df = tables_store.get_table("TestSemicolonTable").table
        assert _SEMCOL_N_COLS == len(df.columns)
        assert _SEMCOL_N_ROWS == len(df)
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


def test_import_csv_default_separator(client, prepared_data):
    """
    separatorパラメータを省略した場合のテスト（デフォルトはカンマ）
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_comma, encoding="utf8")
    # APIリクエスト（separatorを省略）
    request_data = {
        "filePath": test_csv_comma,
        "tableName": "TestDefaultSeparator",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestDefaultSeparator" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestDefaultSeparator").table
    assert expected_data.equals(df)


def test_import_csv_file_not_exists(client, prepared_data):
    """
    存在しないファイルパスを指定した場合のテスト
    """
    tables_store, test_dir = prepared_data
    request_data = {
        "filePath": "/non/existent/file.csv",
        "tableName": "TestNonExistent",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.PATH_NOT_FOUND == response_data["code"]
    message = "filePath '/non/existent/file.csv'は存在しません。"
    assert message == response_data["message"]


def test_import_csv_invalid_file_extension(client, prepared_data):
    """
    非対応拡張子（.txt）を指定した場合のテスト
    統合 /import エンドポイントでサポート外拡張子は 500 が返る
    """
    tables_store, test_dir = prepared_data
    # 非対応拡張子のファイルを作成
    txt_path = f"{test_dir}/unsupported.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("col1,col2\n1,2\n")
    request_data = {
        "filePath": txt_path,
        "tableName": "TestInvalidExtension",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert ErrorCode.UNSUPPORTED_FILE_TYPE == response_data["code"]


def test_import_csv_missing_file_path(client, prepared_data):
    """
    filePathパラメータが未指定の場合のテスト
    FastAPIのバリデーションエラーで422が返る
    """
    tables_store, test_dir = prepared_data
    request_data = {"tableName": "TestMissingPath", "separator": ","}
    response = client.post("/api/data/import", json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "filePathは必須です。" == response_data["message"]
    assert ["filePathは必須です。"] == response_data["details"]


def test_import_csv_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    FastAPIのバリデーションエラーで422が返る
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    request_data = {"filePath": test_csv_comma, "separator": ","}
    response = client.post("/api/data/import", json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須です。" == response_data["message"]
    assert ["tableNameは必須です。"] == response_data["details"]


def test_import_csv_duplicate_table_name(client, prepared_data):
    """
    既存のテーブル名と重複する場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    # 先にテーブルを作成
    first_request_data = {
        "filePath": test_csv_comma,
        "tableName": "DuplicateTable",
        "separator": ",",
    }
    client.post("/api/data/import", json=first_request_data)
    # 同じテーブル名で再度作成を試行
    second_request_data = {
        "filePath": test_csv_comma,
        "tableName": "DuplicateTable",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=second_request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_ALREADY_EXISTS == response_data["code"]
    # テーブル名重複エラーメッセージを確認
    message = "tableName 'DuplicateTable'は既に存在します。"
    assert message == response_data["message"]


def test_import_csv_empty_separator(client, prepared_data):
    """
    空の区切り文字を指定した場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv_comma,
        "tableName": "TestEmptySeparator",
        "separator": "",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    message = "separatorは1文字以上で入力してください。"
    assert message == response_data["message"]
    assert [message] == response_data["details"]


def test_import_csv_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    FastAPIのバリデーションエラーで422が返る
    """
    response = client.post(
        "/api/data/import",
        content=b"invalid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "JSON decode error" == response_data["message"]


@pytest.mark.skip(
    reason="このテストは現在、発生させる方法が不明なためスキップされています。"
)
def test_import_csv_malformed_csv(client, prepared_data):
    """
    不正な形式のCSVファイルを指定した場合のテスト
    """
    # エラーCSVファイルが存在する場合
    request_data = {
        "filePath": "/ECONOMICON/SampleData/Error.csv",
        "tableName": "TestMalformed",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Failed to parse CSV file: Invalid format or encoding."
    assert message == response_data["message"]


def test_import_csv_encoding_utf8bom(client, prepared_data):
    """
    UTF-8 BOM エンコーディングの CSV ファイルをインポートするテスト
    （Polars は utf8 エンコーディングで BOM を自動処理する）
    """
    tables_store, test_dir = prepared_data
    bom_path = f"{test_dir}/TestBom.csv"
    with open(bom_path, "w", encoding="utf-8-sig") as f:
        f.write("col_1,col_2\n1,10\n2,20\n")
    request_data = {
        "filePath": bom_path,
        "tableName": "TestBomTable",
        "separator": ",",
        "encoding": "utf8",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestBomTable" == response_data["result"]["tableName"]
    df = tables_store.get_table("TestBomTable").table
    assert _BOM_N_COLS == len(df.columns)
    assert _BOM_N_ROWS == len(df)


def test_import_csv_invalid_encoding(client, prepared_data):
    """
    無効なエンコーディングを指定した場合はバリデーションエラーになる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv,
        "tableName": "TestInvalidEncoding",
        "encoding": "invalid-encoding",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert _ENCODING_ERROR == response_data["message"]
    assert [_ENCODING_ERROR] == response_data["details"]


def test_import_csv_empty_file_path(client, prepared_data):
    """
    filePathが空文字列の場合はバリデーションエラーになる
    """
    request_data = {"filePath": "", "tableName": "TestTable", "separator": ","}
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "filePathは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_import_csv_empty_table_name(client, prepared_data):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    request_data = {
        "filePath": "/some/path/test.csv",
        "tableName": "",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_import_csv_tablename_only_spaces(client, prepared_data):
    """
    tableNameがスペースのみの場合はトリムされ空文字列になりエラーになる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {"filePath": test_csv, "tableName": "   ", "separator": ","}
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = "tableNameは1文字以上で入力してください。"
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_csv_tablename_only_tabs(client, prepared_data):
    """
    tableNameがタブ文字のみの場合はトリムされ空文字列になりエラーになる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv,
        "tableName": "\t\t\t",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = "tableNameは1文字以上で入力してください。"
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_csv_tablename_embedded_tab(client, prepared_data):
    """
    tableNameにタブ文字が埋め込まれた場合はパターン違反エラーになる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv,
        "tableName": "test\ttable",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = "tableNameに使用できない文字が含まれています。"
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_csv_tablename_exceeds_max_length(client, prepared_data):
    """
    tableNameが最大文字数（128文字）を超える場合はバリデーションエラーになる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    over_limit = "a" * (_MAX_TABLE_NAME_LEN + 1)
    request_data = {
        "filePath": test_csv,
        "tableName": over_limit,
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = (
        f"tableNameは{_MAX_TABLE_NAME_LEN}文字以内で入力してください。"
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_csv_tablename_at_max_length(client, prepared_data):
    """
    tableNameがちょうど最大文字数（128文字）の場合は正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    max_length_name = "a" * _MAX_TABLE_NAME_LEN
    request_data = {
        "filePath": test_csv,
        "tableName": max_length_name,
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert max_length_name == response_data["result"]["tableName"]


def test_import_csv_tablename_leading_trailing_spaces(client, prepared_data):
    """
    tableNameの前後にスペースがある場合はトリムされて正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv,
        "tableName": "  TrimmedCsvTable  ",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    # スペースはトリムされて保存される
    assert "TrimmedCsvTable" == response_data["result"]["tableName"]


def test_import_csv_tablename_emoji(client, prepared_data):
    """
    tableNameに絵文字を使った場合は正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv,
        "tableName": "データ📊テーブル",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "データ📊テーブル" == response_data["result"]["tableName"]


def test_import_csv_tablename_japanese(client, prepared_data):
    """
    tableNameに日本語を使った場合は正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv,
        "tableName": "人口統計データ",
        "separator": ",",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "人口統計データ" == response_data["result"]["tableName"]


# ─────────────────────────────────────────────────────────────
# エンコーディングテスト（正常系）
# ─────────────────────────────────────────────────────────────


def test_import_csv_encoding_shift_jis(client, prepared_data):
    """
    Shift-JIS エンコードの CSV を encoding: shift_jis で正常インポートでき、
    日本語の列名・値が正しく復元される
    """
    tables_store, test_dir = prepared_data
    sjis_path = f"{test_dir}/ShiftJis.csv"
    with open(sjis_path, "wb") as f:
        f.write("名前,年齢\n山田,30\n田中,25\n鈴木,40\n".encode("shift_jis"))
    request_data = {
        "filePath": sjis_path,
        "tableName": "SjisTable",
        "separator": ",",
        "encoding": "shift_jis",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "SjisTable" == response_data["result"]["tableName"]
    df = tables_store.get_table("SjisTable").table
    assert df.columns == ["名前", "年齢"]
    assert df["名前"].to_list() == _SJIS_EXPECTED_NAMES


def test_import_csv_encoding_latin1(client, prepared_data):
    """
    latin1 エンコードの CSV を encoding: latin1 で正常インポートでき、
    西欧文字（ウムラウト等）が正しく復元される
    """
    tables_store, test_dir = prepared_data
    latin1_path = f"{test_dir}/Latin1.csv"
    with open(latin1_path, "wb") as f:
        f.write(
            "name,city\nM\xfcller,K\xf6ln\nDupont,Paris\n".encode("latin1")
        )
    request_data = {
        "filePath": latin1_path,
        "tableName": "Latin1Table",
        "separator": ",",
        "encoding": "latin1",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    df = tables_store.get_table("Latin1Table").table
    assert df.columns == ["name", "city"]
    assert _LATIN1_EXPECTED_CITY in df["city"].to_list()


def test_import_csv_encoding_windows1252(client, prepared_data):
    """
    windows-1252 エンコードの CSV を
    encoding: windows-1252 で正常インポートできる
    """
    tables_store, test_dir = prepared_data
    win1252_path = f"{test_dir}/Win1252.csv"
    with open(win1252_path, "wb") as f:
        f.write(
            "word,meaning\nr\xe9sum\xe9,CV\ncaf\xe9,drinks\n".encode(
                "windows-1252"
            )
        )
    request_data = {
        "filePath": win1252_path,
        "tableName": "Win1252Table",
        "separator": ",",
        "encoding": "windows-1252",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    df = tables_store.get_table("Win1252Table").table
    assert df.columns == ["word", "meaning"]
    assert _WINDOWS1252_EXPECTED_WORD in df["word"].to_list()


def test_import_csv_encoding_ascii(client, prepared_data):
    """
    ASCII 範囲のみのデータを encoding: ascii で正常インポートできる
    """
    tables_store, test_dir = prepared_data
    ascii_path = f"{test_dir}/Ascii.csv"
    with open(ascii_path, "wb") as f:
        f.write("key,value\nhello,world\nfoo,bar\n".encode("ascii"))
    request_data = {
        "filePath": ascii_path,
        "tableName": "AsciiTable",
        "separator": ",",
        "encoding": "ascii",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    df = tables_store.get_table("AsciiTable").table
    assert df.columns == ["key", "value"]
    assert _ASCII_EXPECTED_KEY in df["key"].to_list()


# ─────────────────────────────────────────────────────────────
# エンコーディングテスト（異常系）
# ─────────────────────────────────────────────────────────────


def test_import_csv_encoding_mismatch_shift_jis_as_utf8(client, prepared_data):
    """
    Shift-JIS ファイルを encoding: utf8 で読み込むとパースエラー（500）になる
    """
    tables_store, test_dir = prepared_data
    sjis_path = f"{test_dir}/ShiftJisMismatch.csv"
    with open(sjis_path, "wb") as f:
        f.write("名前,年齢\n山田,30\n".encode("shift_jis"))
    request_data = {
        "filePath": sjis_path,
        "tableName": "MismatchTable",
        "separator": ",",
        "encoding": "utf8",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert ErrorCode.CSV_IMPORT_ERROR == response_data["code"]
    assert _CSV_IMPORT_ERROR_MSG == response_data["message"]
