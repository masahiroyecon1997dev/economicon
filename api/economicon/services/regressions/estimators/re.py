"""変量効果 (RE) パネル回帰モデル"""

from economicon.core.enums import ErrorCode
from economicon.schemas.regression_params import REParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import (
    PanelDataConfig,
    prepare_panel_dataframe,
)
from economicon.services.regressions.estimators._base import _RegressionBase
from economicon.services.regressions.fitters import fit_re
from economicon.services.regressions.formatters import format_re_result
from economicon.services.regressions.validators import (
    validate_base_params,
    validate_panel_columns,
)
from economicon.utils import ProcessingError


class RERegression(_RegressionBase):
    """変量効果パネル回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: REParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        column_name_list, df_schema = validate_base_params(
            self.table_name,
            self.dependent_variable,
            self.explanatory_variables,
            self.tables_store,
        )
        validate_panel_columns(self.analysis, column_name_list, df_schema)

    def execute(self) -> dict:
        try:
            df = self.tables_store.get_table(self.table_name).table
            panel_data_config = PanelDataConfig(
                dependent_variable=self.dependent_variable,
                explanatory_variables=self.explanatory_variables,
                entity_id_column=self.analysis.entity_id_column,
                time_column=self.analysis.time_column,
                missing=self.missing,
            )
            df_pandas = prepare_panel_dataframe(df, panel_data_config)
            model_result = fit_re(
                df_pandas,
                self.dependent_variable,
                self.explanatory_variables,
                self.standard_error.method,
            )
            regression_output = format_re_result(
                model_result,
                self.table_name,
                self.dependent_variable,
                self.explanatory_variables,
                self.analysis.entity_id_column,
            )
            result_id = self._save_result(
                regression_output,
                model_result,
                "re",
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
