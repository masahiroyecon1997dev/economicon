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

# ワイブル分布
WEIBULL_A = 1.5
WEIBULL_SCALE = 1.0

# 対数正規分布
LOGNORMAL_MEAN = 0.0
LOGNORMAL_SIGMA = 1.0

# ベルヌーイ分布
BERNOULLI_P = 0.5

# 幾何分布
GEOMETRIC_P = 0.3

# 負の二項分布
NEG_BINOMIAL_N = 5
NEG_BINOMIAL_P = 0.3

# 固定値
FIXED_VALUE = 42.0

# シード値テスト用
SEED_VALUE = 42
SEED_VALUE_MAX = 100_000_000
SEED_VALUE_DATE = 20241231  # YYYYMMDD 形式


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
                "columnName": "UniformCol",
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
                "columnName": "NormalCol",
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
                "columnName": "BinomialCol",
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
                "columnName": "ExponentialCol",
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
                "columnName": "GammaCol",
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
                "columnName": "BetaCol",
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
                "columnName": "PoissonCol",
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
                "columnName": "HyperGeomCol",
                "distribution": {
                    "type": "hypergeometric",
                    "populationSize": HYPERGEOMETRIC_POPULATION,
                    "successCount": HYPERGEOMETRIC_SUCCESS_STATES,
                    "sampleSize": HYPERGEOMETRIC_DRAWS,
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


def test_add_weibull_column_success(client, tables_store):
    """ワイブル分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "WeibullCol",
                "distribution": {
                    "type": "weibull",
                    "a": WEIBULL_A,
                    "scale": WEIBULL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "weibull"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "WeibullCol", COL_B]
    assert len(df["WeibullCol"]) == ROW_COUNT
    # ワイブル分布は非負
    assert all(v >= 0 for v in df["WeibullCol"])


def test_add_lognormal_column_success(client, tables_store):
    """対数正規分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "LognormalCol",
                "distribution": {
                    "type": "lognormal",
                    "mean": LOGNORMAL_MEAN,
                    "sigma": LOGNORMAL_SIGMA,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "lognormal"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "LognormalCol", COL_B]
    assert len(df["LognormalCol"]) == ROW_COUNT
    # 対数正規分布は正値
    assert all(v > 0 for v in df["LognormalCol"])


def test_add_bernoulli_column_success(client, tables_store):
    """ベルヌーイ分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "BernoulliCol",
                "distribution": {
                    "type": "bernoulli",
                    "p": BERNOULLI_P,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "bernoulli"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "BernoulliCol", COL_B]
    assert len(df["BernoulliCol"]) == ROW_COUNT
    # ベルヌーイ分布は 0 または 1
    assert all(v in (0, 1) for v in df["BernoulliCol"])


def test_add_geometric_column_success(client, tables_store):
    """幾何分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "GeometricCol",
                "distribution": {
                    "type": "geometric",
                    "p": GEOMETRIC_P,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "geometric"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "GeometricCol", COL_B]
    assert len(df["GeometricCol"]) == ROW_COUNT
    # 幾何分布は 1 以上の整数
    assert all(v >= 1 for v in df["GeometricCol"])


def test_add_fixed_column_success(client, tables_store):
    """固定値カラムの追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "FixedCol",
                "distribution": {
                    "type": "fixed",
                    "value": FIXED_VALUE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "fixed"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "FixedCol", COL_B]
    assert len(df["FixedCol"]) == ROW_COUNT
    # 全行が固定値であることを確認
    assert all(v == FIXED_VALUE for v in df["FixedCol"])


def test_add_negative_binomial_column_success(client, tables_store):
    """負の二項分布の列追加が正常に動作する"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "NegBinomialCol",
                "distribution": {
                    "type": "negative_binomial",
                    "n": NEG_BINOMIAL_N,
                    "p": NEG_BINOMIAL_P,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["distributionType"] == "negative_binomial"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "NegBinomialCol", COL_B]
    assert len(df["NegBinomialCol"]) == ROW_COUNT
    # 負の二項分布は非負整数
    assert all(v >= 0 for v in df["NegBinomialCol"])


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
                "columnName": "TestCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "tableNameは必須です。"

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

    expected_msg = "simulationColumnは必須です。"

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
                "columnName": "TestCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
        },
    )

    expected_msg = "addPositionColumnは必須です。"

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
                "columnName": "TestCol",
                "distribution": {"type": "unsupported"},
            },
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "'unsupported'" in response_data["message"]

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
                "columnName": "TestCol",
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
    expected_msg = "一様分布では、'low'は'high'より小さい必要があります"
    assert response_data["message"] == expected_msg
    assert expected_msg in response_data["details"]

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
                "columnName": "TestCol",
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
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.normal"
        ".NormalParams.scaleは必須です。" in response_data["details"]
    )

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
                "columnName": "TestCol",
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
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.normal"
        ".NormalParams.locは数値で入力してください。"
        in response_data["details"]
    )

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
                "columnName": "TestCol",
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
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.normal"
        ".NormalParams.scaleは0.0より大きい値で入力してください。"
        in response_data["details"]
    )

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
                "columnName": "TestCol",
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
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.binomial"
        ".BinomialParams.pは1.0以下で入力してください。"
        in response_data["details"]
    )

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
                "columnName": "TestCol",
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
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.hypergeometric"
        ".function-after[validate_high(), HypergeometricParams]"
        ".populationSizeは必須です。" in response_data["details"]
    )

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
                "columnName": "SimCol",
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
                "columnName": COL_A,  # 既存の列名
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
                "columnName": "SimCol",
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


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_add_simulation_column_japanese_column_name(client, tables_store):
    """N1: 日本語の新規列名を指定しても正常に追加される"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "GDP成長率",
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
    assert response_data["result"]["columnName"] == "GDP成長率"

    df = tables_store.get_table(TABLE_NAME).table
    assert "GDP成長率" in df.columns


def test_add_simulation_column_japanese_position_column(client, tables_store):
    """N2: addPositionColumn に日本語列名を指定しても正常に挿入される"""
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame({"売上①": [1, 2, 3, 4, 5], COL_B: [10, 20, 30, 40, 50]}),
    )

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "uniform",
                    "low": UNIFORM_LOW,
                    "high": UNIFORM_HIGH,
                },
            },
            "addPositionColumn": "売上①",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == ["売上①", "SimCol", COL_B]


def test_add_simulation_column_emoji_column_name(client, tables_store):
    """N3: 絵文字のみの列名でも正常に追加される"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "🔥",
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
    assert response_data["result"]["columnName"] == "🔥"


