from typing import List

import polars as pl
from django.utils.translation import gettext as _

from .common_validators import (ValidationError, validate_candidates,
                                validate_column_is_numeric, validate_integer,
                                validate_item_exists_in_list,
                                validate_list_length, validate_number,
                                validate_required)
from .validation_config import SUPPORTED_DISTRIBUTIONS


def validate_distribution_type(
    distribution_type: str,
    distribution_type_param: str
) -> None:
    validate_required(distribution_type, distribution_type_param)
    validate_candidates(
        distribution_type,
        distribution_type_param,
        SUPPORTED_DISTRIBUTIONS,
    )


def validate_distribution_params(
    distribution_type: str,
    params: dict
) -> None:
    """分布ごとのパラメータを検証"""

    match distribution_type:
        case 'uniform':
            if 'low' not in params or 'high' not in params:
                raise ValidationError("Uniform distribution requires "
                                      "'low' and 'high' parameters")
            validate_number(params['low'], 'low')
            validate_number(params['high'], 'high')
            if params['low'] >= params['high']:
                raise ValidationError("For uniform distribution, "
                                      "'low' must be less than 'high'")
        case 'exponential':
            if 'scale' not in params:
                raise ValidationError("Exponential distribution requires "
                                      "'scale' parameter")
            validate_number(params['scale'], 'scale')
            if params['scale'] <= 0:
                raise ValidationError("For exponential distribution, "
                                      "'scale' must be positive")
        case 'normal':
            if 'loc' not in params or 'scale' not in params:
                raise ValidationError("Normal distribution requires "
                                      "'loc' and 'scale' parameters")
            validate_number(params['loc'], 'loc')
            validate_number(params['scale'], 'scale')
            if params['scale'] <= 0:
                raise ValidationError("For normal distribution, "
                                      "'scale' must be positive")
        case 'gamma':
            if 'shape' not in params or 'scale' not in params:
                raise ValidationError("Gamma distribution requires "
                                      "'shape' and 'scale' parameters")
            validate_number(params['shape'], 'shape')
            validate_number(params['scale'], 'scale')
            if params['shape'] <= 0 or params['scale'] <= 0:
                raise ValidationError("For gamma distribution, "
                                      "'shape' and 'scale' must be "
                                      "positive")
        case 'beta':
            if 'a' not in params or 'b' not in params:
                raise ValidationError("Beta distribution requires "
                                      "'a' and 'b' parameters")
            validate_number(params['a'], 'a')
            validate_number(params['b'], 'b')
            if params['a'] <= 0 or params['b'] <= 0:
                raise ValidationError("For beta distribution, "
                                      "'a' and 'b' must be positive")
        case 'weibull':
            if 'a' not in params or 'scale' not in params:
                raise ValidationError("Weibull distribution requires 'a' "
                                      "and 'scale' parameters")
            validate_number(params['a'], 'a')
            if params['a'] <= 0:
                raise ValidationError("For weibull distribution, "
                                      "'a' must be positive")
            validate_number(params['scale'], 'scale')
            if params['scale'] > 0:
                raise ValidationError("For weibull distribution, "
                                      "'scale' must be positive")
        case 'lognormal':
            if 'mean' not in params or 'sigma' not in params:
                raise ValidationError("Lognormal distribution requires "
                                      "'mean' and 'sigma' parameters")
            validate_number(params['mean'], 'mean')
            validate_number(params['sigma'], 'sigma')
            if params['sigma'] <= 0:
                raise ValidationError("For lognormal distribution, "
                                      "'sigma' must be positive")
        case 'binomial':
            if 'n' not in params or 'p' not in params:
                raise ValidationError("Binomial distribution requires "
                                      "'n' and 'p' parameters")
            validate_integer(params['n'], 'n')
            validate_number(params['p'], 'p')
            if params['n'] <= 0:
                raise ValidationError("For binomial distribution, "
                                      "'n' must be positive")
            if not (0 <= params['p'] <= 1):
                raise ValidationError("For binomial distribution, "
                                      "'p' must be between 0 and 1")
        case 'bernoulli':
            if 'p' not in params:
                raise ValidationError("Bernoulli distribution requires "
                                      "'p' parameter")
            validate_number(params['p'], 'p')
            if not (0 <= params['p'] <= 1):
                raise ValidationError("For bernoulli distribution, "
                                      "'p' must be between 0 and 1")
        case 'poisson':
            if 'lam' not in params:
                raise ValidationError("Poisson distribution requires "
                                      "'lam' parameter")
            validate_number(params['lam'], 'lam')
            if params['lam'] <= 0:
                raise ValidationError("For poisson distribution, "
                                      "'lam' must be positive")
        case 'geometric':
            if 'p' not in params:
                raise ValidationError("Geometric distribution requires "
                                      "'p' parameter")
            validate_number(params['p'], 'p')
            if not (0 < params['p'] <= 1):
                raise ValidationError("For geometric distribution, "
                                      "'p' must be between 0 and 1 "
                                      "(exclusive of 0)")
        case 'hypergeometric':
            if 'N' not in params or 'K' not in params or 'n' not in params:
                raise ValidationError("Hypergeometric distribution requires "
                                      "'N', 'K', and 'n' parameters")
            validate_integer(params['N'], 'N')
            validate_integer(params['K'], 'K')
            validate_integer(params['n'], 'n')
            if params['N'] <= 0 or params['K'] <= 0 or params['n'] <= 0:
                raise ValidationError("For hypergeometric "
                                      "distribution, 'N', 'K', "
                                      "and 'n' must be positive")
            if params['K'] > params['N']:
                raise ValidationError("For hypergeometric "
                                      "distribution, 'K' "
                                      "must not exceed 'N'")
            if params['n'] > params['N']:
                raise ValidationError("For hypergeometric "
                                      "distribution, 'n' "
                                      "must not exceed 'N'")


def validate_explanatory_variables(
    explanatory_variables: List[str],
    column_name_list: List[str],
    df_schema: pl.Schema,
    explanatory_variables_param: str
) -> None:
    least_num_explanatory_variables = 1
    validate_list_length(explanatory_variables,
                         least_num_explanatory_variables,
                         explanatory_variables_param,
                         'explanatory_variable')
    for col_name in explanatory_variables:
        validate_required(col_name, explanatory_variables_param)
        validate_item_exists_in_list(col_name,
                                     explanatory_variables_param,
                                     column_name_list)
        # 型チェックのために取得
        column_type = df_schema.items().mapping[col_name]
        validate_column_is_numeric(col_name,
                                   explanatory_variables_param,
                                   column_type)


def validate_dependent_variable(
    dependent_variable: str,
    column_name_list: List[str],
    explanatory_variables: List[str],
    df_schema: pl.Schema,
    explanatory_variables_param: str
) -> None:
    validate_required(dependent_variable, explanatory_variables_param)
    validate_item_exists_in_list(dependent_variable,
                                 explanatory_variables_param,
                                 column_name_list)
    # 型チェックのために取得
    column_type = df_schema.items().mapping[dependent_variable]
    validate_column_is_numeric(dependent_variable,
                               explanatory_variables_param,
                               column_type)
    # 被説明変数が説明変数に含まれていないかチェック
    if dependent_variable in explanatory_variables:
        raise ValidationError(_("Dependent variable cannot be "
                                "included in explanatory variables"))
