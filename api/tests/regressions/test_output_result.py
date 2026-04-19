"""分析結果フォーマット出力テスト。"""

import re

from fastapi import status

from economicon.schemas.results import RegressionOutputRequest
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.results.output_result import OutputResult
from tests.regressions.conftest import (
    URL_REGRESSION,
    FePayload,
    IvPayload,
    LassoPayload,
    LogitPayload,
    OlsPayload,
)

URL_OUTPUT = "/api/analysis/results/output"
URL_DS = "/api/statistics/descriptive"
URL_CI = "/api/statistics/confidence-interval"
URL_TEST = "/api/statistics/test"

_MISSING_ID_1 = "non-existent-id"
_MISSING_ID_2 = "another-missing-id"
_DUMMY_ID = "dummy-id"
_EXPECTED_MISSING_MSG = (
    f"The following analysis results do not exist: {_MISSING_ID_1}"
)


def _run_regression(client, payload) -> str:
    """任意のペイロードで回帰推定を実行して result_id を返す。"""
    resp = client.post(URL_REGRESSION, json=payload.build())
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["result"]["resultId"]


def _run_ols(client, tables_store) -> str:
    """OLS 推定を実行して result_id を返す。"""
    return _run_regression(client, OlsPayload())


def _output_payload(
    result_ids: list[str],
    *,
    result_type: str = "regression",
    format: str = "text",
    options: dict | None = None,
) -> dict:
    """新しい output API リクエストを生成する。"""
    payload = {
        "resultType": result_type,
        "resultIds": result_ids,
        "format": format,
    }
    if options is not None:
        payload["options"] = options
    return payload


def _save_analysis_result(
    *,
    name: str,
    table_name: str,
    result_type: str,
    result_data: dict,
) -> str:
    """AnalysisResultStore にテスト用結果を保存する。"""
    result = AnalysisResult(
        name=name,
        description="",
        table_name=table_name,
        result_type=result_type,
        result_data=result_data,
    )
    return AnalysisResultStore().save_result(result)


def _create_descriptive_result() -> str:
    return _save_analysis_result(
        name="desc #1",
        table_name="desc_table",
        result_type="descriptive_statistics",
        result_data={
            "tableName": "desc_table",
            "statistics": {
                "A": {"mean": 3.0, "median": 3.0, "count": 5},
                "B": {"mean": 30.0, "median": 30.0, "count": 5},
            },
        },
    )


def _create_confidence_interval_result() -> str:
    return _save_analysis_result(
        name="ci #1",
        table_name="ci_table",
        result_type="confidence_interval",
        result_data={
            "tableName": "ci_table",
            "columnName": "x",
            "statistic": {"type": "mean", "value": 12.34},
            "confidenceInterval": {"lower": 10.0, "upper": 14.68},
            "confidenceLevel": 0.95,
        },
    )


def _create_statistical_test_result() -> str:
    return _save_analysis_result(
        name="t-test #1",
        table_name="test_table",
        result_type="statistical_test",
        result_data={
            "statistic": 2.3456,
            "pValue": 0.021,
            "df": 48.0,
            "confidenceInterval": {"lower": 0.11, "upper": 1.23},
            "confidenceLevel": 0.95,
            "effectSize": 0.44,
        },
    )


def test_output_result_text_success(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([result_id]),
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert data["result"]["format"] == "text"


def test_output_result_markdown_success(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([result_id], format="markdown"),
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "| Variable |" in resp.json()["result"]["content"]


def test_output_result_latex_success(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([result_id], format="latex"),
    )
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert r"\begin{table}" in content
    assert r"\end{table}" in content


def test_output_result_contains_variables(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(URL_OUTPUT, json=_output_payload([result_id]))
    content = resp.json()["result"]["content"]
    assert "x1" in content
    assert "x2" in content
    assert "const" in content


def test_output_result_multiple_models(client, tables_store):
    id1 = _run_ols(client, tables_store)
    id2 = _run_ols(client, tables_store)
    resp = client.post(URL_OUTPUT, json=_output_payload([id1, id2]))
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert "(1)" in content
    assert "(2)" in content


def test_output_result_regression_options_applied(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            options={
                "constAtBottom": False,
                "variableOrder": ["x2", "x1"],
                "variableLabels": {"x1": "Income", "x2": "Education"},
            },
        ),
    )
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert content.index("const") < content.index("Education")
    assert content.index("Education") < content.index("Income")


def test_output_result_iv_first_stage_f_present(client, tables_store):
    result_id = _run_regression(client, IvPayload())
    resp = client.post(URL_OUTPUT, json=_output_payload([result_id]))
    assert resp.status_code == status.HTTP_200_OK
    assert "1st-F:" in resp.json()["result"]["content"]


def test_output_result_fe_r2_within_present(client, tables_store):
    result_id = _run_regression(client, FePayload())
    resp = client.post(URL_OUTPUT, json=_output_payload([result_id]))
    assert "R\u00b2 (within)" in resp.json()["result"]["content"]


def test_output_result_logit_pseudo_r2_present(client, tables_store):
    result_id = _run_regression(client, LogitPayload())
    resp = client.post(URL_OUTPUT, json=_output_payload([result_id]))
    assert "Pseudo R" in resp.json()["result"]["content"]


def test_output_result_lasso_paren_shows_placeholder(client, tables_store):
    result_id = _run_regression(client, LassoPayload())
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            options={"statInParentheses": "se"},
        ),
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "---" in resp.json()["result"]["content"]


def test_output_result_custom_significance_stars_applied(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            options={
                "significanceStars": [{"threshold": 0.05, "symbol": "+"}],
            },
        ),
    )
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert "+" in content
    assert "***" not in content


