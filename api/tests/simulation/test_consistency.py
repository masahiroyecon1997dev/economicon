"""POST /api/simulation/consistency エンドポイントのテスト"""

import math

from starlette import status

URL = "/api/simulation/consistency"

# ---------------------------------------------------------------------------
# デフォルトペイロード
# ---------------------------------------------------------------------------

_DEFAULT = {
    "nMax": 100,
    "trueBeta": 1.0,
    "errorVariance": 1.0,
    "endogenous": False,
    "endogeneityStrength": 1.0,
    "xDistribution": {"xMean": 0.0, "xVariance": 1.0},
}


# ---------------------------------------------------------------------------
# 成功ケース
# ---------------------------------------------------------------------------


def test_consistency_exogenous_success(client):
    """endogenous=False でリクエストが成功する"""
    response = client.post(URL, json=_DEFAULT)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"

    result = data["result"]
    assert result["trueBeta"] == _DEFAULT["trueBeta"]
    # 外生性: 確率極限 = trueBeta
    assert result["probabilityLimit"] == _DEFAULT["trueBeta"]


def test_consistency_exogenous_sequence_structure(client):
    """n_values と beta_estimates の長さが一致し n=2 から始まる"""
    response = client.post(URL, json=_DEFAULT)
    result = response.json()["result"]

    n_values = result["nValues"]
    beta_estimates = result["betaEstimates"]

    assert len(n_values) == len(beta_estimates)
    expected_min_n = 2
    assert n_values[0] == expected_min_n
    assert n_values[-1] == _DEFAULT["nMax"]
    # n_values は単調増加
    assert all(n_values[i] < n_values[i + 1] for i in range(len(n_values) - 1))


def test_consistency_endogenous_probability_limit(client):
    """endogenous=True の確率極限は trueBeta + γ/2"""
    gamma = 2.0
    payload = {
        **_DEFAULT,
        "endogenous": True,
        "endogeneityStrength": gamma,
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    expected_plim = _DEFAULT["trueBeta"] + gamma / 2
    assert math.isclose(
        result["probabilityLimit"], expected_plim, rel_tol=1e-9
    )


def test_consistency_endogenous_success(client):
    """endogenous=True で成功する"""
    payload = {**_DEFAULT, "endogenous": True}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_consistency_large_n_max(client):
    """nMax=500 で最後の n_value が 500"""
    payload = {**_DEFAULT, "nMax": 500}
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    expected_max_n = 500
    assert result["nValues"][-1] == expected_max_n


def test_consistency_negative_true_beta(client):
    """trueBeta=-2.0 で確率極限が -2.0 になる（外生性）"""
    payload = {**_DEFAULT, "trueBeta": -2.0}
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK
    expected_true_beta = -2.0
    assert result["trueBeta"] == expected_true_beta
    assert result["probabilityLimit"] == expected_true_beta


# ---------------------------------------------------------------------------
# バリデーションエラーケース
# ---------------------------------------------------------------------------


def test_consistency_n_max_too_small(client):
    """nMax < 50 で 422"""
    payload = {**_DEFAULT, "nMax": 49}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_consistency_n_max_too_large(client):
    """nMax > 5000 で 422"""
    payload = {**_DEFAULT, "nMax": 5001}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_consistency_true_beta_out_of_range(client):
    """trueBeta > 3 で 422"""
    payload = {**_DEFAULT, "trueBeta": 3.5}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_consistency_endogeneity_strength_too_large(client):
    """endogeneityStrength > 3.0 で 422"""
    payload = {**_DEFAULT, "endogeneityStrength": 3.1}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
