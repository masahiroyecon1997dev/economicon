from typing import Any, Dict, List

import polars as pl
from pydantic import ValidationError as PydanticValidationError

from ...i18n.translation import gettext as _
from ...models.common import (
    BernoulliParams,
    BetaParams,
    BinomialParams,
    ExponentialParams,
    GammaParams,
    GeometricParams,
    HypergeometricParams,
    LognormalParams,
    NormalParams,
    PoissonParams,
    UniformParams,
    WeibullParams,
)
from ...models.types import DistributionType
from .common import (
    ValidationError,
    validate_candidates,
    validate_column_is_numeric,
    validate_item_exists_in_list,
    validate_item_in_dict,
    validate_list_length,
    validate_required,
)
from .tables_store import validate_existed_column_name

SUPPORTED_DISTRIBUTIONS = [dist.value for dist in DistributionType]


def validate_distribution_type(
    distribution_type: str, distribution_type_param: str
) -> None:
    validate_required(distribution_type, distribution_type_param)
    validate_candidates(
        distribution_type,
        distribution_type_param,
        SUPPORTED_DISTRIBUTIONS,
    )


def validate_distribution_params(distribution_type: str, params: dict) -> None:
    """分布ごとのパラメータを検証（Pydanticモデルを使用）"""
    validate_distribution_type(distribution_type, "distributionType")

    if not isinstance(params, dict):
        raise ValidationError(_("distributionParams must be an object"))

    model_by_distribution = {
        "uniform": UniformParams,
        "exponential": ExponentialParams,
        "normal": NormalParams,
        "gamma": GammaParams,
        "beta": BetaParams,
        "weibull": WeibullParams,
        "lognormal": LognormalParams,
        "binomial": BinomialParams,
        "bernoulli": BernoulliParams,
        "poisson": PoissonParams,
        "geometric": GeometricParams,
        "hypergeometric": HypergeometricParams,
    }

    model_class = model_by_distribution[distribution_type]
    input_params = {"type": distribution_type, **params}

    try:
        # Pydanticモデルの基本バリデーション
        model = model_class.model_validate(input_params)

        # 個別の分布パラメータチェック
        if distribution_type == "uniform":
            if model.low >= model.high:
                raise ValidationError(
                    _(
                        "For uniform distribution, 'low' must be less than 'high'"
                    )
                )
        elif distribution_type == "exponential":
            if model.scale <= 0:
                raise ValidationError(
                    _("For exponential distribution, 'scale' must be positive")
                )
        elif distribution_type == "normal":
            if model.scale <= 0:
                raise ValidationError(
                    _("For normal distribution, 'scale' must be positive")
                )
        elif distribution_type == "gamma":
            if model.shape <= 0 or model.scale <= 0:
                raise ValidationError(
                    _(
                        "For gamma distribution, 'shape' and 'scale' must be positive"
                    )
                )
        elif distribution_type == "beta":
            if model.a <= 0 or model.b <= 0:
                raise ValidationError(
                    _("For beta distribution, 'a' and 'b' must be positive")
                )
        elif distribution_type == "weibull":
            if model.a <= 0:
                raise ValidationError(
                    _("For weibull distribution, 'a' must be positive")
                )
            if model.scale <= 0:
                raise ValidationError(
                    _("For weibull distribution, 'scale' must be positive")
                )
        elif distribution_type == "lognormal":
            if model.sigma <= 0:
                raise ValidationError(
                    _("For lognormal distribution, 'sigma' must be positive")
                )
        elif distribution_type == "binomial":
            if model.n <= 0:
                raise ValidationError(
                    _("For binomial distribution, 'n' must be positive")
                )
            if not 0 <= model.p <= 1:
                raise ValidationError(
                    _("For binomial distribution, 'p' must be between 0 and 1")
                )
        elif distribution_type == "bernoulli":
            if not 0 <= model.p <= 1:
                raise ValidationError(
                    _(
                        "For bernoulli distribution, 'p' must be between 0 and 1"
                    )
                )
        elif distribution_type == "poisson":
            if model.lam <= 0:
                raise ValidationError(
                    _("For poisson distribution, 'lam' must be positive")
                )
        elif distribution_type == "geometric":
            if not 0 < model.p <= 1:
                raise ValidationError(
                    _(
                        "For geometric distribution, 'p' must be between 0 and 1 (exclusive of 0)"
                    )
                )
        elif distribution_type == "hypergeometric":
            if model.N <= 0 or model.K <= 0 or model.n <= 0:
                raise ValidationError(
                    _(
                        "For hypergeometric distribution, 'N', 'K', and 'n' must be positive"
                    )
                )
            if model.K > model.N:
                raise ValidationError(
                    _(
                        "For hypergeometric distribution, 'K' must not exceed 'N'"
                    )
                )
            if model.n > model.N:
                raise ValidationError(
                    _(
                        "For hypergeometric distribution, 'n' must not exceed 'N'"
                    )
                )
    except PydanticValidationError as e:
        errors = e.errors()
        if errors:
            message = str(
                errors[0].get("msg", _("Invalid distributionParams"))
            )
        else:
            message = _("Invalid distributionParams")
        raise ValidationError(message) from e


