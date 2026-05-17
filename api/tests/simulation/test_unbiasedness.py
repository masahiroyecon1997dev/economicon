"""POST /api/simulation/unbiasedness エンドポイントのテスト"""

import math

from starlette import status

URL = "/api/simulation/unbiasedness"

# ---------------------------------------------------------------------------
# デフォルトペイロード
# ---------------------------------------------------------------------------

_DEFAULT = {
    "numTrials": 100,
    "sampleSize": 30,
    "trueBeta": 1.0,
    "errorVariance": 1.0,
    "xDistribution": {"xMean": 0.0, "xVariance": 1.0},
}


# ---------------------------------------------------------------------------
# 成功ケース
# ---------------------------------------------------------------------------


def test_unbiasedness_success(client):
    """デフォルトパラメータでリクエストが成功する"""
    response = client.post(URL, json=_DEFAULT)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"

    result = data["result"]
    assert result["trueBeta"] == _DEFAULT["trueBeta"]
    assert len(result["betaEstimates"]) == _DEFAULT["numTrials"]


def test_unbiasedness_beta_estimates_count(client):
    """numTrials に等しい数の betaEstimates が返る"""
    payload = {**_DEFAULT, "numTrials": 300}
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    expected_count = 300
    assert len(result["betaEstimates"]) == expected_count


def test_unbiasedness_true_beta_echoed(client):
    """指定した trueBeta がレスポンスに正しく返る"""
    payload = {**_DEFAULT, "trueBeta": -1.5}
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    expected_true_beta = -1.5
    assert result["trueBeta"] == expected_true_beta


def test_unbiasedness_beta_estimates_are_finite(client):
    """betaEstimates はすべて有限値"""
    response = client.post(URL, json=_DEFAULT)
    estimates = response.json()["result"]["betaEstimates"]

    assert all(math.isfinite(v) for v in estimates)


def test_unbiasedness_custom_x_distribution(client):
    """xDistribution を指定して成功する"""
    payload = {
        **_DEFAULT,
        "xDistribution": {"xMean": 1.0, "xVariance": 2.0},
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_unbiasedness_min_params(client):
    """最小パラメータ (numTrials=10, sampleSize=5) で成功する"""
    payload = {
        **_DEFAULT,
        "numTrials": 10,
        "sampleSize": 5,
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    expected_trials = 10
    assert len(response.json()["result"]["betaEstimates"]) == expected_trials


# ---------------------------------------------------------------------------
# バリデーションエラーケース
# ---------------------------------------------------------------------------


def test_unbiasedness_num_trials_too_small(client):
    """numTrials < 10 で 422"""
    payload = {**_DEFAULT, "numTrials": 5}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_unbiasedness_num_trials_too_large(client):
    """numTrials > 2000 で 422"""
    payload = {**_DEFAULT, "numTrials": 2001}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_unbiasedness_sample_size_too_small(client):
    """sampleSize < 5 で 422"""
    payload = {**_DEFAULT, "sampleSize": 4}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_unbiasedness_error_variance_too_small(client):
    """errorVariance < 0.1 で 422"""
    payload = {**_DEFAULT, "errorVariance": 0.05}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_unbiasedness_true_beta_out_of_range(client):
    """trueBeta < -3 で 422"""
    payload = {**_DEFAULT, "trueBeta": -3.5}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
