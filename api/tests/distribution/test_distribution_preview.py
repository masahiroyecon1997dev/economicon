"""POST /api/distribution/preview エンドポイントのテスト"""

from starlette import status

URL = "/api/distribution/preview"

_DEFAULT_X_COUNT = 200
_MIN_X_COUNT = 50
_MAX_X_COUNT = 2000
_CUSTOM_X_COUNT = 100
_BERNOULLI_POINT_COUNT = 2
_UNIFORM_HIGH = 5.0


# -----------------------------------------------------------
# 連続分布 成功ケース
# -----------------------------------------------------------


def test_distribution_preview_normal_success(client):
    """正規分布で連続プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "normal",
            "mean": 0.0,
            "standardDeviation": 1.0,
        }
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["isDiscrete"] is False
    assert len(result["x"]) == _DEFAULT_X_COUNT
    assert len(result["yDensity"]) == _DEFAULT_X_COUNT
    assert len(result["yCumulative"]) == _DEFAULT_X_COUNT
    assert all(isinstance(v, float) for v in result["x"])
    assert all(v >= 0.0 for v in result["yDensity"])
    assert all(0.0 <= v <= 1.0 for v in result["yCumulative"])


def test_distribution_preview_uniform_success(client):
    """一様分布で x が [low, high] 範囲に収まる"""
    payload = {
        "distribution": {
            "type": "uniform",
            "low": 1.0,
            "high": 5.0,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is False
    assert result["x"][0] >= 1.0
    assert result["x"][-1] <= _UNIFORM_HIGH


def test_distribution_preview_chi_square_success(client):
    """カイ二乗分布で連続プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "chi_square",
            "degreesOfFreedom": 5,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is False
    assert len(result["x"]) == _DEFAULT_X_COUNT
    assert all(v > 0.0 for v in result["x"])
    assert all(v >= 0.0 for v in result["yDensity"])


def test_distribution_preview_f_distribution_success(client):
    """F分布で連続プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "f_distribution",
            "numeratorDf": 5,
            "denominatorDf": 10,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is False
    assert len(result["x"]) == _DEFAULT_X_COUNT
    assert all(v > 0.0 for v in result["x"])


def test_distribution_preview_lognormal_success(client):
    """対数正規分布で連続プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "lognormal",
            "logMean": 0.0,
            "logStandardDeviation": 1.0,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is False
    assert len(result["x"]) == _DEFAULT_X_COUNT


