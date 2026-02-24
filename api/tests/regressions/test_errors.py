"""回帰分析エラー処理テスト（422/400/境界値）"""

import polars as pl
from fastapi import status

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from tests.regressions.conftest import (
    TABLE_BASIC,
    TABLE_NAN,
    TABLE_PANEL,
    TABLE_STRING,
    URL_REGRESSION,
    fe_payload,
    ols_payload,
)

# ─────────────────────────────────────────────
# 日本語テーブル名・カラム名（漢字必須）
# ─────────────────────────────────────────────
_TABLE_KANJI = "売上高集計表"
_COL_KANJI_Y = "費用合計額"
_COL_KANJI_X = "広告宣伝費"
_COL_KANJI_EXISTING = "売上金額"

# 境界値用定数
_SHORT_TABLE = "A"


# ─────────────────────────────────────────────
# 422 バリデーションエラー
# ─────────────────────────────────────────────


class TestValidationError422:
    """Pydantic 422 バリデーションエラーのテスト"""

    def test_missing_table_name(self, client, tables_store):
        """tableName が欠如している場合は 422 を返す"""
        payload = {
            "dependentVariable": "y_linear",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": True,
            "analysis": {"method": "ols"},
            "standardError": {"method": "nonrobust"},
        }
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR
        assert "tableNameは必須項目です。" in data["message"]

    def test_empty_table_name(self, client, tables_store):
        """tableName が空文字の場合は 422 を返す"""
        payload = ols_payload(table="")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR
        assert "tableNameは1文字以上で入力してください。" in data["message"]

    def test_whitespace_only_table_name(self, client, tables_store):
        """tableName が空白のみの場合は 422 を返す（strip後に空文字）"""
        payload = ols_payload(table="   ")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR
        assert "tableNameは1文字以上で入力してください。" in data["message"]

    def test_tab_only_table_name(self, client, tables_store):
        """tableName がタブのみの場合は 422 を返す（strip後に空文字）"""
        payload = ols_payload(table="\t")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR
        assert "tableNameは1文字以上で入力してください。" in data["message"]

    def test_missing_analysis(self, client, tables_store):
        """analysis が欠如している場合は 422 を返す"""
        payload = {
            "tableName": TABLE_BASIC,
            "dependentVariable": "y_linear",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": True,
            "standardError": {"method": "nonrobust"},
        }
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR
        assert "analysisは必須項目です。" in data["message"]

    def test_missing_entity_id_for_fe(self, client, tables_store):
        """固定効果モデルで entityIdColumn が欠如の場合は 422"""
        payload = {
            "tableName": TABLE_PANEL,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "analysis": {"method": "fe"},
            "standardError": {"method": "nonrobust"},
        }
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR
        assert "analysis.fe.entityIdColumnは必須項目です。" in data["message"]

    def test_missing_endogenous_variables_for_iv(self, client, tables_store):
        """IV モデルで endogenousVariables が欠如の場合は 422"""
        payload = {
            "tableName": TABLE_BASIC,
            "dependentVariable": "y_linear",
            "explanatoryVariables": ["x1"],
            "analysis": {
                "method": "iv",
                "endogenousVariables": ["x2"],
            },
            "standardError": {"method": "nonrobust"},
        }
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR

    def test_missing_instrumental_variables_for_iv(self, client, tables_store):
        """IV モデルで instrumentalVariables が欠如の場合は 422"""
        payload = {
            "tableName": TABLE_BASIC,
            "dependentVariable": "y_linear",
            "explanatoryVariables": ["x1"],
            "analysis": {
                "method": "iv",
                "endogenousVariables": ["x2"],
            },
            "standardError": {"method": "nonrobust"},
        }
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert data["code"] == ErrorCode.VALIDATION_ERROR
        assert (
            "analysis.iv.instrumentalVariablesは必須項目です。"
            in data["message"]
        )


# ─────────────────────────────────────────────
# 400 DATA_NOT_FOUND エラー
# ─────────────────────────────────────────────


class TestDataNotFound400:
    """存在しないテーブル・カラム参照の 400 エラーテスト"""

    def test_nonexistent_table(self, client, tables_store):
        """存在しないテーブル名で 400 を返す"""
        payload = ols_payload(table="NonExistentTable")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND
        assert (
            "tableName 'NonExistentTable'は存在しません。" in data["message"]
        )

    def test_nonexistent_dependent_variable(self, client, tables_store):
        """存在しない目的変数で 400 を返す"""
        payload = ols_payload(dep="nonexistent_y")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND
        assert (
            "dependentVariable 'nonexistent_y'は存在しません。"
            in data["message"]
        )

    def test_nonexistent_explanatory_variable(self, client, tables_store):
        """存在しない説明変数で 400 を返す"""
        payload = ols_payload(expl=["nonexistent_x"])
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND
        assert (
            "explanatoryVariables 'nonexistent_x'は存在しません。"
            in data["message"]
        )

    def test_nonexistent_entity_id_column_for_fe(self, client, tables_store):
        """FE モデルで存在しない entityIdColumn を指定した場合は 400"""
        payload = fe_payload(entity_col="nonexistent_entity")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND
        assert "は存在しません。" in data["message"]

    def test_nonexistent_time_column_for_fe(self, client, tables_store):
        """FE モデルで存在しない timeColumn を指定した場合は 400"""
        payload = fe_payload(time_col="nonexistentime")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND
        assert "は存在しません。" in data["message"]

    def test_kanji_table_name_not_found(self, client, tables_store):
        """存在しない漢字テーブル名で 400、エラーメッセージに漢字を含む"""
        payload = ols_payload(table=_TABLE_KANJI)
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND
        assert _TABLE_KANJI in data["message"]
        assert "は存在しません。" in data["message"]

    def test_kanji_column_name_not_found(self, client, tables_store):
        """漢字テーブルに存在しない漢字カラムを指定すると 400"""
        store = TablesStore()
        store.store_table(
            _TABLE_KANJI,
            pl.DataFrame(
                {
                    _COL_KANJI_EXISTING: [
                        100.0,
                        200.0,
                        300.0,
                        400.0,
                        500.0,
                    ],
                    _COL_KANJI_X: [
                        10.0,
                        20.0,
                        30.0,
                        40.0,
                        50.0,
                    ],
                }
            ),
        )
        # テーブルには存在しない _COL_KANJI_Y を目的変数に指定
        payload = ols_payload(
            table=_TABLE_KANJI,
            dep=_COL_KANJI_Y,
            expl=[_COL_KANJI_X],
        )
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND
        assert _COL_KANJI_Y in data["message"]
        assert "は存在しません。" in data["message"]


