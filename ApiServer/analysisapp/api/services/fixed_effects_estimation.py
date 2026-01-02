from typing import Dict, List

import numpy as np
import polars as pl
import statsmodels.api as sm
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import (ValidationError,
                                                     validate_candidates)
from ..utils.validator.statistics_validators import (
    validate_dependent_variable, validate_explanatory_variables)
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name)
from .abstract_api import AbstractApi, ApiError

# 讓呎ｺ冶ｪ､蟾ｮ險育ｮ玲婿豕輔・蛟呵｣・STANDARD_ERROR_METHODS = ['normal', 'clustered', 'robust', 'hac']


class FixedEffectsEstimation(AbstractApi):
    """
    蛟倶ｽ灘・蛛丞ｷｮ繧貞茜逕ｨ縺励◆蝗ｺ螳壼柑譫懈耳螳壹ｒ陦後≧縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ蛻励ｒ菴ｿ逕ｨ縺励※蝗ｺ螳壼柑譫懷・譫舌ｒ螳溯｡後＠縺ｾ縺吶・    陲ｫ隱ｬ譏主､画焚・亥ｾ灘ｱ槫､画焚・・蛻励→隱ｬ譏主､画焚・育峡遶句､画焚・芽､・焚蛻励∝倶ｽ的D蛻励ｒ謖・ｮ壹＠縺ｾ縺吶・    蛟倶ｽ灘・蛛丞ｷｮ・亥倶ｽ灘・縺ｮ蟷ｳ蝮・°繧峨・荵夜屬・峨ｒ蛻ｩ逕ｨ縺励◆譁ｹ豕輔〒謗ｨ螳壹ｒ陦後＞縺ｾ縺吶・    """
    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        entity_id_column: str,
        standard_error_method: str = 'normal',
        use_t_distribution: bool = True
    ):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.dependent_variable = dependent_variable
        self.explanatory_variables = explanatory_variables
        self.entity_id_column = entity_id_column
        self.standard_error_method = standard_error_method
        self.use_t_distribution = use_t_distribution
        self.param_names = {
            'table_name': 'tableName',
            'dependent_variable': 'dependentVariable',
            'explanatory_variables': 'explanatoryVariables',
            'entity_id_column': 'entityIdColumn',
            'standard_error_method': 'standardErrorMethod',
            'use_t_distribution': 'useTDistribution'
        }

    def validate(self):
        try:
            # 繝・・繝悶Ν蜷阪・讀懆ｨｼ
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 蛻怜錐繝ｪ繧ｹ繝医・蜿門ｾ・            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)

            # 隱ｬ譏主､画焚縺ｮ讀懆ｨｼ
            df_schema = self.tables_manager.get_column_info_list(
                self.table_name)
            validate_explanatory_variables(
                self.explanatory_variables,
                column_name_list,
                df_schema,
                self.param_names['explanatory_variables']
            )

            # 陲ｫ隱ｬ譏主､画焚縺ｮ讀懆ｨｼ
            validate_dependent_variable(
                self.dependent_variable,
                column_name_list,
                self.explanatory_variables,
                df_schema,
                self.param_names['dependent_variable']
            )

            # 蛟倶ｽ的D蛻励・讀懆ｨｼ
            validate_existed_column_name(
                self.entity_id_column,
                column_name_list,
                self.param_names['entity_id_column']
            )

            # 蛟倶ｽ的D蛻励′隱ｬ譏主､画焚繧・｢ｫ隱ｬ譏主､画焚縺ｨ驥崎､・＠縺ｦ縺・↑縺・°繝√ぉ繝・け
            if self.entity_id_column == self.dependent_variable:
                raise ValidationError(
                    _("Entity ID column cannot be the same as "
                      "dependent variable")
                )
            if self.entity_id_column in self.explanatory_variables:
                raise ValidationError(
                    _("Entity ID column cannot be included in "
                      "explanatory variables")
                )

            # 讓呎ｺ冶ｪ､蟾ｮ險育ｮ玲婿豕輔・讀懆ｨｼ
            validate_candidates(
                self.standard_error_method,
                self.param_names['standard_error_method'],
                STANDARD_ERROR_METHODS
            )

            return None
        except ValidationError as e:
            return e

    def execute(self) -> Dict:
        try:
            # 繝・・繝悶Ν縺ｮ蜿門ｾ・            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 繝・・繧ｿ縺ｮ貅門ｙ
            all_columns = [self.dependent_variable] \
                + self.explanatory_variables + [self.entity_id_column]

            # 蠢・ｦ√↑蛻励・縺ｿ繧帝∈謚槭＠縲∵ｬ謳榊､繧帝勁蜴ｻ
            working_df = df.select(all_columns).drop_nulls()

            if working_df.height == 0:
                message = _("No valid observations after "
                            "removing missing values")
                raise ApiError(message)

            # 蛟倶ｽ的D縺ｧ繧ｰ繝ｫ繝ｼ繝怜喧縺励※蛟倶ｽ灘・蛛丞ｷｮ繧定ｨ育ｮ・            # 蜷・倶ｽ薙・隕ｳ貂ｬ謨ｰ繧偵メ繧ｧ繝・け・亥崋螳壼柑譫懊・縺溘ａ縺ｫ縺ｯ隍・焚縺ｮ譎らせ縺悟ｿ・ｦ・ｼ・            entity_counts = working_df.group_by(self.entity_id_column).agg(
                pl.count().alias("n_obs")
            )
            valid_entities = entity_counts.filter(pl.col("n_obs") > 1)

            if valid_entities.height == 0:
                message = _("No entities with multiple observations found. "
                            "Fixed effects requires multiple time periods "
                            "per entity.")
                raise ApiError(message)

            # 譛牙柑縺ｪ蛟倶ｽ薙・縺ｿ繧剃ｿ晄戟
            valid_entity_ids = valid_entities.select(
                self.entity_id_column).to_series().to_list()
            working_df = working_df.filter(pl.col(
                self.entity_id_column).is_in(valid_entity_ids))

            # 蛟倶ｽ灘・蟷ｳ蝮・ｒ險育ｮ・            group_means = working_df.group_by(self.entity_id_column).agg([
                pl.mean(col).alias(f"{col}_mean")
                for col in (
                    [self.dependent_variable] + self.explanatory_variables)
            ])

            # 蜈・・繝・・繧ｿ縺ｨ蛟倶ｽ灘・蟷ｳ蝮・ｒ繝槭・繧ｸ
            working_df = working_df.join(group_means, on=self.entity_id_column)

            # 蛟倶ｽ灘・蛛丞ｷｮ繧定ｨ育ｮ暦ｼ・ithin-group demeaning・・            y_demeaned = working_df.select(
                (pl.col(self.dependent_variable) - pl.col(
                    f"{self.dependent_variable}_mean")).alias("y_demeaned")
            ).to_series().to_numpy()

            x_demeaned_list = []
            for var in self.explanatory_variables:
                x_demeaned = working_df.select(
                    (pl.col(var) - pl.col(f"{var}_mean")).alias(
                        f"{var}_demeaned")
                ).to_series().to_numpy()
                x_demeaned_list.append(x_demeaned)

            x_demeaned = np.column_stack(x_demeaned_list)

            # 蝗ｺ螳壼柑譫懷屓蟶ｰ縺ｮ螳溯｡鯉ｼ亥ｮ壽焚鬆・・荳崎ｦ√∝倶ｽ灘・蛛丞ｷｮ縺ｫ繧医ｊ髯､蜴ｻ縺輔ｌ繧具ｼ・            model = sm.OLS(y_demeaned, x_demeaned).fit()

            # 讓呎ｺ冶ｪ､蟾ｮ縺ｮ隱ｿ謨ｴ
            if self.standard_error_method == 'robust':
                model = model.get_robustcov_results(cov_type='HC0')
            elif self.standard_error_method == 'clustered':
                # 繧ｯ繝ｩ繧ｹ繧ｿ繝ｼ讓呎ｺ冶ｪ､蟾ｮ・亥倶ｽ薙〒繧ｯ繝ｩ繧ｹ繧ｿ繝ｼ・・                entity_ids = working_df.select(
                    self.entity_id_column).to_series().to_numpy()
                model = model.get_robustcov_results(cov_type='cluster',
                                                    groups=entity_ids)
            elif self.standard_error_method == 'hac':
                # HAC讓呎ｺ冶ｪ､蟾ｮ・・ewey-West・・                model = model.get_robustcov_results(cov_type='HAC', maxlags=1)

            # t邨ｱ險磯㍼縺ｾ縺溘・z邨ｱ險磯㍼縺ｮ驕ｸ謚・            if self.use_t_distribution:
                p_values = model.pvalues
                t_values = model.tvalues
            else:
                # 豁｣隕丞・蟶・ｒ菴ｿ逕ｨ
                from scipy import stats
                t_values = model.params / model.bse
                p_values = 2 * (1 - stats.norm.cdf(np.abs(t_values)))

            # 邨先棡縺ｮ謨ｴ逅・            summary_text = model.summary().as_text()

            # 繝代Λ繝｡繝ｼ繧ｿ縺ｮ隧ｳ邏ｰ諠・ｱ
            params_info = []
            for i, name in enumerate(self.explanatory_variables):
                params_info.append({
                    'variable': name,
                    'coefficient': float(model.params[i]),
                    'standardError': float(model.bse[i]),
                    'pValue': float(p_values[i]),
                    'tValue': float(t_values[i])
                })

            # 繝｢繝・Ν邨ｱ險域ュ蝣ｱ
            n_entities = len(valid_entity_ids)
            n_obs = int(working_df.height)
            df_resid = n_obs - len(
                self.explanatory_variables) - n_entities + 1  # 蝗ｺ螳壼柑譫懊ｒ閠・・

            model_stats = {
                'R2': float(model.rsquared),
                'adjustedR2': float(model.rsquared_adj),
                'fValue': float(model.fvalue) if hasattr(
                    model, 'fvalue') else None,
                'fProbability': float(
                    model.f_pvalue) if hasattr(model, 'f_pvalue') else None,
                'nObservations': n_obs,
                'nEntities': n_entities,
                'degreesOfFreedom': df_resid,
                'standardErrorMethod': self.standard_error_method,
                'useTDistribution': self.use_t_distribution
            }

            # 邨先棡繧定ｿ斐☆
            result = {
                'tableName': self.table_name,
                'dependentVariable': self.dependent_variable,
                'explanatoryVariables': self.explanatory_variables,
                'entityIdColumn': self.entity_id_column,
                'estimationMethod': 'fixed_effects_within_group_demeaning',
                'regressionResult': summary_text,
                'parameters': params_info,
                'modelStatistics': model_stats
            }
            return result

        except ApiError:
            # Re-raise ApiError so it can be handled by the REST layer
            raise
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "fixed effects estimation processing")
            raise ApiError(message) from e