def test_add_simulation_column_strip_whitespace_position_column(
    client, tables_store
):
    """N4: addPositionColumn の前後スペースは除去されて正常に処理される"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "uniform",
                    "low": UNIFORM_LOW,
                    "high": UNIFORM_HIGH,
                },
            },
            "addPositionColumn": "  A  ",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df.columns == [COL_A, "SimCol", COL_B]


def test_add_simulation_column_max_length_column_name(client, tables_store):
    """N5: 128文字（最大長境界値）の列名は正常に追加される"""
    long_name = "x" * 128
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": long_name,
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
    assert response_data["result"]["columnName"] == long_name


def test_add_simulation_column_too_long_column_name(client, tables_store):
    """N6: 129文字（最大長超過）の列名は422エラーになる"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "x" * 129,
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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        "simulationColumn.columnNameは128文字以内で入力してください。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_add_simulation_column_tab_char_column_name(client, tables_store):
    """N7: タブ文字を含む列名は422エラーになる"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "col\tA",
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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        "simulationColumn.columnNameに使用できない文字が含まれています。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


# ========================================
# 意地悪な入力テスト (D1-D8: 分布パラメータ極端値)
# ========================================


def test_add_simulation_column_uniform_low_equals_high(client, tables_store):
    """D1: 一様分布で low==high の場合は422エラーになる"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "uniform",
                    "low": 5.0,
                    "high": 5.0,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "一様分布では、'low'は'high'より小さい必要があります"
    assert response_data["message"] == expected_msg
    assert expected_msg in response_data["details"]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_uniform_reversed_range(client, tables_store):
    """D2: 一様分布で low > high の場合は422エラーになる"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "uniform",
                    "low": 10.0,
                    "high": 5.0,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "一様分布では、'low'は'high'より小さい必要があります"
    assert response_data["message"] == expected_msg
    assert expected_msg in response_data["details"]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_uniform_extreme_wide_range(
    client, tables_store
):
    """D3: 一様分布で超広範囲 (-1e10, 1e10) でも正常に追加される"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "WideRangeCol",
                "distribution": {
                    "type": "uniform",
                    "low": -1e10,
                    "high": 1e10,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"


def test_add_simulation_column_normal_scale_zero(client, tables_store):
    """D4: 正規分布で scale=0 は422エラーになる（gt=0 制約）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "normal",
                    "loc": 0.0,
                    "scale": 0.0,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR

    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.normal"
        ".NormalParams.scaleは0.0より大きい値で入力してください。"
        in response_data["details"]
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_normal_near_zero_scale(client, tables_store):
    """
    D5: 正規分布で scale=1e-15 (ゼロに非常に近い正の値) でも正常に追加される
    """
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "TinyScaleCol",
                "distribution": {
                    "type": "normal",
                    "loc": 0.0,
                    "scale": 1e-15,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"


def test_add_simulation_column_binomial_probability_zero(client, tables_store):
    """D6: 二項分布で p=0 は422エラーになる（gt=0 制約）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "binomial",
                    "n": BINOMIAL_N,
                    "p": 0.0,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.binomial"
        ".BinomialParams.pは0.0より大きい値で入力してください。"
        in response_data["details"]
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_binomial_probability_over_one(
    client, tables_store
):
    """D7: 二項分布で p=1.5 は422エラーになる（le=1 制約）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "binomial",
                    "n": BINOMIAL_N,
                    "p": 1.5,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.binomial"
        ".BinomialParams.pは1.0以下で入力してください。"
        in response_data["details"]
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_hypergeometric_k_exceeds_n(
    client, tables_store
):
    """D8: 超幾何分布で K>N の場合は422エラーになる"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "hypergeometric",
                    "N": 5,
                    "K": 6,
                    "n": 3,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.hypergeometric"
        ".function-after[validate_high(), HypergeometricParams]"
        ".populationSizeは必須です。" in response_data["details"]
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# 負の二項分布 (D-NB1 – D-NB3)


def test_add_simulation_column_negative_binomial_probability_zero(
    client, tables_store
):
    """D-NB1: 負の二項分布で p=0 は422エラーになる（gt=0 制約）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "negative_binomial",
                    "n": NEG_BINOMIAL_N,
                    "p": 0.0,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.negative_binomial"
        ".NegativeBinomialParams.pは0.0より大きい値で入力してください。"
        in response_data["details"]
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_negative_binomial_probability_over_one(
    client, tables_store
):
    """D-NB2: 負の二項分布で p=1.5 は422エラーになる（le=1 制約）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "negative_binomial",
                    "n": NEG_BINOMIAL_N,
                    "p": 1.5,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.negative_binomial"
        ".NegativeBinomialParams.pは1.0以下で入力してください。"
        in response_data["details"]
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_negative_binomial_n_zero(client, tables_store):
    """D-NB3: 負の二項分布で n=0 は422エラーになる（gt=0 制約）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SimCol",
                "distribution": {
                    "type": "negative_binomial",
                    "n": 0,
                    "p": NEG_BINOMIAL_P,
                },
            },
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "simulationColumn.distribution" in response_data["message"]
    assert (
        "simulationColumn.distribution.negative_binomial"
        ".NegativeBinomialParams.nは0より大きい値で入力してください。"
        in response_data["details"]
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# シード値テスト (S1-S6)
# ========================================


def test_add_simulation_column_with_seed_is_reproducible(
    client, tables_store
):
    """S1: 同一シードで追加した2カラムは同じ値を持つ"""
    # 1回目: seed=42 で SeedColA を追加
    response1 = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SeedColA",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
            "randomSeed": SEED_VALUE,
        },
    )
    assert response1.status_code == status.HTTP_200_OK

    # 2回目: 同一シードで SeedColB を追加
    response2 = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SeedColB",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
            "randomSeed": SEED_VALUE,
        },
    )
    assert response2.status_code == status.HTTP_200_OK

    df = tables_store.get_table(TABLE_NAME).table
    assert df["SeedColA"].to_list() == df["SeedColB"].to_list()


def test_add_simulation_column_seed_zero_is_valid(client, tables_store):
    """S2: randomSeed=0（最小境界値）は正常に受け付けられる"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SeedZeroCol",
                "distribution": {
                    "type": "uniform",
                    "low": UNIFORM_LOW,
                    "high": UNIFORM_HIGH,
                },
            },
            "addPositionColumn": COL_A,
            "randomSeed": 0,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_add_simulation_column_seed_max_is_valid(client, tables_store):
    """S3: randomSeed=100_000_000（最大境界値）は正常に受け付けられる"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SeedMaxCol",
                "distribution": {
                    "type": "uniform",
                    "low": UNIFORM_LOW,
                    "high": UNIFORM_HIGH,
                },
            },
            "addPositionColumn": COL_A,
            "randomSeed": SEED_VALUE_MAX,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_add_simulation_column_seed_exceeds_max_is_rejected(
    client, tables_store
):
    """S4: randomSeed > 100_000_000 は 422 VALIDATION_ERROR"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SeedOverCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
            "randomSeed": SEED_VALUE_MAX + 1,
        },
    )
    expected_msg = "randomSeedは100000000以下で入力してください。"
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_seed_negative_is_rejected(
    client, tables_store
):
    """S5: randomSeed < 0 は 422 VALIDATION_ERROR"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SeedNegCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
            "randomSeed": -1,
        },
    )
    expected_msg = "randomSeedは0以上で入力してください。"
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_add_simulation_column_seed_date_format_is_valid(
    client, tables_store
):
    """S6: 日付形式シード（20241231）は正常に受け付けられる"""
    response = client.post(
        "/api/column/add-simulation",
        json={
            "tableName": TABLE_NAME,
            "simulationColumn": {
                "columnName": "SeedDateCol",
                "distribution": {
                    "type": "normal",
                    "loc": NORMAL_LOC,
                    "scale": NORMAL_SCALE,
                },
            },
            "addPositionColumn": COL_A,
            "randomSeed": SEED_VALUE_DATE,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"
