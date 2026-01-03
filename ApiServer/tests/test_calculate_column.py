import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl

from main import app
from analysisapp.services.data.tables_manager import TablesManager


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    # チE�Eブルをクリア
    manager.clear_tables()
    # チE��ト用チE�EブルをセチE��
    df = pl.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6],
        'C': [10.0, 20.0, 30.0],
        'D': [2.5, 3.5, 4.5],
        'text_col': ['hello', 'world', 'test']  # 非数値刁E
    })
    manager.store_table('TestTable', df)
    yield manager
    # チE��ト後�EクリーンアチE�E
    manager.clear_tables()



def test_calculate_column_simple_addition(client, tables_manager):
    # 単純な足し箁E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'E',
        'calculationExpression': 'pl.col("A") + pl.col("B")'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    assert response_data['result']['columnName'] == 'E'
    # 計算結果の確誁E
    df = tables_manager.get_table('TestTable').table
    assert 'E' in df.columns
    expected_values = [5, 7, 9]  # [1+4, 2+5, 3+6]
    assert df['E'].to_list() == expected_values


def test_calculate_column_complex_expression(client, tables_manager):
    # 褁E��な計算式（四剁E��算とかっこ！E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'F',
        'calculationExpression': 'pl.col("C")/pl.col("D")+'
                                 '(pl.col("A") + pl.col("B"))*2'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 計算結果の確誁E
    df = tables_manager.get_table('TestTable').table
    assert 'F' in df.columns
    # 期征E��: 10.0/2.5+(1+4)*2=4+10=14, 20.0/3.5+(2+5)*2=5.714...+14
    # =19.714..., 30.0/4.5+(3+6)*2=6.666...+18=24.666...
    result_values = df['F'].to_list()
    assert abs(result_values[0] - 14.0) < 1e-5
    assert abs(result_values[1] - 19.714285714285715) < 1e-5
    assert abs(result_values[2] - 24.666666666666668) < 1e-5


def test_calculate_column_with_numbers(client, tables_manager):
    # 列と数値の計箁E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'G',
        'calculationExpression': 'pl.col("A") * 5 + 10'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    # 計算結果の確誁E
    df = tables_manager.get_table('TestTable').table
    expected_values = [15, 20, 25]  # [1*5+10, 2*5+10, 3*5+10]
    assert df['G'].to_list() == expected_values


def test_calculate_column_invalid_table(client, tables_manager):
    # 存在しなぁE��ーブル吁E
    payload = {
        'tableName': 'NoTable',
        'newColumnName': 'E',
        'calculationExpression': 'pl.col("A") + pl.col("B")'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable' does not exist" in response_data['message']


def test_calculate_column_invalid_column(client, tables_manager):
    # 存在しなぁE�E名を参�E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'E',
        'calculationExpression': 'pl.col("A") + pl.col("Z")'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName in calculationExpression 'Z' does not exist." in response_data['message']


def test_calculate_column_non_numeric_column(client, tables_manager):
    # 非数値列を参�E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'E',
        'calculationExpression': 'pl.col("A") + pl.col("text_col")'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName in calculationExpression 'text_col' is not numeric" in response_data['message']


def test_calculate_column_empty_expression(client, tables_manager):
    # 空の計算弁E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'E',
        'calculationExpression': ''
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "calculationExpression is required." in response_data['message']


def test_calculate_column_no_column_reference(client, tables_manager):
    # 列参照がなぁE��算弁E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'E',
        'calculationExpression': '5 + 10'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "calculationExpression must be with at least 1 column." in response_data['message']


def test_calculate_column_duplicate_column_name(client, tables_manager):
    # 既存�E列名と同じ新列名
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'A',  # 既存�E列名
        'calculationExpression': 'pl.col("B") + pl.col("C")'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newColumnName 'A' already exists" in response_data['message']


def test_calculate_column_invalid_syntax(client, tables_manager):
    # 不正な計算弁E
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'E',
        'calculationExpression': 'pl.col("A") @ pl.col("B")'  # 不正な演算孁E
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Invalid calculation expression" in response_data['message']


def test_calculate_column_division_by_zero_handling(client, tables_manager):
    # ゼロ除算�EチE��チE
    # ゼロを含むチE�Eブルを作�E
    df_zero = pl.DataFrame({
        'X': [1, 2, 0],
        'Y': [0, 2, 1]
    })
    tables_manager.store_table('ZeroTable', df_zero)
    payload = {
        'tableName': 'ZeroTable',
        'newColumnName': 'Z',
        'calculationExpression': 'pl.col("X") / pl.col("Y")'
    }
    response = client.post(
        '/api/column/calculate',
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    # ゼロ除算�E結果を確認！Eolarsはinfまた�Enullを返す�E�E
    df = tables_manager.get_table('ZeroTable').table
    result_values = df['Z'].to_list()
    # 1/0 = inf, 2/2 = 1.0, 0/1 = 0.0
    import math
    assert math.isinf(result_values[0])
    assert result_values[1] == 1.0
    assert result_values[2] == 0.0
