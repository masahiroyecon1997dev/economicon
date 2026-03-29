"""固定効果 IV (PanelIV) 回帰モデル — 未実装スタブ"""

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.entities import PanelIvParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.estimators._base import _RegressionBase
from economicon.utils import ProcessingError


class PanelIVRegression(_RegressionBase):
    """PanelIV 回帰 DataOperation 実装（未実装）。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: PanelIvParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        pass

    def execute(self) -> dict:
        raise ProcessingError(
            error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
            message=_("Specified regression method is not supported"),
        )
