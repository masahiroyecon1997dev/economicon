from typing import Any, Dict, List

import polars as pl

from ...i18n.translation import gettext as _
from .common import (
    ValidationError,
    validate_column_is_numeric,
    validate_item_exists_in_list,
)
from .tables_store import validate_existed_column_name


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
