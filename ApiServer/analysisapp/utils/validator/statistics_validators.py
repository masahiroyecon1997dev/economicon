from typing import Any, Dict, List

import polars as pl

from ...i18n.translation import gettext as _
from .common_validators import (
    ValidationError,
    validate_candidates,
    validate_column_is_numeric,
    validate_integer,
    validate_item_exists_in_list,
    validate_item_in_dict,
    validate_list_length,
    validate_number,
    validate_required,
)
from .tables_store_validator import validate_existed_column_name
from .validation_config import SUPPORTED_DISTRIBUTIONS


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
    """分布ごとのパラメータを検証"""

    match distribution_type:
        case "uniform":
            if "low" not in params or "high" not in params:
                raise ValidationError(
                    _(
                        "Uniform distribution requires "
                        "'low' and 'high' parameters"
                    )
                )
            validate_number(params["low"], "low")
            validate_number(params["high"], "high")
            if params["low"] >= params["high"]:
                raise ValidationError(
                    _(
                        "For uniform distribution, "
                        "'low' must be less than 'high'"
                    )
                )
        case "exponential":
            if "scale" not in params:
                raise ValidationError(
                    _("Exponential distribution requires 'scale' parameter")
                )
            validate_number(params["scale"], "scale")
            if params["scale"] <= 0:
                raise ValidationError(
                    _("For exponential distribution, 'scale' must be positive")
                )
        case "normal":
            if "loc" not in params or "scale" not in params:
                raise ValidationError(
                    _(
                        "Normal distribution requires "
                        "'loc' and 'scale' parameters"
                    )
                )
            validate_number(params["loc"], "loc")
            validate_number(params["scale"], "scale")
            if params["scale"] <= 0:
                raise ValidationError(
                    _("For normal distribution, 'scale' must be positive")
                )
        case "gamma":
            if "shape" not in params or "scale" not in params:
                raise ValidationError(
                    _(
                        "Gamma distribution requires "
                        "'shape' and 'scale' parameters"
                    )
                )
            validate_number(params["shape"], "shape")
            validate_number(params["scale"], "scale")
            if params["shape"] <= 0 or params["scale"] <= 0:
                raise ValidationError(
                    _(
                        "For gamma distribution, "
                        "'shape' and 'scale' must be "
                        "positive"
                    )
                )
        case "beta":
            if "a" not in params or "b" not in params:
                raise ValidationError(
                    _("Beta distribution requires 'a' and 'b' parameters")
                )
            validate_number(params["a"], "a")
            validate_number(params["b"], "b")
            if params["a"] <= 0 or params["b"] <= 0:
                raise ValidationError(
                    _("For beta distribution, 'a' and 'b' must be positive")
                )
        case "weibull":
            if "a" not in params or "scale" not in params:
                raise ValidationError(
                    _(
                        "Weibull distribution requires 'a' "
                        "and 'scale' parameters"
                    )
                )
            validate_number(params["a"], "a")
            if params["a"] <= 0:
                raise ValidationError(
                    _("For weibull distribution, 'a' must be positive")
                )
            validate_number(params["scale"], "scale")
            if params["scale"] > 0:
                raise ValidationError(
                    _("For weibull distribution, 'scale' must be positive")
                )
        case "lognormal":
            if "mean" not in params or "sigma" not in params:
                raise ValidationError(
                    _(
                        "Lognormal distribution requires "
                        "'mean' and 'sigma' parameters"
                    )
                )
            validate_number(params["mean"], "mean")
            validate_number(params["sigma"], "sigma")
            if params["sigma"] <= 0:
                raise ValidationError(
                    _("For lognormal distribution, 'sigma' must be positive")
                )
        case "binomial":
            if "n" not in params or "p" not in params:
                raise ValidationError(
                    _("Binomial distribution requires 'n' and 'p' parameters")
                )
            validate_integer(params["n"], "n")
            validate_number(params["p"], "p")
            if params["n"] <= 0:
                raise ValidationError(
                    _("For binomial distribution, 'n' must be positive")
                )
            if not (0 <= params["p"] <= 1):
                raise ValidationError(
                    _("For binomial distribution, 'p' must be between 0 and 1")
                )
        case "bernoulli":
            if "p" not in params:
                raise ValidationError(
                    _("Bernoulli distribution requires 'p' parameter")
                )
            validate_number(params["p"], "p")
            if not (0 <= params["p"] <= 1):
                raise ValidationError(
                    _(
                        "For bernoulli distribution, "
                        "'p' must be between 0 and 1"
                    )
                )
        case "poisson":
            if "lam" not in params:
                raise ValidationError(
                    _("Poisson distribution requires 'lam' parameter")
                )
            validate_number(params["lam"], "lam")
            if params["lam"] <= 0:
                raise ValidationError(
                    _("For poisson distribution, 'lam' must be positive")
                )
        case "geometric":
            if "p" not in params:
                raise ValidationError(
                    _("Geometric distribution requires 'p' parameter")
                )
            validate_number(params["p"], "p")
            if not (0 < params["p"] <= 1):
                raise ValidationError(
                    _(
                        "For geometric distribution, "
                        "'p' must be between 0 and 1 "
                        "(exclusive of 0)"
                    )
                )
        case "hypergeometric":
            if "N" not in params or "K" not in params or "n" not in params:
                raise ValidationError(
                    _(
                        "Hypergeometric distribution requires "
                        "'N', 'K', and 'n' parameters"
                    )
                )
            validate_integer(params["N"], "N")
            validate_integer(params["K"], "K")
            validate_integer(params["n"], "n")
            if params["N"] <= 0 or params["K"] <= 0 or params["n"] <= 0:
                raise ValidationError(
                    _(
                        "For hypergeometric "
                        "distribution, 'N', 'K', "
                        "and 'n' must be positive"
                    )
                )
            if params["K"] > params["N"]:
                raise ValidationError(
                    _(
                        "For hypergeometric "
                        "distribution, 'K' "
                        "must not exceed 'N'"
                    )
                )
            if params["n"] > params["N"]:
                raise ValidationError(
                    _(
                        "For hypergeometric "
                        "distribution, 'n' "
                        "must not exceed 'N'"
                    )
                )


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
