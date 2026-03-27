"""操作変数法 (IV) 回帰モデル"""

from economicon.core.enums import ErrorCode
from economicon.schemas.entities import InstrumentalVariablesParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import (
    IvDataConfig,
    prepare_iv_dataframe,
)
from economicon.services.regressions.fitters import IVInput, fit_iv
from economicon.services.regressions.formatters import format_iv_result
from economicon.services.regressions.models._base import _RegressionBase
from economicon.services.regressions.validators import (
    validate_base_params,
    validate_iv_columns,
)
from economicon.utils import ProcessingError


class IVRegression(_RegressionBase):
    """操作変数法回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: InstrumentalVariablesParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        column_name_list, df_schema = validate_base_params(
            self.table_name,
            self.dependent_variable,
            self.explanatory_variables,
            self.tables_store,
        )
        validate_iv_columns(self.analysis, column_name_list, df_schema)

    def execute(self) -> dict:
        try:
            df = self.tables_store.get_table(self.table_name).table
            iv_data_config = IvDataConfig(
                dependent_variable=self.dependent_variable,
                explanatory_variables=self.explanatory_variables,
                endogenous_variables=self.analysis.endogenous_variables,
                instrumental_variables=self.analysis.instrumental_variables,
                missing=self.missing,
            )
            df_pandas = prepare_iv_dataframe(df, iv_data_config)
            data_input = IVInput(
                df_pandas=df_pandas,
                dependent_variable=self.dependent_variable,
                explanatory_variables=self.explanatory_variables,
                endogenous_variables=self.analysis.endogenous_variables,
                instrumental_variables=self.analysis.instrumental_variables,
                standard_error_method=self.standard_error.method,
                has_const=self.has_const,
                iv_method=self.analysis.iv_method,
                gmm_weight_matrix=self.analysis.gmm_weight_matrix,
            )
            model_result = fit_iv(data_input)
            regression_output = format_iv_result(
                model_result,
                self.table_name,
                self.dependent_variable,
                self.explanatory_variables,
                self.analysis.endogenous_variables,
                self.analysis.instrumental_variables,
                self.has_const,
            )
            result_id = self._save_result(
                regression_output, model_result, "iv"
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e
