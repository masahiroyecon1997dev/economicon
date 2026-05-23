"""共通フィールドを保持するベースクラス（内部使用）"""

import logging
from typing import ClassVar

import numpy as np

from economicon.i18n.translation import gettext as _
from economicon.schemas.regressions import RegressionRequestBody
from economicon.schemas.standard_error_settings import StandardErrorSettings
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import MISSING_HANDLING_MAP

_logger = logging.getLogger(__name__)


class _RegressionBase:
    """全回帰モデルに共通するフィールドと結果保存ロジック。

    DataOperation Protocol には直接関与しない内部クラス。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "dependent_variable": "dependentVariable",
        "explanatory_variables": "explanatoryVariables",
        "entity_id_column": "entityIdColumn",
        "time_column": "timeColumn",
        "instrumental_variables": "instrumentalVariables",
        "endogenous_variables": "endogenousVariables",
    }

    def __init__(
        self,
        body: RegressionRequestBody,
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
        self.has_const = body.has_const
        self.missing_value_handling = body.missing_value_handling
        self.standard_error: StandardErrorSettings = body.standard_error
        self.missing: str = MISSING_HANDLING_MAP.get(
            self.missing_value_handling, "drop"
        )

    def _save_result(
        self,
        regression_output: dict,
        raw_model: object,
        model_type: str,
        entity_id_column: str | None = None,
        time_column: str | None = None,
        row_indices: np.ndarray | None = None,
    ) -> str:
        """AnalysisResult を生成・保存し result_id を返す。"""
        if self.result_name:
            name = self.result_name
        else:
            seq = self.result_store.next_sequence("regression")
            name = _("{model_type}: {dependent} #{seq}").format(
                model_type=model_type.upper(),
                dependent=self.dependent_variable,
                seq=seq,
            )
        analysis_result = AnalysisResult(
            name=name,
            description=self.description,
            table_name=self.table_name,
            result_data=regression_output,
            result_type="regression",
            model_type=model_type,
            entity_id_column=entity_id_column,
            time_column=time_column,
            row_indices=row_indices,
        )
        result_id = self.result_store.save_result(analysis_result)

        if raw_model is not None:
            analysis_result.save_model(raw_model)

        return result_id
