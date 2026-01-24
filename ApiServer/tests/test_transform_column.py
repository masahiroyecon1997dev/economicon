import math

import polars as pl
import pytest
from analysisapp.services.data.tables_store import TablesStore
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
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 4, 8, 16],
        'B': [10, 20, 30, 40, 50],
        'C': [0.5, 1.0, 1.5, 2.0, 2.5]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_transform_column_log_natural_success(client, tables_store):
    # 自然対数変換のテスト
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_ln',
        'transformMethod': 'log'
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    assert response_data['result']['columnName'] == 'A_ln'
    # カラムが正しい位置に追加されているか
    df = tables_store.get_table('TestTable').table
    expected_columns = ['A', 'A_ln', 'B', 'C']
    assert df.columns == expected_columns
    # 自然対数の値が正しいか（近似値でチェック）
    ln_values = df['A_ln'].to_list()
    expected_ln_values = [math.log(1), math.log(2), math.log(4),
                          math.log(8), math.log(16)]
    for actual, expected in zip(ln_values, expected_ln_values):
        assert actual == pytest.approx(expected, abs=1e-5)


def test_transform_column_log_base2_success(client, tables_store):
    # 底2の対数変換のテスト
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_log2',
        'transformMethod': 'log',
        'logBase': 2
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 底2の対数の値が正しいか
    df = tables_store.get_table('TestTable').table
    log2_values = df['A_log2'].to_list()
    # log2(1), log2(2), log2(4), log2(8), log2(16)
    expected_log2_values = [0, 1, 2, 3, 4]
    for actual, expected in zip(log2_values, expected_log2_values):
        assert actual == pytest.approx(expected, abs=1e-5)


def test_transform_column_power_square_success(client, tables_store):
    # 二乗変換のテスト（デフォルト）
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_square',
        'transformMethod': 'power'
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 二乗の値が正しいか
    df = tables_store.get_table('TestTable').table
    square_values = df['A_square'].to_list()
    # 1^2, 2^2, 4^2, 8^2, 16^2
    expected_square_values = [1, 4, 16, 64, 256]
    assert square_values == expected_square_values


def test_transform_column_power_cube_success(client, tables_store):
    # 三乗変換のテスト
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_cube',
        'transformMethod': 'power',
        'exponent': 3
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 三乗の値が正しいか
    df = tables_store.get_table('TestTable').table
    cube_values = df['A_cube'].to_list()
    # 1^3, 2^3, 4^3, 8^3, 16^3
    expected_cube_values = [1, 8, 64, 512, 4096]
    assert cube_values == expected_cube_values


def test_transform_column_fractional_exponent(client, tables_store):
    # 小数の指数での累乗変換
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_sqrt',
        'transformMethod': 'power',
        'exponent': 0.5  # 平方根
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 平方根の値が正しいか
    df = tables_store.get_table('TestTable').table
    sqrt_values = df['A_sqrt'].to_list()
    expected_sqrt_values = [1.0, math.sqrt(2), 2.0, math.sqrt(8), 4.0]
    for actual, expected in zip(sqrt_values, expected_sqrt_values):
        assert actual == pytest.approx(expected, abs=1e-5)


def test_transform_column_root_square_success(client, tables_store):
    # 平方根変換のテスト
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_sqrt',
        'transformMethod': 'root',
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 平方根の値が正しいか
    df = tables_store.get_table('TestTable').table
    sqrt_values = df['A_sqrt'].to_list()
    # sqrt(1), sqrt(2), sqrt(4), sqrt(8), sqrt(16)
    expected_sqrt_values = [1, 1.41421, 2, 2.82843, 4]
    for actual, expected in zip(sqrt_values, expected_sqrt_values):
        assert actual == pytest.approx(expected, abs=1e-5)


def test_transform_column_root_cubic_success(client, tables_store):
    # 立方根変換のテスト
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_cbrt',
        'transformMethod': 'root',
        'rootIndex': 3
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 立方根の値が正しいか
    df = tables_store.get_table('TestTable').table
    cbrt_values = df['A_cbrt'].to_list()
    # cbrt(1), cbrt(2), cbrt(4), cbrt(8), cbrt(16)
    expected_cbrt_values = [1, 1.25992, 1.58740, 2, 2.51984]
    for actual, expected in zip(cbrt_values, expected_cbrt_values):
        assert actual == pytest.approx(expected, abs=1e-5)


def test_transform_column_root_fractional_success(client, tables_store):
    # 二乗変換のテスト
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_square',
        'transformMethod': 'root',
        'rootIndex': 0.5
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 二乗の値が正しいか
    df = tables_store.get_table('TestTable').table
    square_values = df['A_square'].to_list()
    # square(1), square(2), square(4), square(8), square(16)
    expected_square_values = [1, 4, 16, 64, 256]
    for actual, expected in zip(square_values, expected_square_values):
        assert actual == pytest.approx(expected, abs=1e-5)


def test_transform_column_invalid_table(client, tables_store):
    # 存在しないテーブル名
    payload = {
        'tableName': 'NoTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_ln',
        'transformMethod': 'log'
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable'は存在しません。" == response_data['message']


def test_transform_column_invalid_source_column(client, tables_store):
    # 存在しないソースカラム名
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'Z',
        'newColumnName': 'Z_ln',
        'transformMethod': 'log'
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "sourceColumnName 'Z'は存在しません。" in response_data['message']


def test_transform_column_duplicate_column_name(client, tables_store):
    # 既存のカラム名と重複
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'B',  # 既存のカラム名
        'transformMethod': 'log'
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newColumnName 'B'は既に存在します。" in response_data['message']


def test_transform_column_invalid_method(client, tables_store):
    # 無効な変換方法
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_invalid',
        'transformMethod': 'invalid'
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert ("transformMethod 'invalid' は無効です。有効なメソッド: "
            "log, power, root") == response_data[
        'message']


def test_transform_column_invalid_log_base(client, tables_store):
    # 無効な対数の底
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_log',
        'transformMethod': 'log',
        'logBase': 1  # 無効：底が1
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "logBaseは1ではない正の数値である必要があります" \
        == response_data['message']


def test_transform_column_negative_log_base(client, tables_store):
    # 負の対数の底
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_log',
        'transformMethod': 'log',
        'logBase': -2  # 無効：負の値
    }
    response = client.post(
        '/api/column/transform',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "logBase は 1 ではない正の数値である必要があります" \
        == response_data['message']
