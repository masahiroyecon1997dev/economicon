"""
差の差（DID）分析サービス

DataOperation プロトコル実装。
現在は未実装（NotImplementedError を送出）。

推定方針（実装時の参考）
-----------------------
1. 基本 DID（TWFE）:
   y_it = α + β*(D_i × P_t) + Σγ_k*X_kit + μ_i + τ_t + ε_it
   → linearmodels.PanelOLS(entity_effects=True, time_effects=True)

2. Event Study:
   y_it = α + Σ_{k≠base} δ_k*(D_i × 1[t=k])
          + Σγ_k*X_kit + μ_i + τ_t + ε_it
   → 各相対期間ダミーを Polars で生成し PanelOLS に渡す

3. 標準誤差:
   クラスタ SE（個体レベル）を推奨。
   linearmodels: cov_type='clustered', cluster_entity=True

4. 並行トレンド検定:
   処置前係数（k < 0, k ≠ base_period）の Wald 検定。
   linearmodels: model.wald_test(restrictions, formula=None)
"""

from economicon.schemas.did import DIDRequestBody
from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ValidationError
from economicon.utils.validators import (
    validate_existence,
    validate_numeric_types,
)

_PARAM_NAMES: dict[str, str] = {
    "table_name": "tableName",
    "dependent_variable": "dependentVariable",
    "explanatory_variables": "explanatoryVariables",
    "treatment_column": "treatmentColumn",
    "post_column": "postColumn",
    "time_column": "timeColumn",
    "entity_id_column": "entityIdColumn",
}


class DIDAnalysis:
    """
    DID 分析 DataOperation 実装（validate / execute）。

    Parameters
    ----------
    body : DIDRequestBody
        リクエストボディ
    tables_store : TablesStore
        テーブルストア
    result_store : AnalysisResultStore
        分析結果ストア
    """

    def __init__(
        self,
        body: DIDRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        self.tables_store = tables_store
        self.result_store = result_store
        self.table_name = body.table_name
        self.result_name = body.result_name
        self.description = body.description
        self.dependent_variable = body.dependent_variable
        self.explanatory_variables = body.explanatory_variables
        self.treatment_column = body.treatment_column
        self.post_column = body.post_column
        self.time_column = body.time_column
        self.entity_id_column = body.entity_id_column
        self.include_event_study = body.include_event_study
        self.base_period = body.base_period
        self.max_pre_periods = body.max_pre_periods
        self.max_post_periods = body.max_post_periods
        self.missing_value_handling = body.missing_value_handling
        self.standard_error = body.standard_error
        self.confidence_level = body.confidence_level

    def validate(self) -> None:
        """
        入力バリデーション。

        チェック項目:
        - テーブル存在確認
        - 全指定列の存在確認
        - 被説明変数・処置/処置後ダミー列の数値型確認
        - explanatory_variables と treatment/post/entity_id/time 列の重複禁止
        """
        # テーブル存在確認
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

        # 全列の存在確認
        # --- 被説明変数 ---
        validate_existence(
            value=self.dependent_variable,
            valid_list=column_name_list,
            target=_PARAM_NAMES["dependent_variable"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=[self.dependent_variable],
            target=_PARAM_NAMES["dependent_variable"],
        )

        # --- 共変量 ---
        if self.explanatory_variables:
            validate_existence(
                value=self.explanatory_variables,
                valid_list=column_name_list,
                target=_PARAM_NAMES["explanatory_variables"],
            )
            validate_numeric_types(
                schema=df_schema,
                columns=self.explanatory_variables,
                target=_PARAM_NAMES["explanatory_variables"],
            )

        # --- treatment / post 列 ---
        for col, param in [
            (self.treatment_column, "treatment_column"),
            (self.post_column, "post_column"),
        ]:
            validate_existence(
                value=col,
                valid_list=column_name_list,
                target=_PARAM_NAMES[param],
            )
            validate_numeric_types(
                schema=df_schema,
                columns=[col],
                target=_PARAM_NAMES[param],
            )

        # --- time / entity_id 列 ---
        validate_existence(
            value=self.time_column,
            valid_list=column_name_list,
            target=_PARAM_NAMES["time_column"],
        )
        validate_existence(
            value=self.entity_id_column,
            valid_list=column_name_list,
            target=_PARAM_NAMES["entity_id_column"],
        )

        # --- 重複チェック ---
        # explanatory_variables が treatment/post/entity_id/time と被らないこと
        reserved_cols = {
            self.treatment_column,
            self.post_column,
            self.entity_id_column,
            self.time_column,
        }
        overlap = reserved_cols & set(self.explanatory_variables)
        if overlap:
            raise ValidationError(
                error_code="DUPLICATE_COLUMN",
                message=(
                    "explanatoryVariables に treatmentColumn /"
                    " postColumn / entityIdColumn / timeColumn"
                    " と重複する列が含まれています: "
                    f"{sorted(overlap)}"
                ),
            )

    def execute(self) -> dict:
        """
        DID 推定を実行して結果 ID を返す。

        現在は未実装。linearmodels.PanelOLS を使用した TWFE 推定を実装予定。
        """
        raise NotImplementedError
