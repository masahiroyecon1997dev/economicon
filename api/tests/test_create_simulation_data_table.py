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
    # テスト前にテーブルをクリア
    manager.clear_tables()
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_create_table_with_distribution_columns(client, tables_store):
    """分布データ列を持つテーブル作成のテスト"""

    # テスト用の列設定
    column_settings = [
        {
            "columnName": "normal_col",
            "dataType": "distribution",
            "distributionType": "normal",
            "distributionParams": {"loc": 0, "scale": 1},
        },
        {
            "columnName": "uniform_col",
            "dataType": "distribution",
            "distributionType": "uniform",
            "distributionParams": {"low": 0, "high": 10},
        },
    ]
    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 100,
        "columnSettings": column_settings,
    }
    response = client.post("/api/table/create-simulation-data", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "test_table"

    # store_tableに渡されたDataFrameの確認
    assert "test_table" in tables_store.get_table_name_list()
    columns = tables_store.get_column_name_list("test_table")
    assert "normal_col" in columns
    assert "uniform_col" in columns
    df = tables_store.get_table("test_table").table
    assert len(columns) == 2
    assert len(df) == 100


def test_create_table_with_fixed_columns(client, tables_store):
    """固定値列を持つテーブル作成のテスト"""

    # テスト用の列設定
    column_settings = [
        {"columnName": "fixed_col_1", "dataType": "fixed", "fixedValue": 42},
        {
            "columnName": "fixed_col_2",
            "dataType": "fixed",
            "fixedValue": "constant_string",
        },
    ]

    payload = {
        "tableName": "fixed_table",
        "tableNumberOfRows": 50,
        "columnSettings": column_settings,
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "fixed_table"

    # テーブルの確認
    assert "fixed_table" in tables_store.get_table_name_list()
    columns = tables_store.get_column_name_list("fixed_table")
    assert "fixed_col_1" in columns
    assert "fixed_col_2" in columns
    df = tables_store.get_table("fixed_table").table
    assert len(df) == 50

    # 固定値の確認
    assert (df["fixed_col_1"] == 42).all()
    assert (df["fixed_col_2"] == "constant_string").all()


def test_create_table_with_mixed_columns(client, tables_store):
    """分布データ列と固定値列の混合テーブル作成のテスト"""

    # テスト用の列設定
    column_settings = [
        {
            "columnName": "exponential_col",
            "dataType": "distribution",
            "distributionType": "exponential",
            "distributionParams": {"scale": 2.0},
        },
        {"columnName": "fixed_id", "dataType": "fixed", "fixedValue": 1},
    ]

    payload = {
        "tableName": "mixed_table",
        "tableNumberOfRows": 30,
        "columnSettings": column_settings,
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "mixed_table"

    # テーブルの確認
    assert "mixed_table" in tables_store.get_table_name_list()
    columns = tables_store.get_column_name_list("mixed_table")
    assert "exponential_col" in columns
    assert "fixed_id" in columns
    df = tables_store.get_table("mixed_table").table
    assert len(df) == 30
    assert len(df.columns) == 2

    # 固定値の確認
    assert (df["fixed_id"] == 1).all()


def test_validation_error_duplicate_table_name(client, tables_store):
    """重複するテーブル名のバリデーションエラーテスト"""

    # 既存のテーブルを作成
    existing_payload = {
        "tableName": "existing_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {"columnName": "test_col", "dataType": "fixed", "fixedValue": 1}
        ],
    }
    client.post("/api/table/create-simulation-data", json=existing_payload)

    # 同じ名前のテーブルを再度作成しようとする
    duplicate_payload = {
        "tableName": "existing_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {"columnName": "test_col2", "dataType": "fixed", "fixedValue": 2}
        ],
    }

    response = client.post(
        "/api/table/create-simulation-data", json=duplicate_payload
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_validation_error_invalid_num_rows(client, tables_store):
    """無効な行数のバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 0,  # 無効な行数
        "columnSettings": [
            {"columnName": "test_col", "dataType": "fixed", "fixedValue": 1}
        ],
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_validation_error_empty_column_settings(client, tables_store):
    """空の列設定のバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 10,
        "columnSettings": [],  # 空の列設定
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_validation_error_missing_column_name(client, tables_store):
    """列名が不足している場合のバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {
                "dataType": "fixed",
                "fixedValue": 1,
                # 'columnName' が不足
            }
        ],
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_validation_error_invalid_data_type(client, tables_store):
    """無効なデータタイプのバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {
                "columnName": "test_col",
                "dataType": "invalid_type",  # 無効なデータタイプ
                "fixedValue": 1,
            }
        ],
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_validation_error_missing_distribution_params(client, tables_store):
    """分布パラメータが不足している場合のバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {
                "columnName": "test_col",
                "dataType": "distribution",
                "distributionType": "normal",
                # 'distributionParams' が不足
            }
        ],
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_validation_error_missing_fixed_value(client, tables_store):
    """固定値が不足している場合のバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {
                "columnName": "test_col",
                "dataType": "fixed",
                # 'fixedValue' が不足
            }
        ],
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_validation_error_invalid_distribution_type(client, tables_store):
    """無効な分布タイプのバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {
                "columnName": "test_col",
                "dataType": "distribution",
                "distributionType": "invalid_distribution",  # 無効な分布タイプ
                "distributionParams": {"param1": 1},
            }
        ],
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_validation_error_invalid_distribution_params(client, tables_store):
    """無効な分布パラメータのバリデーションエラーテスト"""

    payload = {
        "tableName": "test_table",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {
                "columnName": "test_col",
                "dataType": "distribution",
                "distributionType": "normal",
                "distributionParams": {"invalidParam": 1},  # 無効なパラメータ
            }
        ],
    }

    response = client.post("/api/table/create-simulation-data", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# Pydanticバリデーションテスト


def test_create_simulation_data_table_pydantic_empty_table_name(
    client, tables_store
):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        "tableName": "",
        "tableNumberOfRows": 10,
        "columnSettings": [
            {"columnName": "test_col", "dataType": "fixed", "fixedValue": 1}
        ],
    }
    response = client.post(
        "/api/table/create-simulation-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


def test_create_simulation_data_table_pydantic_negative_number_of_rows(
    client, tables_store
):
    """
    tableNumberOfRowsが負の場合はバリデーションエラーになる
    """
    payload = {
        "tableName": "TestTable",
        "tableNumberOfRows": -1,
        "columnSettings": [
            {"columnName": "test_col", "dataType": "fixed", "fixedValue": 1}
        ],
    }
    response = client.post(
        "/api/table/create-simulation-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableNumberOfRows" in response_data["message"]


def test_create_simulation_data_table_pydantic_empty_column_settings(
    client, tables_store
):
    """
    columnSettingsが空の場合はバリデーションエラーになる
    """
    payload = {
        "tableName": "TestTable",
        "tableNumberOfRows": 10,
        "columnSettings": [],
    }
    response = client.post(
        "/api/table/create-simulation-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "List should have at least 1 item" in response_data["message"]


def test_create_simulation_data_table_pydantic_missing_table_name(
    client, tables_store
):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "tableNumberOfRows": 10,
        "columnSettings": [
            {"columnName": "test_col", "dataType": "fixed", "fixedValue": 1}
        ],
    }
    response = client.post(
        "/api/table/create-simulation-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


def test_create_simulation_data_table_pydantic_missing_number_of_rows(
    client, tables_store
):
    """
    tableNumberOfRowsが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "tableName": "TestTable",
        "columnSettings": [
            {"columnName": "test_col", "dataType": "fixed", "fixedValue": 1}
        ],
    }
    response = client.post(
        "/api/table/create-simulation-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableNumberOfRows" in response_data["message"]


def test_create_simulation_data_table_pydantic_missing_column_settings(
    client, tables_store
):
    """
    columnSettingsが欠損している場合はバリデーションエラーになる
    """
    payload = {"tableName": "TestTable", "tableNumberOfRows": 10}
    response = client.post(
        "/api/table/create-simulation-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "columnSettings" in response_data["message"]
