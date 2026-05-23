"""POST /api/simulation/asymptotic-normality エンドポイントのテスト"""

import math

from starlette import status

URL = "/api/simulation/asymptotic-normality"

# ---------------------------------------------------------------------------
# デフォルトペイロード
# ---------------------------------------------------------------------------

_DEFAULT = {
    "sampleSize": 30,
    "numSimulations": 200,
    "trueBeta": 1.0,
    "errorVariance": 1.0,
    "errorType": "normal",
    "endogeneityStrength": 1.0,
    "xDistribution": {"xMean": 0.0, "xVariance": 1.0},
}


# ---------------------------------------------------------------------------
# 成功ケース（errorType 別）
# ---------------------------------------------------------------------------


def test_asymptotic_normality_normal_success(client):
    """errorType=normal で成功し漸近正規性が成立する"""
    response = client.post(URL, json=_DEFAULT)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"

    result = data["result"]
    assert result["trueBeta"] == _DEFAULT["trueBeta"]
    assert result["isAsymptoticallyNormal"] is True
    assert isinstance(result["asymptoticMean"], float)
    assert isinstance(result["asymptoticVariance"], float)
    assert result["asymptoticVariance"] > 0.0
    assert len(result["betaEstimates"]) == _DEFAULT["numSimulations"]


def test_asymptotic_normality_normal_asymptotic_mean(client):
    """errorType=normal の漸近平均が trueBeta に一致する"""
    response = client.post(URL, json=_DEFAULT)
    result = response.json()["result"]

    # 漸近平均は OLS の不偏性から trueBeta に等しい
    assert result["asymptoticMean"] == _DEFAULT["trueBeta"]


def test_asymptotic_normality_cauchy_no_clt(client):
    """errorType=cauchy では CLT が成立しない"""
    payload = {**_DEFAULT, "errorType": "cauchy"}
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isAsymptoticallyNormal"] is False
    assert result["asymptoticMean"] is None
    assert result["asymptoticVariance"] is None
    assert len(result["betaEstimates"]) == _DEFAULT["numSimulations"]


def test_asymptotic_normality_endogenous_biased(client):
    """errorType=endogenous では確率極限が trueBeta + γ/2 になる"""
    gamma = 2.0
    payload = {
        **_DEFAULT,
        "errorType": "endogenous",
        "endogeneityStrength": gamma,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    assert result["isAsymptoticallyNormal"] is True
    expected_mean = _DEFAULT["trueBeta"] + gamma / 2
    assert math.isclose(result["asymptoticMean"], expected_mean, rel_tol=1e-9)


def test_asymptotic_normality_custom_x_distribution(client):
    """xDistribution を指定して成功する"""
    payload = {
        **_DEFAULT,
        "xDistribution": {"xMean": 2.0, "xVariance": 2.0},
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_asymptotic_normality_beta_estimates_are_finite(client):
    """errorType=normal の β̂ はすべて有限値"""
    response = client.post(URL, json=_DEFAULT)
    estimates = response.json()["result"]["betaEstimates"]

    assert all(math.isfinite(v) for v in estimates)


# ---------------------------------------------------------------------------
# バリデーションエラーケース
# ---------------------------------------------------------------------------


def test_asymptotic_normality_invalid_sample_size(client):
    """sampleSize が Literal 外 (e.g. 15) で 422"""
    payload = {**_DEFAULT, "sampleSize": 15}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_asymptotic_normality_invalid_error_type(client):
    """不正な errorType で 422"""
    payload = {**_DEFAULT, "errorType": "uniform"}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_asymptotic_normality_num_simulations_too_small(client):
    """numSimulations < 10 で 422"""
    payload = {**_DEFAULT, "numSimulations": 5}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_asymptotic_normality_endogeneity_strength_too_small(client):
    """endogeneityStrength < 0.1 で 422"""
    payload = {**_DEFAULT, "endogeneityStrength": 0.05}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_asymptotic_normality_x_variance_too_small(client):
    """xDistribution.xVariance < 0.1 で 422"""
    payload = {
        **_DEFAULT,
        "xDistribution": {"xMean": 0.0, "xVariance": 0.05},
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
