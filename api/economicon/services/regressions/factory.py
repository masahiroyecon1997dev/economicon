"""回帰分析モデルファクトリ

`RegressionParams` の型に基づいて、対応する DataOperation クラスを生成する。
"""

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.entities import (
    FEParams,
    FGLSParams,
    GLSParams,
    InstrumentalVariablesParams,
    LassoParams,
    LogitParams,
    OLSParams,
    PanelIvParams,
    ProbitParams,
    REParams,
    RidgeParams,
    TobitParams,
    WLSParams,
)
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.operation import DataOperation
from economicon.services.regressions.estimators import (
    FERegression,
    FGLSRegression,
    GLSRegression,
    IVRegression,
    LassoRegression,
    LogitRegression,
    OLSRegression,
    PanelIVRegression,
    ProbitRegression,
    RERegression,
    RidgeRegression,
    TobitRegression,
    WLSRegression,
)
from economicon.utils import ProcessingError

# 1:1 マッピング。スキーマ分割により各 Params 型がユニークになっている。
_FACTORY_MAP: dict[type, type] = {
    OLSParams: OLSRegression,
    LassoParams: LassoRegression,
    RidgeParams: RidgeRegression,
    LogitParams: LogitRegression,
    ProbitParams: ProbitRegression,
    InstrumentalVariablesParams: IVRegression,
    FEParams: FERegression,
    REParams: RERegression,
    TobitParams: TobitRegression,
    PanelIvParams: PanelIVRegression,
    WLSParams: WLSRegression,
    GLSParams: GLSRegression,
    FGLSParams: FGLSRegression,
}


def create_regression(
    body: RegressionRequestBody,
    tables_store: TablesStore,
    result_store: AnalysisResultStore,
) -> DataOperation:
    """`body.analysis` の型に対応する回帰モデルオブジェクトを生成する。

    Returns
    -------
    DataOperation Protocol を満たすオブジェクト。
    """
    cls = _FACTORY_MAP.get(type(body.analysis))
    if cls is None:
        raise ProcessingError(
            error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
            message=_("Specified regression method is not supported"),
        )
    return cls(body, tables_store, result_store)