def fixed_effects_estimation(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column: str,
    standard_error_method: str = 'normal',
    use_t_distribution: bool = True
) -> Dict:
    """
    蛟倶ｽ灘・蛛丞ｷｮ繧貞茜逕ｨ縺励◆蝗ｺ螳壼柑譫懈耳螳壹ｒ螳溯｡後☆繧矩未謨ｰ

    Args:
        table_name: 繝・・繝悶Ν蜷・        dependent_variable: 陲ｫ隱ｬ譏主､画焚縺ｮ蛻怜錐
        explanatory_variables: 隱ｬ譏主､画焚縺ｮ蛻怜錐繝ｪ繧ｹ繝・        entity_id_column: 蛟倶ｽ的D蛻怜錐
        standard_error_method: 讓呎ｺ冶ｪ､蟾ｮ縺ｮ險育ｮ玲婿豕・                               ('normal', 'clustered', 'robust', 'hac')
        use_t_distribution: t蛻・ｸ・ｒ菴ｿ逕ｨ縺吶ｋ縺九←縺・°

    Returns:
        蝗ｺ螳壼柑譫懷・譫千ｵ先棡繧貞性繧霎樊嶌
    """
    api = FixedEffectsEstimation(
        table_name,
        dependent_variable,
        explanatory_variables,
        entity_id_column,
        standard_error_method,
        use_t_distribution
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