# ─────────────────────────────────────────────
# 400 INVALID_DTYPE エラー
# ─────────────────────────────────────────────


class TestInvalidDtype400:
    """型不一致の 400 エラーテスト"""

    def test_string_column_as_dependent_variable(self, client, tables_store):
        """文字列カラムを目的変数に指定した場合は 400"""
        payload = ols_payload(
            table=TABLE_STRING,
            dep="name",
            expl=["score"],
        )
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.INVALID_DTYPE
        assert "name" in data["message"]

    def test_string_column_as_explanatory_variable(self, client, tables_store):
        """文字列カラムを説明変数に指定した場合は 400"""
        payload = ols_payload(
            table=TABLE_STRING,
            dep="score",
            expl=["name"],
        )
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.INVALID_DTYPE
        assert "name" in data["message"]


# ─────────────────────────────────────────────
# 境界値テスト
# ─────────────────────────────────────────────


class TestBoundaryValues:
    """境界値・特殊文字テスト"""

    def test_kanji_table_name_is_valid(self, client, tables_store):
        """漢字テーブル名・漢字カラム名で正常に回帰分析を実行できる"""
        store = TablesStore()
        store.store_table(
            _TABLE_KANJI,
            pl.DataFrame(
                {
                    _COL_KANJI_EXISTING: [
                        100.0,
                        200.0,
                        300.0,
                        400.0,
                        500.0,
                        600.0,
                        700.0,
                        800.0,
                        900.0,
                        1000.0,
                    ],
                    _COL_KANJI_X: [
                        10.0,
                        20.0,
                        30.0,
                        40.0,
                        50.0,
                        60.0,
                        70.0,
                        80.0,
                        90.0,
                        100.0,
                    ],
                    _COL_KANJI_Y: [
                        5.0,
                        10.0,
                        15.0,
                        20.0,
                        25.0,
                        30.0,
                        35.0,
                        40.0,
                        45.0,
                        50.0,
                    ],
                }
            ),
        )
        payload = ols_payload(
            table=_TABLE_KANJI,
            dep=_COL_KANJI_EXISTING,
            expl=[_COL_KANJI_X, _COL_KANJI_Y],
        )
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        assert data["code"] == "OK"

    def test_single_char_table_name_is_valid(self, client, tables_store):
        """1 文字のテーブル名は有効（min_length=1）"""
        store = TablesStore()
        store.store_table(
            _SHORT_TABLE,
            pl.DataFrame(
                {
                    "y": [1.0, 2.0, 3.0, 4.0, 5.0],
                    "x": [2.0, 4.0, 6.0, 8.0, 10.0],
                }
            ),
        )
        payload = ols_payload(
            table=_SHORT_TABLE,
            dep="y",
            expl=["x"],
        )
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        assert data["code"] == "OK"

    def test_emoji_table_name_returns_not_found(self, client, tables_store):
        """絵文字含むテーブル名は 422 にならず DATA_NOT_FOUND を返す

        TableName は NAME_PATTERN を持たないため絵文字も通過する。
        登録されていなければ 400 DATA_NOT_FOUND となる。
        """
        payload = ols_payload(table="🎉売上テーブル集計")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert data["code"] == ErrorCode.DATA_NOT_FOUND

    def test_leading_trailing_space_is_stripped(self, client, tables_store):
        """前後スペース付きテーブル名は strip されて正常参照できる"""
        # TABLE_BASIC は既に tables_store で登録済み
        payload = ols_payload(table=f"  {TABLE_BASIC}  ")
        resp = client.post(URL_REGRESSION, json=payload)
        data = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        assert data["code"] == "OK"


# ─────────────────────────────────────────────
# 欠損値処理エラーテスト
# ─────────────────────────────────────────────


class TestMissingValueHandling:
    """欠損値処理モードのテスト"""

    def test_missing_value_error_mode(self, client, tables_store):
        """missingValueHandling='error'の場合、NaNありデータは 500 を返す"""
        payload = {
            "tableName": TABLE_NAN,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": True,
            "missingValueHandling": "error",
            "analysis": {"method": "ols"},
            "standardError": {"method": "nonrobust"},
        }
        resp = client.post(URL_REGRESSION, json=payload)
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_missing_value_remove_mode(self, client, tables_store):
        """missingValueHandling='remove'の場合、NaN行を除去して正常終了する"""
        payload = {
            "tableName": TABLE_NAN,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": True,
            "missingValueHandling": "remove",
            "analysis": {"method": "ols"},
            "standardError": {"method": "nonrobust"},
        }
        resp = client.post(URL_REGRESSION, json=payload)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["code"] == "OK"
