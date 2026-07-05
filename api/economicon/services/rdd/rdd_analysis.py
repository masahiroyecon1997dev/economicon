"""
回帰不連続デザイン（RDD）分析サービス

DataOperation プロトコル実装。

推定方針
---------
1. シャープ RDD:
   処置割り当て D = 1[X >= c] のカットオフ c における
   結果変数 Y の不連続の大きさ（LATE）を推定する。
   → rdrobust による局所多項式回帰（kernel 加重）

2. 推定値:
   conventional（局所 p 次）/ bias-corrected（p+1 次補正）の両方を返す。
   フロントエンド表示では bias-corrected + robust CI を推奨。

3. 診断:
   - McCrary 密度検定: 実行変数の密度不連続を rddensity で検定
   - プラシーボ検定: 偽境界値での RDD 推定で識別戦略を検証

4. 可視化データ:
   - bins_data: Polars による等幅ビン集計（散布図用）
   - poly_fit_data: カーネル加重局所多項式フィット曲線（100 グリッド点）
"""

from __future__ import annotations

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.rdd import RDDRequestBody
from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.data.tables_store import TablesStore

# NOTE: fitters のうち rdrobust/rddensity 依存シンボルは GPL のため削除済み。
# compute_bins_data, compute_poly_fit_data は残存するが execute() は
# NotImplementedError を送出するため現在は未使用。
from economicon.utils import ValidationError
from economicon.utils.validators import (
    validate_existence,
    validate_numeric_types,
)

_PARAM_NAMES: dict[str, str] = {
    "table_name": "tableName",
    "outcome_variable": "outcomeVariable",
    "running_variable": "runningVariable",
}

# RDD 推定に必要な最低サンプル数（片側）
_MIN_OBS_PER_SIDE = 10


class RDDAnalysis:
    """
    RDD 分析 DataOperation 実装（validate / execute）。

    Parameters
    ----------
    body : RDDRequestBody
        リクエストボディ
    tables_store : TablesStore
        テーブルストア
    result_store : AnalysisResultStore
        分析結果ストア
    """

    def __init__(
        self,
        body: RDDRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        self.tables_store = tables_store
        self.result_store = result_store
        self.table_name = body.table_name
        self.result_name = body.result_name
        self.description = body.description
        self.outcome_variable = body.outcome_variable
        self.running_variable = body.running_variable
        self.cutoff = body.cutoff
        self.kernel = body.kernel.value
        self.bw_select = body.bw_select.value
        self.h = body.h
        self.p = body.p
        self.vce = body.vce.value
        self.confidence_level = body.confidence_level
        self.n_bins = body.n_bins
        self.placebo_cutoffs = body.placebo_cutoffs

    def validate(self) -> None:
        """
        入力バリデーション。

        チェック項目:
        - テーブル存在確認
        - 結果変数・実行変数の存在確認
        - 結果変数・実行変数の数値型確認
        - 結果変数と実行変数の重複禁止
        - カットオフ両側の最低サンプル数確認
        """
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=_PARAM_NAMES["table_name"],
        )

        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        df_schema = self.tables_store.get_schema(self.table_name)

        # 結果変数の存在・数値型確認
        validate_existence(
            value=self.outcome_variable,
            valid_list=column_name_list,
            target=_PARAM_NAMES["outcome_variable"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=[self.outcome_variable],
            target=_PARAM_NAMES["outcome_variable"],
        )

        # 実行変数の存在・数値型確認
        validate_existence(
            value=self.running_variable,
            valid_list=column_name_list,
            target=_PARAM_NAMES["running_variable"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=[self.running_variable],
            target=_PARAM_NAMES["running_variable"],
        )

        # カットオフ両側のサンプル数確認
        df = self.tables_store.get_table(self.table_name).table
        x_col = df[self.running_variable].drop_nulls()
        n_left = int((x_col < self.cutoff).sum())
        n_right = int((x_col >= self.cutoff).sum())

        if n_left < _MIN_OBS_PER_SIDE:
            raise ValidationError(
                error_code=ErrorCode.RDD_INSUFFICIENT_OBSERVATIONS,
                message=_(
                    "Insufficient observations to the left of cutoff:"
                    " {} (minimum: {})."
                ).format(n_left, _MIN_OBS_PER_SIDE),
                target=_PARAM_NAMES["running_variable"],
            )

        if n_right < _MIN_OBS_PER_SIDE:
            raise ValidationError(
                error_code=ErrorCode.RDD_INSUFFICIENT_OBSERVATIONS,
                message=_(
                    "Insufficient observations to the right of cutoff:"
                    " {} (minimum: {})."
                ).format(n_right, _MIN_OBS_PER_SIDE),
                target=_PARAM_NAMES["running_variable"],
            )

    def execute(self) -> dict:
        """
        RDD 推定・診断・可視化データ生成を実行する。

        Returns
        -------
        dict
            {"resultId": str}

        Raises
        ------
        ProcessingError
            rdrobust 実行失敗・収束エラー等
        NOTE: rdrobust は GPL のため削除済み。NotImplementedError を送出。
        """
        # NOTE: rdrobust / rddensity は GPL ライセンスのため削除済み。
        # ルーター側で NotImplementedError を送出するため、このメソッドは
        # 到達しないが、静的解析エラーを避けるために raise しておく。
        raise NotImplementedError()