def validate_explanatory_variables(
    explanatory_variables: List[str],
    column_name_list: List[str],
    df_schema: pl.Schema,
    explanatory_variables_param: str,
) -> None:
    least_num_explanatory_variables = 1
    validate_list_length(
        explanatory_variables,
        least_num_explanatory_variables,
        explanatory_variables_param,
        "explanatory_variable",
    )
    for col_name in explanatory_variables:
        validate_required(col_name, explanatory_variables_param)

        # "const"は定数項として予約されているため使用不可
        if col_name == "const":
            raise ValidationError(
                _(
                    '"const" is a reserved column name and cannot be used as an explanatory variable'
                )
            )

        validate_item_exists_in_list(
            col_name, explanatory_variables_param, column_name_list
        )
        # 型チェックのために取得
        column_type = df_schema.items().mapping[col_name]
        validate_column_is_numeric(
            col_name, explanatory_variables_param, column_type
        )


def validate_dependent_variable(
    dependent_variable: str,
    column_name_list: List[str],
    explanatory_variables: List[str],
    df_schema: pl.Schema,
    dependent_variable_param: str,
) -> None:
    validate_required(dependent_variable, dependent_variable_param)

    # "const"は定数項として予約されているため使用不可
    if dependent_variable == "const":
        raise ValidationError(
            _(
                '"const" is a reserved column name and cannot be used as a dependent variable'
            )
        )

    validate_item_exists_in_list(
        dependent_variable, dependent_variable_param, column_name_list
    )
    # 型チェックのために取得
    column_type = df_schema.items().mapping[dependent_variable]
    validate_column_is_numeric(
        dependent_variable, dependent_variable_param, column_type
    )
    # 被説明変数が説明変数に含まれていないかチェック
    if dependent_variable in explanatory_variables:
        raise ValidationError(
            _("Dependent variable cannot be included in explanatory variables")
        )


def validate_standard_error_method(
    standard_error_method: str,
    standard_error_params: Dict[str, Any],
    column_name_list: List[str],
) -> None:
    # 標準誤差方法の検証
    if standard_error_method == "clustered":
        if "groups" not in standard_error_params:
            message = _(
                "standardErrorParams requires 'groups' (cluster variable name)"
            )
            raise ValidationError(message)

        # クラスタ変数が存在するか確認
        groups_col = standard_error_params["groups"]
        if groups_col not in column_name_list:
            message = _("{} is not an existing column name").format(groups_col)
            raise ValidationError(message)


def validate_instrumental_variables(
    instrumental_variables: List[str],
    column_name_list: List[str],
    dependent_variable: str,
    explanatory_variables: List[str],
    instrumental_variables_param: str,
) -> None:
    # 操作変数の検証
    if not instrumental_variables:
        message = _("At least one instrumental variable is required")
        raise ValidationError(message)
    # 列の存在検証
    for iv in instrumental_variables:
        validate_existed_column_name(
            iv, column_name_list, instrumental_variables_param
        )
    # 操作変数が被説明変数と重複していないかチェック
    if dependent_variable in instrumental_variables:
        raise ValidationError(
            _("Instrumental variables cannot include the dependent variable")
        )
    # 操作変数が説明変数と重複していないかチェック
    if any(iv in explanatory_variables for iv in instrumental_variables):
        raise ValidationError(
            _(
                "Instrumental variables cannot include the explanatory variables"
            )
        )


def validate_endogenous_variables(
    endogenous_variables: List[str],
    column_name_list: List[str],
    endogenous_variables_param: str,
) -> None:
    # 内生変数の検証
    for endog in endogenous_variables:
        # "const"は定数項として予約されているため使用不可
        if endog == "const":
            raise ValidationError(
                _(
                    '"const" is a reserved column name and cannot be used as an endogenous variable'
                )
            )
        validate_existed_column_name(
            endog, column_name_list, endogenous_variables_param
        )


def validate_entity_id_column(
    entity_id_column: str,
    column_name_list: List[str],
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column_param: str,
) -> None:
    # 個体ID列の検証
    validate_existed_column_name(
        entity_id_column,
        column_name_list,
        entity_id_column_param,
    )

    # 個体ID列が説明変数や被説明変数と重複していないかチェック
    if entity_id_column == dependent_variable:
        raise ValidationError(
            _("Entity ID column cannot be the same as dependent variable")
        )
    if entity_id_column in explanatory_variables:
        raise ValidationError(
            _("Entity ID column cannot be included in explanatory variables")
        )


def validate_time_column(
    time_column: str,
    column_name_list: List[str],
    dependent_variable: str,
    explanatory_variables: List[str],
    time_column_param: str,
) -> None:
    # 時間列の検証
    if not time_column:
        return
    validate_existed_column_name(
        time_column,
        column_name_list,
        time_column_param,
    )

    # 時間列が説明変数や被説明変数と重複していないかチェック
    if time_column == dependent_variable:
        raise ValidationError(
            _("Time column cannot be the same as dependent variable")
        )
    if time_column in explanatory_variables:
        raise ValidationError(
            _("Time column cannot be included in explanatory variables")
        )


def validate_regulalized_hyperparameters(
    hyper_parameters: Dict[str, Any],
    parameter_name: str,
    regularization_param: str,
) -> None:
    validate_item_in_dict(
        hyper_parameters, parameter_name, regularization_param
    )

    alpha = hyper_parameters.get("alpha")
    if not isinstance(alpha, (int, float)) or alpha < 0:
        message = _("alpha must be a numeric value greater than or equal to 0")
        raise ValidationError(message)
