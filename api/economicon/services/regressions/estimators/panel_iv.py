"""固定効果 IV (PanelIV / FE-2SLS) 回帰モデル"""

from economicon.core.enums import ErrorCode
from economicon.schemas.regression_params import PanelIvParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import (
    PanelIvDataConfig,
    prepare_panel_iv_dataframe,
)
from economicon.services.regressions.estimators._base import _RegressionBase
from economicon.services.regressions.fitters import PanelIVInput, fit_panel_iv
from economicon.services.regressions.formatters import format_panel_iv_result
from economicon.services.regressions.validators import (
    validate_base_params,
    validate_panel_iv_columns,
)
from economicon.utils import ProcessingError


class PanelIVRegression(_RegressionBase):
    """固定効果IV回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: PanelIvParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        column_name_list, df_schema = validate_base_params(
            self.table_name,
            self.dependent_variable,
            self.explanatory_variables,
            self.tables_store,
        )
        validate_panel_iv_columns(self.analysis, column_name_list, df_schema)

    def execute(self) -> dict:
        try:
            df = self.tables_store.get_table(self.table_name).table
            panel_iv_config = PanelIvDataConfig(
                dependent_variable=self.dependent_variable,
                explanatory_variables=self.explanatory_variables,
                endogenous_variables=self.analysis.endogenous_variables,
                instrumental_variables=self.analysis.instrumental_variables,
                entity_id_column=self.analysis.entity_id_column,
                time_column=self.analysis.time_column,
                missing=self.missing,
            )
            df_pandas = prepare_panel_iv_dataframe(df, panel_iv_config)
            data_input = PanelIVInput(
                df_pandas=df_pandas,
                dependent_variable=self.dependent_variable,
                explanatory_variables=self.explanatory_variables,
                endogenous_variables=self.analysis.endogenous_variables,
                instrumental_variables=self.analysis.instrumental_variables,
                entity_id_column=self.analysis.entity_id_column,
                standard_error_method=self.standard_error.method,
                time_column=self.analysis.time_column,
            )
            model_result = fit_panel_iv(data_input)
            y = df_pandas[self.dependent_variable]
            regression_output = format_panel_iv_result(
                model_result,
                y,
                self.table_name,
                self.dependent_variable,
                self.explanatory_variables,
                self.analysis.endogenous_variables,
                self.analysis.instrumental_variables,
                self.analysis.entity_id_column,
            )
            result_id = self._save_result(
                regression_output,
                model_result,
                "feiv",
                entity_id_column=self.analysis.entity_id_column,
                time_column=self.analysis.time_column,
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e
