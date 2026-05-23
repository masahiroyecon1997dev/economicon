"""POST /api/simulation/confidence-interval エンドポイントのテスト"""

from starlette import status

URL = "/api/simulation/confidence-interval"

# ---------------------------------------------------------------------------
# デフォルトペイロード
# ---------------------------------------------------------------------------

_DEFAULT = {
    "ciType": "mean",
    "trials": 50,
    "sampleSize": 20,
    "confidenceLevel": 0.95,
    "trueMean": 0.0,
    "trueVariance": 1.0,
}


# ---------------------------------------------------------------------------
# 成功ケース
# ---------------------------------------------------------------------------


def test_confidence_interval_sim_mean_success(client):
    """ciType=mean でリクエストが成功し基本構造を返す"""
    response = client.post(URL, json=_DEFAULT)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"

    result = data["result"]
    assert result["trueValue"] == _DEFAULT["trueMean"]
    assert result["confidenceLevel"] == _DEFAULT["confidenceLevel"]
    assert len(result["intervals"]) == _DEFAULT["trials"]


def test_confidence_interval_sim_variance_success(client):
    """ciType=variance でリクエストが成功し基本構造を返す"""
    payload = {**_DEFAULT, "ciType": "variance"}
    response = client.post(URL, json=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["code"] == "OK"

    result = data["result"]
    assert result["trueValue"] == _DEFAULT["trueVariance"]
    assert len(result["intervals"]) == _DEFAULT["trials"]


def test_confidence_interval_sim_interval_structure(client):
    """各区間に lower, upper, containsTrue が含まれ lower <= upper"""
    response = client.post(URL, json=_DEFAULT)
    intervals = response.json()["result"]["intervals"]

    for iv in intervals:
        assert "lower" in iv
        assert "upper" in iv
        assert "containsTrue" in iv
        assert isinstance(iv["containsTrue"], bool)
        assert iv["lower"] <= iv["upper"]


def test_confidence_interval_sim_level_90_success(client):
    """confidenceLevel=0.9 で成功する"""
    payload = {**_DEFAULT, "confidenceLevel": 0.9}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    expected_level = 0.9
    assert response.json()["result"]["confidenceLevel"] == expected_level


def test_confidence_interval_sim_level_99_success(client):
    """confidenceLevel=0.99 で成功する"""
    payload = {**_DEFAULT, "confidenceLevel": 0.99}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    expected_level = 0.99
    assert response.json()["result"]["confidenceLevel"] == expected_level


def test_confidence_interval_sim_max_trials(client):
    """trials=2000 で intervals が 2000 件返る"""
    payload = {**_DEFAULT, "trials": 2000}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    expected_trials = 2000
    assert len(response.json()["result"]["intervals"]) == expected_trials


# ---------------------------------------------------------------------------
# バリデーションエラーケース
# ---------------------------------------------------------------------------


def test_confidence_interval_sim_invalid_ci_type(client):
    """不正な ciType で 422"""
    payload = {**_DEFAULT, "ciType": "median"}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_confidence_interval_sim_invalid_confidence_level(client):
    """非許可の confidenceLevel (0.8) で 422"""
    payload = {**_DEFAULT, "confidenceLevel": 0.8}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_confidence_interval_sim_trials_too_small(client):
    """trials < 10 で 422"""
    payload = {**_DEFAULT, "trials": 5}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_confidence_interval_sim_trials_too_large(client):
    """trials > 2000 で 422"""
    payload = {**_DEFAULT, "trials": 2001}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_confidence_interval_sim_sample_size_too_small(client):
    """sampleSize < 5 で 422"""
    payload = {**_DEFAULT, "sampleSize": 4}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_confidence_interval_sim_true_variance_out_of_range(client):
    """trueVariance < 0.01 で 422"""
    payload = {**_DEFAULT, "trueVariance": 0.001}
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
