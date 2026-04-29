"""
差の差（DID）分析サービス

DataOperation プロトコル実装。

推定方針
---------
1. 基本 DID（TWFE）:
   y_it = α + β*(D_i×P_t) + Σγ_k*X_kit + μ_i + τ_t + ε_it
   → PanelOLS(entity_effects=True, time_effects=True)

2. Event Study:
   y_it = α + Σ_{k≠base} δ_k*(D_i×1[t=k])
          + Σγ_k*X_kit + μ_i + τ_t + ε_it
   → 各時点ダミーを Polars で生成し同 API に渡す

3. 標準誤差:
   クラスタ SE（個体レベル）推奨。
   cluster_entity=True で個体内系列相関に対応。

4. 並行トレンド検定:
   処置前係数 (k < base_period) の Wald F 検定。
"""

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.did import DIDRequestBody
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.data.tables_store import TablesStore
from economicon.services.did.fitters import (
    auto_select_base_period,
    build_interaction_columns,
    compute_pretrend_wald,
    fit_twfe,
    prepare_did_dataframe,
    resolve_cov_kwargs,
    validate_base_period_in_data,
    validate_binary_column,
    validate_panel_uniqueness,
)
from economicon.services.did.formatters import (
    DIDFormatConfig,
    format_did_result,
)
from economicon.services.regressions.common import MISSING_HANDLING_MAP
from economicon.utils import ProcessingError
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
        - Event Study 有効時: time_column の数値型確認
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
        if self.include_event_study:
            validate_numeric_types(
                schema=df_schema,
                columns=[self.time_column],
                target=_PARAM_NAMES["time_column"],
            )
        validate_existence(
            value=self.entity_id_column,
            valid_list=column_name_list,
            target=_PARAM_NAMES["entity_id_column"],
        )

        # base_period が明示指定の場合は、データの時点集合に
        # 存在するかを validate() で確認する。
        # None の場合は auto-select (実行時に確定) のため不要。
        if self.include_event_study and self.base_period is not None:
            df = self.tables_store.get_table(self.table_name).table
            validate_base_period_in_data(
                df, self.time_column, self.base_period
            )

    def execute(self) -> dict:
        """
        TWFE DID 推定を実行して結果 ID を返す。

        実行フロー:
        1. Polars でデータ読み込み
        2. パネルユニーク性の検証
        3. basePeriod の決定（Event Study 時のみ）
        4. 交差項列の生成（Polars）
        5. Pandas MultiIndex DataFrame への変換・欠損値処理
        6. PanelOLS 推定（TWFE）
        7. Event Study: 処置前係数の Wald 検定
        8. 結果フォーマットと AnalysisResultStore への保存

        Returns:
            {"resultId": "<uuid>"}
        """
        try:
            # 1. データ読み込み
            df = self.tables_store.get_table(self.table_name).table

            # 2. パネルユニーク性の検証（欠損値処理前）
            validate_panel_uniqueness(
                df, self.entity_id_column, self.time_column
            )

            # 2b. treatment / post 列の 0/1 バイナリ検証
            validate_binary_column(
                df, self.treatment_column, "treatmentColumn"
            )
            validate_binary_column(df, self.post_column, "postColumn")

            # 3. basePeriod の決定（Event Study のみ使用）
            base_period: int = 0  # 基本 DID では未使用のセンチネル
            if self.include_event_study:
                if self.base_period is None:
                    base_period = auto_select_base_period(
                        df, self.time_column, self.post_column
                    )
                else:
                    base_period = self.base_period

            # 4. 交差項列の生成
            df, interact_col, es_cols = build_interaction_columns(
                df,
                treatment_column=self.treatment_column,
                post_column=self.post_column,
                time_column=self.time_column,
                include_event_study=self.include_event_study,
                base_period=base_period,
            )

            # 5. X 列リストの構築
            if interact_col is not None:
                x_columns = [interact_col] + self.explanatory_variables
            else:
                x_columns = es_cols + self.explanatory_variables

            # 6. 欠損値処理 + Pandas MultiIndex 変換
            missing = MISSING_HANDLING_MAP.get(
                self.missing_value_handling, "drop"
            )
            df_pandas = prepare_did_dataframe(
                df,
                dependent_variable=self.dependent_variable,
                entity_id_column=self.entity_id_column,
                time_column=self.time_column,
                treatment_column=self.treatment_column,
                x_columns=x_columns,
                missing=missing,
            )

            # 7. 標準誤差設定の解決
            cov_type, cov_kwargs = resolve_cov_kwargs(
                self.standard_error,
                self.entity_id_column,
                self.time_column,
            )

            # 8. TWFE 推定
            model_result = fit_twfe(
                df_pandas,
                dependent_variable=self.dependent_variable,
                x_columns=x_columns,
                cov_type=cov_type,
                cov_kwargs=cov_kwargs,
            )

            # 9. 並行トレンド検定（Event Study のみ）
            pre_trend_test: dict | None = None
            if self.include_event_study and es_cols:
                pre_trend_test = compute_pretrend_wald(
                    model_result,
                    es_cols=es_cols,
                    base_period=base_period,
                )

            # 10. 結果フォーマット
            config = DIDFormatConfig(
                table_name=self.table_name,
                dependent_variable=self.dependent_variable,
                treatment_column=self.treatment_column,
                post_column=self.post_column,
                time_column=self.time_column,
                entity_id_column=self.entity_id_column,
                explanatory_variables=self.explanatory_variables,
                confidence_level=self.confidence_level,
                include_event_study=self.include_event_study,
                base_period=base_period,
                interact_col=interact_col,
                es_cols=es_cols,
                pre_trend_test=pre_trend_test,
            )
            result_data = format_did_result(model_result, df_pandas, config)

            # 11. 結果保存
            result_id = self._save_result(result_data)
            return {"resultId": result_id}

        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=_("DID analysis failed: {}").format(str(e)),
            ) from e

    def _save_result(self, result_data: dict) -> str:
        """AnalysisResult を生成・保存し result_id を返す。"""
        if self.result_name:
            name = self.result_name
        else:
            seq = self.result_store.next_sequence("did")
            name = _("DID: {dep} #{seq}").format(
                dep=self.dependent_variable,
                seq=seq,
            )
        ar = AnalysisResult(
            name=name,
            description=self.description,
            table_name=self.table_name,
            result_data=result_data,
            result_type="did",
            model_type="did",
            entity_id_column=self.entity_id_column,
            time_column=self.time_column,
        )
        return self.result_store.save_result(ar)
