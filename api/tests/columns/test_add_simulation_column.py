import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ========================================
# 定数
# ========================================

TABLE_NAME = "TestTable"
COL_A = "A"
COL_B = "B"
ROW_COUNT = 5

# 一様分布
UNIFORM_LOW = 0.0
UNIFORM_HIGH = 1.0

# 正規分布
NORMAL_LOC = 0.0
NORMAL_SCALE = 1.0

# 二項分布
BINOMIAL_N = 10
BINOMIAL_P = 0.5

# 指数分布
EXPONENTIAL_SCALE = 1.0

# ガンマ分布
GAMMA_SHAPE = 2.0
GAMMA_SCALE = 1.0

# ベータ分布
BETA_A = 2.0
BETA_B = 5.0

# ポアソン分布
POISSON_LAM = 3.0

# 超幾何分布
HYPERGEOMETRIC_POPULATION = 100
HYPERGEOMETRIC_SUCCESS_STATES = 30
HYPERGEOMETRIC_DRAWS = 10


# ========================================
# フィクスチャ
# ========================================


@pytest.fixture
def client():
    """TestClient のフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStore のフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame({COL_A: [1, 2, 3, 4, 5], COL_B: [10, 20, 30, 40, 50]})
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_add_uniform_column_success(client, tables_store):
    """一様分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "UniformCol",
                "distribution": {
                    "type": "uniform",
                    "low": UNIFORM_LOW,
                    "high": UNIFORM_HIGH,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == "UniformCol"
    assert response_data["result"]["distributionType"] == "uniform"

    df = tables_store.get_table(TABLE_NAME).table
    # COL_A の右隣に挿入される
    assert df.columns == [COL_A, "UniformCol", COL_B]
    assert len(df["UniformCol"]) == ROW_COUNT
    # 一様分布の範囲内
    assert all(UNIFORM_LOW <= v <= UNIFORM_HIGH for v in df["UniformCol"])
    # 元のデータが保持されている
    assert df[COL_A].to_list() == [1, 2, 3, 4, 5]


def test_add_normal_column_success(client, tables_store):
    """正規分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "NormalCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "normal"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "NormalCol", COL_B]
    assert len(df["NormalCol"]) == ROW_COUNT


def test_add_binomial_column_success(client, tables_store):
    """二項分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "BinomialCol",
                "distribution": {
                    "type": "binomial",
                    "n": BINOMIAL_N,
                    "p": BINOMIAL_P,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "binomial"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "BinomialCol", COL_B]
    # 二項分布は [0, n] の範囲
    assert all(0 <= v <= BINOMIAL_N for v in df["BinomialCol"])


def test_add_exponential_column_success(client, tables_store):
    """指数分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "ExponentialCol",
                "distribution": {
                    "type": "exponential",
                    "scale": EXPONENTIAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "ExponentialCol", COL_B]
    # 指数分布は非負
    assert all(v >= 0 for v in df["ExponentialCol"])


def test_add_gamma_column_success(client, tables_store):
    """ガンマ分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "GammaCol",
                "distribution": {
                    "type": "gamma",
                    "shape": GAMMA_SHAPE,
                    "scale": GAMMA_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(TABLE_NAME).table
    # ガンマ分布は非負
    assert all(v >= 0 for v in df["GammaCol"])


def test_add_beta_column_success(client, tables_store):
    """ベータ分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "BetaCol",
                "distribution": {
                    "type": "beta",
                    "a": BETA_A,
                    "b": BETA_B,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(TABLE_NAME).table
    # ベータ分布は [0, 1] の範囲
    assert all(0 <= v <= 1 for v in df["BetaCol"])


def test_add_poisson_column_success(client, tables_store):
    r"""ポアソン分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "PoissonCol",
                "distribution": {
                    "type": "poisson",
                    "lam": POISSON_LAM,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(TABLE_NAME).table
    # ポアソン分布は非負の整数
    assert all(v >= 0 for v in df["PoissonCol"])


def test_add_hypergeometric_column_success(client, tables_store):
    """超幾何分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "HyperGeomCol",
                "distribution": {
                    "type": "hypergeometric",
                    "N": HYPERGEOMETRIC_POPULATION,
                    "K": HYPERGEOMETRIC_SUCCESS_STATES,
                    "n": HYPERGEOMETRIC_DRAWS,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "hypergeometric"

    df = tables_store.get_table(TABLE_NAME).table
    # 超幾何分布: [0, min(K, n)] の範囲
    maximum = min(HYPERGEOMETRIC_SUCCESS_STATES, HYPERGEOMETRIC_DRAWS)
    assert all(0 <= v <= maximum for v in df["HyperGeomCol"])


# ========================================
# 異常系テスト（Pydantic バリデーション: 422）
# ========================================


def test_add_simulation_column_missing_table_name(client, tables_store):
    """tableName が未指定の場合"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "tableNameは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_missing_simulation_column(client, tables_store):
    """simulationColumn が未指定の場合"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "simulationColumnは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_missing_add_position_column(
    client, tables_store
):
    """addPositionColumn が未指定の場合"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
        },
    )

    expected_msg = "addPositionColumnは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_unsupported_distribution(client, tables_store):
    """サポートされていない分布タイプを指定した場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {"type": "unsupported"},
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_invalid_uniform_params_low_ge_high(client, tables_store):
    """一様分布で low >= high（model_validator 違反）の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    # low が high 以上（low=1.0, high=0.0）
    invalid_low = 1.0
    invalid_high = 0.0

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "uniform",
                    "low": invalid_low,
                    "high": invalid_high,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_missing_required_distribution_param(client, tables_store):
    """正規分布で scale が省略されている場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    # scale が省略
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_invalid_distribution_param_type(client, tables_store):
    """分布パラメータに文字列（不正な型）を指定した場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "normal",
                    "loc": "invalid",  # float でないと無効
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_normal_negative_scale(client, tables_store):
    """正規分布で scale が負の値（gt=0 違反）の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    negative_scale = -1.0

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": negative_scale,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_binomial_invalid_p_greater_than_one(client, tables_store):
    """二項分布で p > 1（le=1 違反）の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    invalid_p = 1.5

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "binomial",
                    "n": BINOMIAL_N,
                    "p": invalid_p,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_hypergeometric_invalid_k_exceeds_n(client, tables_store):
    """超幾何分布で K > N（model_validator 違反）の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    # K=15 が N=10 を超えている
    invalid_population = 10
    invalid_success_states = 15

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "TestCol",
                "distribution": {
                    "type": "hypergeometric",
                    "N": invalid_population,
                    "K": invalid_success_states,
                    "n": 5,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 異常系テスト（内部バリデーション: 400）
# ========================================


def test_invalid_table_name(client, tables_store):
    """存在しないテーブル名を指定した場合"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": "NoTable",
            "simulationColumn": {
                "column_name": "SimCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert response_data["message"] == "tableName 'NoTable'は存在しません。"

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_duplicate_column_name(client, tables_store):
    """既存の列名と同じ名前を新列名として指定した場合"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": COL_A,  # 既存の列名
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"]
        == f"newColumnName '{COL_A}'は既に存在します。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_invalid_position_column(client, tables_store):
    """addPositionColumn が存在しない列名の場合"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "column_name": "SimCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": "no_such_col",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "addPositionColumn 'no_such_col'は存在しません。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)