def test_distribution_preview_exponential_success(client):
    """指数分布で x_min が 0 になる"""
    payload = {
        "distribution": {
            "type": "exponential",
            "scaleParameter": 1.0,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is False
    assert result["x"][0] == 0.0


def test_distribution_preview_weibull_success(client):
    """ワイブル分布で x_min が 0 になる"""
    payload = {
        "distribution": {
            "type": "weibull",
            "shapeParameter": 2.0,
            "scaleParameter": 1.0,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["x"][0] == 0.0


# -----------------------------------------------------------
# 離散分布 成功ケース
# -----------------------------------------------------------


def test_distribution_preview_binomial_success(client):
    """二項分布で離散プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "binomial",
            "trialCount": 10,
            "successProbability": 0.3,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is True
    assert len(result["x"]) >= 1
    # 整数値が float として返る
    assert all(v == int(v) for v in result["x"])
    assert all(v >= 0.0 for v in result["yDensity"])


def test_distribution_preview_bernoulli_success(client):
    """ベルヌーイ分布の x は [0.0, 1.0] に固定される"""
    payload = {
        "distribution": {
            "type": "bernoulli",
            "successProbability": 0.5,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is True
    assert result["x"] == [0.0, 1.0]
    assert len(result["yDensity"]) == _BERNOULLI_POINT_COUNT
    assert len(result["yCumulative"]) == _BERNOULLI_POINT_COUNT


def test_distribution_preview_poisson_success(client):
    """ポアソン分布で離散プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "poisson",
            "rate": 3.0,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is True
    assert result["x"][0] >= 0.0


def test_distribution_preview_geometric_success(client):
    """幾何分布で x_min が 1 以上になる"""
    payload = {
        "distribution": {
            "type": "geometric",
            "successProbability": 0.5,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is True
    assert result["x"][0] >= 1.0


def test_distribution_preview_hypergeometric_success(client):
    """超幾何分布で離散プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "hypergeometric",
            "populationSize": 50,
            "successCount": 10,
            "sampleSize": 5,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is True


def test_distribution_preview_negative_binomial_success(client):
    """負の二項分布で離散プレビューデータが返る"""
    payload = {
        "distribution": {
            "type": "negative_binomial",
            "targetSuccessCount": 5,
            "successProbability": 0.3,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isDiscrete"] is True


# -----------------------------------------------------------
# x_count 指定
# -----------------------------------------------------------


def test_distribution_preview_x_count_custom(client):
    """x_count を指定すると連続分布の点数が変わる"""
    payload = {
        "distribution": {
            "type": "normal",
            "mean": 0.0,
            "standardDeviation": 1.0,
        },
        "xCount": 100,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert len(result["x"]) == _CUSTOM_X_COUNT


def test_distribution_preview_x_count_min_boundary(client):
    """x_count=50（最小値）は正常に処理される"""
    payload = {
        "distribution": {
            "type": "normal",
            "mean": 0.0,
            "standardDeviation": 1.0,
        },
        "xCount": 50,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert len(result["x"]) == _MIN_X_COUNT


def test_distribution_preview_x_count_max_boundary(client):
    """x_count=2000（最大値）は正常に処理される"""
    payload = {
        "distribution": {
            "type": "normal",
            "mean": 0.0,
            "standardDeviation": 1.0,
        },
        "xCount": 2000,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert len(result["x"]) == _MAX_X_COUNT


def test_distribution_preview_x_count_below_min(client):
    """x_count=49（最小値未満）は 422 が返る"""
    payload = {
        "distribution": {
            "type": "normal",
            "mean": 0.0,
            "standardDeviation": 1.0,
        },
        "xCount": 49,
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_distribution_preview_x_count_above_max(client):
    """x_count=2001（最大値超過）は 422 が返る"""
    payload = {
        "distribution": {
            "type": "normal",
            "mean": 0.0,
            "standardDeviation": 1.0,
        },
        "xCount": 2001,
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "VALIDATION_ERROR"


# -----------------------------------------------------------
# 非対応タイプ（400 Bad Request）
# -----------------------------------------------------------


def test_distribution_preview_fixed_unsupported(client):
    """FIXED タイプはプレビュー非対応で 400 が返る"""
    payload = {
        "distribution": {
            "type": "fixed",
            "value": 5.0,
        }
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DISTRIBUTION_PREVIEW_UNSUPPORTED_TYPE"
    expected_msg = "Distribution type 'fixed' is not supported for preview"
    assert response_data["message"] == expected_msg


def test_distribution_preview_sequence_unsupported(client):
    """SEQUENCE タイプはプレビュー非対応で 400 が返る"""
    payload = {
        "distribution": {
            "type": "sequence",
            "start": 1,
            "step": 1,
        }
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DISTRIBUTION_PREVIEW_UNSUPPORTED_TYPE"
    expected_msg = "Distribution type 'sequence' is not supported for preview"
    assert response_data["message"] == expected_msg


# -----------------------------------------------------------
# レスポンス構造確認
# -----------------------------------------------------------


def test_distribution_preview_response_keys(client):
    """レスポンスに必要なキーがすべて含まれる"""
    payload = {
        "distribution": {
            "type": "gamma",
            "shapeParameter": 2.0,
            "scaleParameter": 1.0,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert set(result.keys()) == {
        "isDiscrete",
        "x",
        "yDensity",
        "yCumulative",
    }
    assert isinstance(result["isDiscrete"], bool)
    assert isinstance(result["x"], list)
    assert isinstance(result["yDensity"], list)
    assert isinstance(result["yCumulative"], list)


def test_distribution_preview_array_lengths_match(client):
    """x / yDensity / yCumulative の長さが一致する"""
    payload = {
        "distribution": {
            "type": "beta",
            "alpha": 2.0,
            "beta": 5.0,
        }
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert len(result["x"]) == len(result["yDensity"])
    assert len(result["x"]) == len(result["yCumulative"])
