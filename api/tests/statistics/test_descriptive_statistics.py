import polars as pl
import pytest
from economicon.services.data.tables_store import TablesStore
from fastapi import status
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット (数値データ)
    df_numeric = pl.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50],
            "C": [5.234, 8.321, 2.976, 4.567, 9.629],
        }
    )
    manager.store_table("TestTableNumeric", df_numeric)
    # テスト用テーブルをセット (文字列データ)
    df_string = pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Alice", "Bob"],
            "category": ["A", "B", "A", "A", "C"],
        }
    )
    manager.store_table("TestTableString", df_string)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_descriptive_statistics_success_numeric(client, tables_store):
    # 数値データに対する記述統計の計算が正常に動作する
    payload = {
        "tableName": "TestTableNumeric",
        "columnNameList": ["A"],
        "statistics": ["mean", "median", "variance", "std"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # 結果の検証
    result = response_data["result"]
    assert result["tableName"] == "TestTableNumeric"
    assert result["statistics"]["A"]["mean"] == pytest.approx(3.0, abs=1e-5)
    assert result["statistics"]["A"]["median"] == pytest.approx(3.0, abs=1e-5)
    assert result["statistics"]["A"]["variance"] == pytest.approx(
        2.5, abs=1e-5
    )
    assert result["statistics"]["A"]["std"] == pytest.approx(
        1.5811388300841898, abs=1e-5
    )


def test_descriptive_statistics_success_all_stats(client, tables_store):
    # 全ての統計を計算する
    payload = {
        "tableName": "TestTableNumeric",
        "columnNameList": ["A", "B", "C"],
        "statistics": [
            "mean",
            "mode",
            "median",
            "variance",
            "std",
            "range",
            "iqr",
        ],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert result["tableName"] == "TestTableNumeric"
    assert result["statistics"]["B"]["mean"] == pytest.approx(30.0, abs=1e-5)
    assert result["statistics"]["B"]["median"] == pytest.approx(30.0, abs=1e-5)
    assert result["statistics"]["B"]["range"] == pytest.approx(40.0, abs=1e-5)
    assert result["statistics"]["B"]["iqr"] == pytest.approx(20.0, abs=1e-5)


def test_descriptive_statistics_success_string_mode(client, tables_store):
    # 文字列データに対するmode計算
    payload = {
        "tableName": "TestTableString",
        "columnNameList": ["name"],
        "statistics": ["mode"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    # name列は ['Alice', 'Bob', 'Charlie', 'Alice', 'Bob'] なので、AliceかBobがmode
    assert result["statistics"]["name"]["mode"] in ["Alice", "Bob"]


def test_descriptive_statistics_string_numeric_stats(client, tables_store):
    # 文字列データに対して数値専用統計を要求した場合はNoneが返される
    payload = {
        "tableName": "TestTableString",
        "columnNameList": ["name"],
        "statistics": ["mean", "variance", "std", "range", "iqr"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    # 文字列列に対する数値統計はNone
    assert result["statistics"]["name"]["mean"] is None
    assert result["statistics"]["name"]["variance"] is None
    assert result["statistics"]["name"]["std"] is None
    assert result["statistics"]["name"]["range"] is None
    assert result["statistics"]["name"]["iqr"] is None


def test_descriptive_statistics_invalid_table(client, tables_store):
    # 存在しないテーブル名
    payload = {
        "tableName": "NoTable",
        "columnNameList": ["A"],
        "statistics": ["mean"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "tableName 'NoTable'は存在しません。" == response_data["message"]


def test_descriptive_statistics_invalid_column(client, tables_store):
    # 存在しないカラム名を指定
    payload = {
        "tableName": "TestTableNumeric",
        "columnNameList": ["A", "Z"],
        "statistics": ["mean"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "columnName 'Z'は存在しません。" == response_data["message"]


def test_descriptive_statistics_invalid_statistic(client, tables_store):
    # サポートされていない統計を指定
    payload = {
        "tableName": "TestTableNumeric",
        "columnNameList": ["A"],
        "statistics": ["invalid_stat"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = (
        "statistics 'invalid_stat'はサポートされていません。"
        "利用可能: ['mean', 'mode', 'median', "
        "'variance', 'std', 'range', 'iqr']"
    )
    assert message == response_data["message"]


def test_descriptive_statistics_empty_statistics_list(client, tables_store):
    # 空の統計リストを指定
    payload = {
        "tableName": "TestTableNumeric",
        "columnNameList": ["A"],
        "statistics": [],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "NG"


def test_descriptive_statistics_empty_table_name(client, tables_store):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        "tableName": "",
        "columnNameList": ["A"],
        "statistics": ["mean"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


def test_descriptive_statistics_empty_column_name_list(client, tables_store):
    """
    columnNameListが空の場合はバリデーションエラーになる
    """
    payload = {
        "tableName": "TestTableNumeric",
        "columnNameList": [],
        "statistics": ["mean"],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]


def test_descriptive_statistics_empty_statistics(client, tables_store):
    """
    statisticsが空の場合はバリデーションエラーになる
    """
    payload = {
        "tableName": "TestTableNumeric",
        "columnNameList": ["A"],
        "statistics": [],
    }
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]


def test_descriptive_statistics_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {"columnNameList": ["A"], "statistics": ["mean"]}
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


def test_descriptive_statistics_missing_column_name_list(client, tables_store):
    """
    columnNameListが欠損している場合はバリデーションエラーになる
    """
    payload = {"tableName": "TestTableNumeric", "statistics": ["mean"]}
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "columnNameList" in response_data["message"]


def test_descriptive_statistics_missing_statistics(client, tables_store):
    """
    statisticsが欠損している場合はバリデーションエラーになる
    """
    payload = {"tableName": "TestTableNumeric", "columnNameList": ["A"]}
    response = client.post(
        "/api/statistics/descriptive",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "statistics" in response_data["message"]
