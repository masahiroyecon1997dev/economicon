"""
統合回帰分析サービス

全ての回帰分析手法を単一のインターフェースで提供します。
services/regressions/ 配下の各分析クラスへのディスパッチャとして機能します。
"""

from typing import Dict, Any, Optional, List

from .regressions import (
    OLSRegression,
    LogitRegression,
    ProbitRegression,
    TobitRegression,
    FixedEffectsRegression,
    RandomEffectsRegression,
    IVRegression,
    LassoRegression,
    RidgeRegression
)
from ..utils.validator.common_validators import ValidationError
from .abstract_api import ApiError


def execute_regression_analysis(
    analysis_type: str,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    standard_error_method: str = 'nonrobust',
    has_const: bool = True,
    missing_value_handling: str = 'remove',
    use_t_distribution: bool = True,
    # Panel data specific
    entity_id_column: Optional[str] = None,
    time_column: Optional[str] = None,
    # IV specific
    instrumental_variables: Optional[List[str]] = None,
    endogenous_variables: Optional[List[str]] = None,
    # Tobit specific
    left_censoring_limit: Optional[float] = None,
    right_censoring_limit: Optional[float] = None,
    # Regularization specific
    alpha: Optional[float] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    統合回帰分析の実行

    Args:
        analysis_type: 分析タイプ (ols, logit, probit, tobit, fe, re, 
                      feiv, iv, lasso, ridge)
        table_name: 対象テーブル名
        dependent_variable: 被説明変数
        explanatory_variables: 説明変数のリスト
        standard_error_method: 標準誤差の計算方法
        has_const: 定数項を含めるか
        missing_value_handling: 欠損値の処理方法
        use_t_distribution: t分布を使用するか
        entity_id_column: 個体ID列名（パネルデータ用）
        time_column: 時間列名（パネルデータ用）
        instrumental_variables: 操作変数のリスト（IV用）
        endogenous_variables: 内生変数のリスト（IV用）
        left_censoring_limit: 左側打ち切り値（Tobit用）
        right_censoring_limit: 右側打ち切り値（Tobit用）
        alpha: 正則化パラメータ（Lasso/Ridge用）
        **kwargs: その他のパラメータ

    Returns:
        分析結果の辞書

    Raises:
        ValidationError: パラメータバリデーションエラー
        ApiError: 分析実行時エラー
    """
    # 共通パラメータ
    common_params = {
        'table_name': table_name,
        'dependent_variable': dependent_variable,
        'explanatory_variables': explanatory_variables,
        'standard_error_method': standard_error_method,
        'missing_value_handling': missing_value_handling,
        'use_t_distribution': use_t_distribution
    }

    # 分析タイプに応じてサービスクラスを選択
    if analysis_type == 'ols':
        api = OLSRegression(**common_params, has_const=has_const)

    elif analysis_type == 'logit':
        api = LogitRegression(**common_params, has_const=has_const)

    elif analysis_type == 'probit':
        api = ProbitRegression(**common_params, has_const=has_const)

    elif analysis_type == 'tobit':
        api = TobitRegression(
            **common_params,
            has_const=has_const,
            left_censoring_limit=left_censoring_limit,
            right_censoring_limit=right_censoring_limit
        )

    elif analysis_type == 'fe':
        if not entity_id_column:
            raise ValidationError(
                "entityIdColumn is required for fixed effects analysis"
            )
        # パネル分析ではhas_constは使用しない
        api = FixedEffectsRegression(
            **common_params,
            entity_id_column=entity_id_column,
            time_column=time_column
        )

    elif analysis_type == 're':
        if not entity_id_column:
            raise ValidationError(
                "entityIdColumn is required for random effects analysis"
            )
        # パネル分析ではhas_constは使用しない
        api = RandomEffectsRegression(
            **common_params,
            entity_id_column=entity_id_column,
            time_column=time_column
        )

    elif analysis_type in ['iv', 'feiv']:
        # feiv: Fixed Effects Instrumental Variables
        if not instrumental_variables:
            raise ValidationError(
                "instrumentalVariables is required for IV analysis"
            )
        
        # feivの場合、entity_id_columnも必要
        if analysis_type == 'feiv':
            if not entity_id_column:
                raise ValidationError(
                    "entityIdColumn is required for fixed effects IV "
                    "analysis"
                )
            # TODO: 将来的にFixed Effects IVクラスを実装
            # 現在はentity_id_columnを説明変数として扱う暫定対応
            raise NotImplementedError(
                "Fixed Effects IV (feiv) is not yet implemented. "
                "Use 'iv' for standard instrumental variables regression."
            )
        
        api = IVRegression(
            **common_params,
            has_const=has_const,
            instrumental_variables=instrumental_variables,
            endogenous_variables=endogenous_variables or []
        )

    elif analysis_type == 'lasso':
        if alpha is None:
            raise ValidationError(
                "alpha is required in hyperParameters for Lasso regression"
            )
        api = LassoRegression(
            **common_params,
            has_const=has_const,
            hyper_parameters={'alpha': alpha}
        )

    elif analysis_type == 'ridge':
        if alpha is None:
            raise ValidationError(
                "alpha is required in hyperParameters for Ridge regression"
            )
        api = RidgeRegression(
            **common_params,
            has_const=has_const,
            hyper_parameters={'alpha': alpha}
        )

    else:
        raise ValidationError(f"Unknown analysis type: {analysis_type}")

    # バリデーション実行
    validation_error = api.validate()
    if validation_error:
        raise validation_error

    # 分析実行
    result = api.execute()
    return result


# 後方互換性のための個別関数（既存コードとの互換性維持）

def linear_regression(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str]
) -> Dict[str, Any]:
    """線形回帰分析（後方互換性用）"""
    return execute_regression_analysis(
        analysis_type='ols',
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables
    )


def logistic_regression(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str]
) -> Dict[str, Any]:
    """ロジスティック回帰分析（後方互換性用）"""
    return execute_regression_analysis(
        analysis_type='logit',
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables
    )


def probit_regression(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str]
) -> Dict[str, Any]:
    """プロビット回帰分析（後方互換性用）"""
    return execute_regression_analysis(
        analysis_type='probit',
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables
    )


def fixed_effects_estimation(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column: str,
    standard_error_method: str = 'clustered',
    use_t_distribution: bool = True
) -> Dict[str, Any]:
    """固定効果推定（後方互換性用）"""
    return execute_regression_analysis(
        analysis_type='fe',
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables,
        entity_id_column=entity_id_column,
        standard_error_method=standard_error_method,
        use_t_distribution=use_t_distribution
    )


def variable_effects_estimation(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column: str,
    standard_error_method: str = 'clustered',
    use_t_distribution: bool = True
) -> Dict[str, Any]:
    """変量効果推定（後方互換性用）"""
    return execute_regression_analysis(
        analysis_type='re',
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables,
        entity_id_column=entity_id_column,
        standard_error_method=standard_error_method,
        use_t_distribution=use_t_distribution
    )
