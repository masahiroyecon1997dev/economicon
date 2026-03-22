import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# test用テーブル名とデータ
table_name = "test_table"
test_data = pl.DataFrame(
    {"column1": [1, 2, 3, 4, 5], "column2": ["a", "b", "c", "d", "e"]}
)
# テーブルの行数
_TOTAL_ROWS = 5
# テーブル行数を超えた取得に使用する行数（テーブルは5行）
_FETCH_BEYOND_ROWS = 10
# fetchRows の最大値
_MAX_FETCH_ROWS = 10000


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    # テスト用のテーブルをセットアップ
    manager = TablesStore()
    # テーブルをクリア
    manager.clear_tables()
    manager.store_table(table_name, test_data)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_fetch_data_to_json_success(client, tables_store):
    # 正常系テスト: JSONデータを取得
    start_row = 1
    fetch_rows = 2
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == table_name
    # メタ情報の確認
    assert response_data["result"]["totalRows"] == _TOTAL_ROWS
    assert response_data["result"]["startRow"] == start_row
    assert response_data["result"]["endRow"] == start_row + fetch_rows
    # データの内容を確認
    data = response_data["result"]["data"]
    expected_data = test_data[1:3].write_json()
    assert data == expected_data


def test_fetch_data_to_json_table_not_found(client, tables_store):
    # 異常系テスト: 存在しないテーブル名
    not_existent_table = "non_existent_table"
    start_row = 1
    fetch_rows = 3
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": not_existent_table,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    message = "tableName 'non_existent_table'は存在しません。"
    assert message == response_data["message"]


def test_fetch_data_to_json_invalid_start_row_range(client, tables_store):
    # 異常系テスト: 無効な行範囲 startRow
    start_row = -1
    fetch_rows = 4
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "startRowは0以上で入力してください。" == response_data["message"]
    assert ["startRowは0以上で入力してください。"] == response_data["details"]


def test_fetch_data_to_json_invalid_fetch_rows(client, tables_store):
    # 異常系テスト: 無効な取得行数 fetchRows
    start_row = 1
    fetch_rows = 0
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "fetchRowsは1以上で入力してください。" == response_data["message"]
    assert ["fetchRowsは1以上で入力してください。"] == response_data["details"]


def test_fetch_data_to_json_missing_table_name(client, tables_store):
    # 異常系テスト: 必須パラメータが不足している場合（tableName）
    not_table_name = ""
    start_row = 1
    fetch_rows = 6
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": not_table_name,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_fetch_data_to_json_missing_start_row(client, tables_store):
    # 異常系テスト: startRow に文字列を渡した場合（型エラー）
    start_row = ""
    fetch_rows = 6
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "startRowは整数で入力してください。" == response_data["message"]
    assert ["startRowは整数で入力してください。"] == response_data["details"]


def test_fetch_data_to_json_missing_fetch_rows(client, tables_store):
    # 異常系テスト: fetchRows に文字列を渡した場合（型エラー）
    start_row = 1
    fetch_rows = ""
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "fetchRowsは整数で入力してください。" == response_data["message"]
    assert ["fetchRowsは整数で入力してください。"] == response_data["details"]


