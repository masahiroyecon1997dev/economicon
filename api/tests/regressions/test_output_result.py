"""推定結果フォーマット出力テスト (POST /api/analysis/output-result)"""

import re

from fastapi import status

from tests.regressions.conftest import (
    URL_REGRESSION,
    OlsPayload,
)

URL_OUTPUT = "/api/analysis/output-result"


def _run_ols(client, tables_store) -> str:
    """OLS 推定を実行して result_id を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=OlsPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["result"]["resultId"]


# -----------------------------------------------------------
# 正常系
# -----------------------------------------------------------


def test_output_result_text_success(client, tables_store):
    """正常系: text フォーマットで 200 が返る"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "OK" == data["code"]
    result = data["result"]
    assert "content" in result
    assert "format" in result
    assert "text" == result["format"]


def test_output_result_markdown_success(client, tables_store):
    """正常系: markdown フォーマットで 200 が返りテーブルヘッダーを含む"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "markdown"},
    )
    assert resp.status_code == status.HTTP_200_OK
    result = resp.json()["result"]
    assert "markdown" == result["format"]
    assert "| Variable |" in result["content"]


def test_output_result_latex_success(client, tables_store):
    """正常系: latex フォーマットで 200 が返り tabular 環境を含む"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "latex"},
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert r"\begin{table}" in content
    assert r"\end{table}" in content
    assert r"\hline\hline" in content


def test_output_result_contains_variables(client, tables_store):
    """正常系: 出力に説明変数と定数項が含まれる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    content = resp.json()["result"]["content"]
    assert "x1" in content
    assert "x2" in content
    assert "const" in content


def test_output_result_const_at_bottom(client, tables_store):
    """正常系: constAtBottom=True のとき const が x1・x2 より後に現れる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "constAtBottom": True,
        },
    )
    content = resp.json()["result"]["content"]
    assert content.index("x1") < content.index("const")
    assert content.index("x2") < content.index("const")


def test_output_result_variable_labels(client, tables_store):
    """正常系: variableLabels で変数名を置換できる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "variableLabels": {
                "x1": "Income",
                "x2": "Education",
            },
        },
    )
    content = resp.json()["result"]["content"]
    assert "Income" in content
    assert "Education" in content
    # 元の変数名は表示されないこと
    assert "x1" not in content
    assert "x2" not in content


def test_output_result_multiple_models(client, tables_store):
    """正常系: 複数モデルを渡すとモデル番号列が 2 つ生成される"""
    id1 = _run_ols(client, tables_store)
    id2 = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [id1, id2], "format": "text"},
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert "(1)" in content
    assert "(2)" in content


def test_output_result_stat_none_no_parentheses(client, tables_store):
    """正常系: statInParentheses='none' のとき括弧付き数値行が出力されない"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "statInParentheses": "none",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    # "(0.xxxx)" 形式（括弧付き数値）が含まれないこと
    # ヘッダーの "(1)" 等は除外するため数値パターンで検証
    assert not re.search(r"\(\d+\.\d+\)", content), (
        "括弧付き数値行が検出された"
    )


def test_output_result_significance_stars_present(client, tables_store):
    """正常系: デフォルト有意性記号が係数に付与される"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    content = resp.json()["result"]["content"]
    # OLS では通常 p<0.01 の係数が複数存在するため *** が現れる
    assert "***" in content


def test_output_result_model_stats_present(client, tables_store):
    """正常系: N・R² などのモデル統計行が出力に含まれる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    content = resp.json()["result"]["content"]
    assert "N" in content
    # R² のシンボル（UTF-8）または "R2" が含まれること
    assert "R\u00b2" in content or "R2" in content


# -----------------------------------------------------------
# 異常系
# -----------------------------------------------------------


def test_output_result_invalid_id_returns_400(client, tables_store):
    """異常系: 存在しない result_id は 400 を返す"""
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": ["non-existent-id"],
            "format": "text",
        },
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert "DATA_NOT_FOUND" == data["code"]
    assert "non-existent-id" in data["message"]


def test_output_result_empty_ids_returns_422(client, tables_store):
    """異常系: resultIds が空リストは 422 を返す"""
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [], "format": "text"},
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_output_result_invalid_format_returns_422(client, tables_store):
    """異常系: 不正な format 値（excel）は 422 を返す"""
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": ["dummy"], "format": "excel"},
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