def test_output_result_stat_none_no_parentheses(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            options={"statInParentheses": "none"},
        ),
    )
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert not re.search(r"\(\d+\.\d+\)", content)


def test_output_result_latex_stars_superscript_format(client, tables_store):
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([result_id], format="latex"),
    )
    assert "$^{" in resp.json()["result"]["content"]


def test_output_result_idempotent(client, tables_store):
    result_id = _run_ols(client, tables_store)
    payload = _output_payload([result_id])
    r1 = client.post(URL_OUTPUT, json=payload).json()
    r2 = client.post(URL_OUTPUT, json=payload).json()
    assert r1["code"] == r2["code"]
    assert r1["result"]["content"] == r2["result"]["content"]


def test_output_result_execute_without_validate_uses_fallback(
    client, tables_store
):
    result_id = _run_ols(client, tables_store)
    req = RegressionOutputRequest(
        result_ids=[result_id],
        format="text",
    )
    svc = OutputResult(req, AnalysisResultStore())
    assert svc._fetched is None
    result = svc.execute()
    assert result["format"] == "text"
    assert len(result["content"]) > 0


def test_output_result_descriptive_statistics_markdown_success(
    client, tables_store
):
    result_id = _create_descriptive_result()
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            result_type="descriptive_statistics",
            format="markdown",
            options={
                "statisticOrder": ["count", "mean", "median"],
                "variableLabels": {"A": "Income"},
            },
        ),
    )
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert "| Result | Table | Variable | count | mean | median |" in content
    assert "Income" in content


def test_output_result_confidence_interval_text_success(client, tables_store):
    result_id = _create_confidence_interval_result()
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            result_type="confidence_interval",
            options={"includeTableName": False},
        ),
    )
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert "Column" in content
    assert "Estimate" in content
    assert "ci_table" not in content


def test_output_result_statistical_test_text_success(client, tables_store):
    result_id = _create_statistical_test_result()
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            result_type="statistical_test",
            options={"includeTableName": False},
        ),
    )
    content = resp.json()["result"]["content"]
    assert resp.status_code == status.HTTP_200_OK
    assert "p-value" in content
    assert "Effect Size" in content
    assert "test_table" not in content


def test_output_result_mixed_result_types_returns_400(client, tables_store):
    regression_id = _run_ols(client, tables_store)
    ci_id = _create_confidence_interval_result()
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([regression_id, ci_id]),
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["code"] == "VALIDATION_ERROR"


def test_output_result_requested_type_mismatch_returns_400(
    client, tables_store
):
    result_id = _create_descriptive_result()
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload(
            [result_id],
            result_type="confidence_interval",
        ),
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["code"] == "VALIDATION_ERROR"


def test_output_result_invalid_id_returns_400(client, tables_store):
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([_MISSING_ID_1]),
    )
    data = resp.json()
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert data["code"] == "DATA_NOT_FOUND"
    assert _MISSING_ID_1 in data["message"]


def test_output_result_error_message_exact_match(client, tables_store):
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([_MISSING_ID_1]),
    )
    assert _EXPECTED_MISSING_MSG == resp.json()["message"]


def test_output_result_multiple_missing_ids_comma_separated(
    client, tables_store
):
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([_MISSING_ID_1, _MISSING_ID_2]),
    )
    msg = resp.json()["message"]
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert _MISSING_ID_1 in msg
    assert _MISSING_ID_2 in msg


def test_output_result_empty_ids_returns_422(client, tables_store):
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([]),
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_output_result_invalid_format_returns_422(client, tables_store):
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([_DUMMY_ID], format="excel"),
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_output_result_missing_result_type_returns_422(client, tables_store):
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [_DUMMY_ID], "format": "text"},
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_output_result_422_detail_has_loc_and_msg(client, tables_store):
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([]),
    )
    data = resp.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert isinstance(data["details"], list)
    assert len(data["details"]) > 0


def test_output_result_422_no_info_leak(client, tables_store):
    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([]),
    )
    body = resp.text
    assert "Traceback" not in body
    assert "password" not in body.lower()
    assert "api_key" not in body.lower()
    assert "c:\\" not in body.lower()
    assert "/home/" not in body


def test_output_result_500_on_malformed_regression_output(
    client, tables_store
):
    bad = AnalysisResult(
        name="malformed",
        description="test",
        table_name="dummy",
        result_data={"parameters": []},
        result_type="regression",
    )
    AnalysisResultStore().save_result(bad)

    resp = client.post(
        URL_OUTPUT,
        json=_output_payload([bad.id]),
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert resp.json()["code"] == "OUTPUT_RESULT_ERROR"