def test_fetch_data_to_json_fetch_beyond_table(client, tables_store):
    # 正常系テスト: テーブルの行数を超える取得行数
    start_row = 2
    # テーブルは5行なので3行目から最後までの3行を取得
    fetch_rows = _FETCH_BEYOND_ROWS
    response = client.post(
        "/api/table/fetch-data-to-json",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "fetchRows": fetch_rows,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # メタ情報の確認
    assert response_data["result"]["totalRows"] == _TOTAL_ROWS
    assert response_data["result"]["startRow"] == start_row
    assert response_data["result"]["endRow"] == _TOTAL_ROWS  # 最後の行
    # データの内容を確認（3行目から最後まで）
    data = response_data["result"]["data"]
    expected_data = test_data[2:5].write_json()
    assert data == expected_data


# Pydanticバリデーションテスト


def test_fetch_data_to_json_pydantic_empty_table_name(client, tables_store):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {"tableName": "", "startRow": 1, "fetchRows": 3}
    response = client.post(
        "/api/table/fetch-data-to-json",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "tableNameは1文字以上で入力してください。" == response_data["message"]
    )
    assert ["tableNameは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_fetch_data_to_json_pydantic_negative_start_row(client, tables_store):
    """
    startRowが負の場合はバリデーションエラーになる
    """
    payload = {"tableName": table_name, "startRow": -1, "fetchRows": 3}
    response = client.post(
        "/api/table/fetch-data-to-json",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "startRowは0以上で入力してください。" == response_data["message"]
    assert ["startRowは0以上で入力してください。"] == response_data["details"]


def test_fetch_data_to_json_pydantic_negative_fetch_rows(client, tables_store):
    """
    fetchRowsが負の場合はバリデーションエラーになる
    """
    payload = {"tableName": table_name, "startRow": 1, "fetchRows": -1}
    response = client.post(
        "/api/table/fetch-data-to-json",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "fetchRowsは1以上で入力してください。" == response_data["message"]
    assert ["fetchRowsは1以上で入力してください。"] == response_data["details"]


def test_fetch_data_to_json_pydantic_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {"startRow": 1, "fetchRows": 3}
    response = client.post(
        "/api/table/fetch-data-to-json",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須です。" == response_data["message"]
    assert ["tableNameは必須です。"] == response_data["details"]


def test_fetch_data_to_json_pydantic_missing_start_row(client, tables_store):
    """
    startRowが欠損している場合はバリデーションエラーになる
    """
    payload = {"tableName": table_name, "fetchRows": 3}
    response = client.post(
        "/api/table/fetch-data-to-json",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "startRowは必須です。" == response_data["message"]
    assert ["startRowは必須です。"] == response_data["details"]


def test_fetch_data_to_json_pydantic_missing_fetch_rows(client, tables_store):
    """
    fetchRowsが欠損している場合、fetchRowsにはデフォルト値500が設定されるため
    200 OK
    """
    payload = {"tableName": table_name, "startRow": 1}
    response = client.post(
        "/api/table/fetch-data-to-json",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert response_data["result"]["tableName"] == table_name


# ---------------------------------------------------------------------------
# 意地悪なリクエストテスト
# ---------------------------------------------------------------------------


def test_fetch_data_to_json_tablename_only_spaces(client, tables_store):
    """
    tableNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {"tableName": "   ", "startRow": 0, "fetchRows": 3}
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_fetch_data_to_json_tablename_tab_chars(client, tables_store):
    """
    tableNameがタブ文字のみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {"tableName": "\t", "startRow": 0, "fetchRows": 3}
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_fetch_data_to_json_tablename_leading_trailing_spaces(
    client, tables_store
):
    """
    tableNameの前後スペースはトリムされ、正常に取得できる
    """
    payload = {
        "tableName": f"  {table_name}  ",
        "startRow": 0,
        "fetchRows": 3,
    }
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert response_data["result"]["tableName"] == table_name


def test_fetch_data_to_json_tablename_tab_leading_trailing(
    client, tables_store
):
    """
    tableNameの前後タブ文字はトリムされ、正常に取得できる
    """
    payload = {
        "tableName": f"\t{table_name}\t",
        "startRow": 0,
        "fetchRows": 3,
    }
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert response_data["result"]["tableName"] == table_name


def test_fetch_data_to_json_tablename_japanese(client, tables_store):
    """
    tableNameに日本語を使った場合、型は有効だが存在しないので400になる
    """
    payload = {"tableName": "日本語テーブル名", "startRow": 0, "fetchRows": 3}
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_fetch_data_to_json_tablename_emoji(client, tables_store):
    """
    tableNameに絵文字を使った場合、型は有効だが存在しないので400になる
    """
    payload = {"tableName": "🚀table", "startRow": 0, "fetchRows": 3}
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_fetch_data_to_json_fetch_rows_max(client, tables_store):
    """
    fetchRowsが最大値（10000）のとき正常に取得できる
    """
    payload = {
        "tableName": table_name,
        "startRow": 0,
        "fetchRows": _MAX_FETCH_ROWS,
    }
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_fetch_data_to_json_fetch_rows_exceeds_max(client, tables_store):
    """
    fetchRowsが最大値を超えた場合422エラーになる
    """
    payload = {
        "tableName": table_name,
        "startRow": 0,
        "fetchRows": _MAX_FETCH_ROWS + 1,
    }
    response = client.post("/api/table/fetch-data-to-json", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = f"fetchRowsは{_MAX_FETCH_ROWS}以下で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]
