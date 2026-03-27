"""Tobit 回帰モデル"""

import logging

import numpy as np

from economicon.core.enums import ErrorCode
from economicon.schemas.entities import TobitParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import prepare_tobit_dataframe
from economicon.services.regressions.fitters import (
    TobitInput,
    fit_tobit,
    fit_tobit_null,
)
from economicon.services.regressions.formatters import (
    build_tobit_lr_test,
    format_tobit_result,
)
from economicon.services.regressions.models._base import _RegressionBase
from economicon.services.regressions.validators import validate_base_params
from economicon.utils import ProcessingError

_logger = logging.getLogger(__name__)


class TobitRegression(_RegressionBase):
    """Tobit 回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: TobitParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        validate_base_params(
            self.table_name,
            self.dependent_variable,
            self.explanatory_variables,
            self.tables_store,
        )

    def execute(self) -> dict:
        try:
            df = self.tables_store.get_table(self.table_name).table
            df_pandas = prepare_tobit_dataframe(
                df,
                self.dependent_variable,
                self.explanatory_variables,
                self.missing,
            )
            # Critical#3: dropna() 後のインデックスを保存（診断列の行ズレ防止）
            row_indices = df_pandas.index.to_numpy(dtype=np.int64)

            data_input = TobitInput(
                df_pandas=df_pandas,
                dependent_variable=self.dependent_variable,
                explanatory_variables=self.explanatory_variables,
                has_const=self.has_const,
                left_censoring_limit=self.analysis.left_censoring_limit,
                right_censoring_limit=self.analysis.right_censoring_limit,
            )
            model_result = fit_tobit(data_input)

            lr_test_result = None
            try:
                null_result = fit_tobit_null(data_input)
                n_slopes = len(self.explanatory_variables)
                lr_test_result = build_tobit_lr_test(
                    model_result, null_result, n_slopes
                )
            except Exception as _lr_exc:
                # Warning#9: LR 検定失敗をサイレントに無視せずログに記録
                _logger.warning("Tobit LR test failed: %s", _lr_exc)

            regression_output = format_tobit_result(
                model_result,
                self.table_name,
                self.dependent_variable,
                self.explanatory_variables,
                self.has_const,
                self.analysis.left_censoring_limit,
                self.analysis.right_censoring_limit,
                lr_test_result=lr_test_result,
            )
            result_id = self._save_result(
                regression_output,
                model_result,
                "tobit",
                row_indices=row_indices,
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e
