"""統計的検定サービス (t-test / z-test / f-test)"""

from typing import Any, ClassVar

import numpy as np
from scipy import stats
from statsmodels.stats.weightstats import ztest as sm_ztest

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.enums import AlternativeHypothesis, StatisticalTestType
from economicon.schemas.statistics import (
    ConfidenceIntervalBounds,
    StatisticalTestRequestBody,
    StatisticalTestResult,
)
from economicon.services.data.tables_store import TablesStore
from economicon.utils.exceptions import ProcessingError, ValidationError
from economicon.utils.validators import validate_existence

# paired チェック・F 検定分岐で使用する定数
_TWO_SAMPLES: int = 2

# z 検定の 95% 信頼区間に使用する定数
# z_crit = norm.ppf(1 - α/2) = norm.ppf(0.975) ≈ 1.95996...
_ALPHA_95: float = 0.05
_Z_CRIT_95: float = float(stats.norm.ppf(1.0 - _ALPHA_95 / 2))


class StatisticalTest:
    """
    指定されたテーブルの列に対して統計的検定を
    実行するサービスクラス。

    対応検定:
      - t-test : 1 群・独立 2 群・対応あり 2 群
      - z-test : 1 群・2 群
      - f-test : 2 群の分散比検定 / 3 群以上の ANOVA
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "test_type": "testType",
        "samples": "samples",
    }

    def __init__(
        self,
        body: StatisticalTestRequestBody,
        tables_store: TablesStore,
    ) -> None:
        self.tables_store = tables_store
        self.test_type = body.test_type
        self.samples = body.samples
        self.options = body.options

    # ------------------------------------------------------------------ #
    # DataOperation インターフェイス                                        #
    # ------------------------------------------------------------------ #

    def validate(self) -> None:
        """
        入力バリデーション。

        - 各サンプルのテーブル名・列名の存在確認
        - paired=True の場合はサンプルサイズ一致チェック
        """
        table_name_list = self.tables_store.get_table_name_list()

        for i, sample in enumerate(self.samples):
            # テーブル存在確認
            validate_existence(
                value=sample.table_name,
                valid_list=table_name_list,
                target=f"samples[{i}].tableName",
            )
            # 列存在確認
            col_list = self.tables_store.get_column_name_list(
                sample.table_name
            )
            validate_existence(
                value=sample.column_name,
                valid_list=col_list,
                target=f"samples[{i}].columnName",
            )

        # 対応あり検定: サンプルサイズ一致チェック
        # （to_numpy を避け、Polars で列長のみ取得）
        if len(self.samples) == _TWO_SAMPLES and self.options.paired:
            lengths = [
                len(
                    self.tables_store.get_table(s.table_name)
                    .table[s.column_name]
                    .drop_nulls()
                )
                for s in self.samples
            ]
            if lengths[0] != lengths[1]:
                raise ValidationError(
                    error_code=ErrorCode.STATISTICAL_TEST_ERROR,
                    message=_(
                        "Paired test requires equal sample sizes,"
                        " but got {} and {}"
                    ).format(lengths[0], lengths[1]),
                    target="samples",
                )

    def execute(self) -> dict:
        """統計的検定を実行し、結果 dict を返す。"""
        try:
            arrays = self._get_arrays()

            # 空データチェック
            for i, arr in enumerate(arrays):
                if len(arr) == 0:
                    raise ValidationError(
                        error_code=ErrorCode.STATISTICAL_TEST_ERROR,
                        message=_(
                            "samples[{}] contains no valid data"
                            " (all values are null)"
                        ).format(i),
                        target=f"samples[{i}]",
                    )

            match self.test_type:
                case StatisticalTestType.T_TEST:
                    return self._run_ttest(arrays)
                case StatisticalTestType.Z_TEST:
                    return self._run_ztest(arrays)
                case StatisticalTestType.F_TEST:
                    return self._run_ftest(arrays)

        except ValidationError, ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.STATISTICAL_TEST_ERROR,
                message=_(
                    "An unexpected error occurred during statistical testing"
                ),
                detail=str(e),
            ) from e

    # ------------------------------------------------------------------ #
    # データ取得                                                            #
    # ------------------------------------------------------------------ #

    def _get_arrays(self) -> list[np.ndarray]:
        """
        TablesStore から各サンプルのデータを
        numpy 配列として取得する。欠損値は除去する。
        """
        result: list[np.ndarray] = []
        for sample in self.samples:
            table_info = self.tables_store.get_table(sample.table_name)
            col = table_info.table[sample.column_name].drop_nulls()
            result.append(col.to_numpy().astype(float))
        return result

    # ------------------------------------------------------------------ #
    # 検定ロジック                                                          #
    # ------------------------------------------------------------------ #

    def _run_ttest(self, arrays: list[np.ndarray]) -> dict:
        """
        t 検定を実行する。

        - 1 群 : ttest_1samp
        - 2 群・対応なし : ttest_ind (等分散 / Welch)
        - 2 群・対応あり : ttest_rel

        信頼区間は常に両側 95% CI を計算する（片側検定時の
        inf を避けるため）。
        """
        alt_scipy = self._to_scipy_alternative(self.options.alternative)

        if len(arrays) == 1:
            mu = self.options.mu if self.options.mu is not None else 0.0
            res: Any = stats.ttest_1samp(
                arrays[0], popmean=mu, alternative=alt_scipy
            )
            # CI は two-sided で再計算（片側 alternative だと inf になる）
            ci_res: Any = stats.ttest_1samp(
                arrays[0], popmean=mu, alternative="two-sided"
            )
            df = float(res.df)
            ci = ci_res.confidence_interval(confidence_level=0.95)
            effect_size = self._cohen_d_1samp(arrays[0], mu)

        elif self.options.paired:
            res = stats.ttest_rel(arrays[0], arrays[1], alternative=alt_scipy)
            ci_res = stats.ttest_rel(
                arrays[0], arrays[1], alternative="two-sided"
            )
            df = float(res.df)
            ci = ci_res.confidence_interval(confidence_level=0.95)
            effect_size = self._cohen_d_paired(arrays[0], arrays[1])

        else:
            res = stats.ttest_ind(
                arrays[0],
                arrays[1],
                equal_var=self.options.equal_var,
                alternative=alt_scipy,
            )
            ci_res = stats.ttest_ind(
                arrays[0],
                arrays[1],
                equal_var=self.options.equal_var,
                alternative="two-sided",
            )
            df = float(res.df)
            ci = ci_res.confidence_interval(confidence_level=0.95)
            effect_size = self._cohen_d_2samp(
                arrays[0], arrays[1], self.options.equal_var
            )

        return StatisticalTestResult(
            statistic=float(res.statistic),
            p_value=float(res.pvalue),
            df=df,
            confidence_interval=ConfidenceIntervalBounds(
                lower=float(ci.low), upper=float(ci.high)
            ),
            effect_size=effect_size,
        ).model_dump(by_alias=True)

    def _run_ztest(self, arrays: list[np.ndarray]) -> dict:
        """
        z 検定を実行する（statsmodels を使用）。

        statsmodels の alternative は "two-sided" / "larger" / "smaller"
        を直接受け付けるため変換不要。
        """
        mu = self.options.mu if self.options.mu is not None else 0.0
        alt_sm = self.options.alternative.value

        if len(arrays) == 1:
            stat, p_val = sm_ztest(
                arrays[0],
                value=mu,  # type: ignore[arg-type]
                alternative=alt_sm,  # type: ignore[arg-type]
            )
            center = float(np.mean(arrays[0]))
            se = float(np.std(arrays[0], ddof=1) / np.sqrt(len(arrays[0])))
        else:
            stat, p_val = sm_ztest(
                arrays[0],
                arrays[1],
                value=mu,  # type: ignore[arg-type]
                alternative=alt_sm,  # type: ignore[arg-type]
            )
            center = float(np.mean(arrays[0]) - np.mean(arrays[1]))
            se = float(
                np.sqrt(
                    np.var(arrays[0], ddof=1) / len(arrays[0])
                    + np.var(arrays[1], ddof=1) / len(arrays[1])
                )
            )

        # 95% 信頼区間（モジュール定数 _Z_CRIT_95 を使用）
        return StatisticalTestResult(
            statistic=float(stat),
            p_value=float(p_val),
            df=None,
            confidence_interval=ConfidenceIntervalBounds(
                lower=center - _Z_CRIT_95 * se,
                upper=center + _Z_CRIT_95 * se,
            ),
            effect_size=None,
        ).model_dump(by_alias=True)

    def _run_ftest(self, arrays: list[np.ndarray]) -> dict:
        """
        F 検定を実行する。

        - 2 群 : 分散比 F 検定 (Snedecor's F-test)
        - 3 群以上 : 一元配置分散分析 (ANOVA)
        """
        if len(arrays) == _TWO_SAMPLES:
            return self._f_variance_ratio(arrays[0], arrays[1])
        return self._f_oneway_anova(arrays)

    def _f_variance_ratio(self, x: np.ndarray, y: np.ndarray) -> dict:
        """2 群の分散比 F 検定（両側）。"""
        var_x = float(np.var(x, ddof=1))
        var_y = float(np.var(y, ddof=1))
        f_stat = var_x / var_y
        df1 = len(x) - 1
        df2 = len(y) - 1
        # 両側 p 値
        p_val = 2.0 * min(
            float(stats.f.cdf(f_stat, df1, df2)),
            float(stats.f.sf(f_stat, df1, df2)),
        )
        return StatisticalTestResult(
            statistic=float(f_stat),
            p_value=p_val,
            df=float(df1),
            df2=float(df2),
            confidence_interval=None,
            effect_size=None,
        ).model_dump(by_alias=True)

    def _f_oneway_anova(self, arrays: list[np.ndarray]) -> dict:
        """一元配置分散分析（ANOVA）。効果量として η² を返す。"""
        res = stats.f_oneway(*arrays)
        dfn = float(len(arrays) - 1)  # 分子自由度: k - 1
        dfd = float(  # 分母自由度: N - k
            sum(len(a) for a in arrays) - len(arrays)
        )
        eta_sq = self._eta_squared(arrays)
        return StatisticalTestResult(
            statistic=float(res.statistic),
            p_value=float(res.pvalue),
            df=dfn,
            df2=dfd,
            confidence_interval=None,
            effect_size=eta_sq,
        ).model_dump(by_alias=True)

    # ------------------------------------------------------------------ #
    # 効果量計算                                                            #
    # ------------------------------------------------------------------ #

    def _cohen_d_1samp(self, x: np.ndarray, mu: float) -> float:
        """
        1 群 Cohen's d。

        d = |mean(x) - mu| / std(x, ddof=1)
        """
        return float(abs(np.mean(x) - mu) / np.std(x, ddof=1))

    def _cohen_d_2samp(
        self,
        x: np.ndarray,
        y: np.ndarray,
        equal_var: bool,
    ) -> float:
        """
        2 群独立 Cohen's d。

        equal_var=True  : プールされた標準偏差を使用
        equal_var=False : (s1² + s2²) / 2 の平方根を使用
        """
        n1, n2 = len(x), len(y)
        s1 = float(np.std(x, ddof=1))
        s2 = float(np.std(y, ddof=1))
        if equal_var:
            pooled = np.sqrt(
                ((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2)
            )
        else:
            pooled = np.sqrt((s1**2 + s2**2) / 2)
        return float(abs(np.mean(x) - np.mean(y)) / pooled)

    def _cohen_d_paired(self, x: np.ndarray, y: np.ndarray) -> float:
        """
        対応あり Cohen's d。

        d = |mean(x - y)| / std(x - y, ddof=1)
        """
        diff = x - y
        return float(abs(np.mean(diff)) / np.std(diff, ddof=1))

    def _eta_squared(self, arrays: list[np.ndarray]) -> float:
        """
        η² (Eta-squared) = SS_between / SS_total。

        SS_between = Σ n_i * (mean_i - grand_mean)²
        SS_total   = Σ (x_ij - grand_mean)²
        """
        all_data = np.concatenate(arrays)
        grand_mean = float(np.mean(all_data))
        ss_between = float(
            sum(len(g) * (float(np.mean(g)) - grand_mean) ** 2 for g in arrays)
        )
        ss_total = float(np.sum((all_data - grand_mean) ** 2))
        if ss_total == 0.0:
            return 0.0
        return ss_between / ss_total

    # ------------------------------------------------------------------ #
    # ヘルパー                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_scipy_alternative(alt: AlternativeHypothesis) -> str:
        """
        AlternativeHypothesis を scipy が受け付ける文字列に変換する。

        scipy: "two-sided" / "greater" / "less"
        """
        _alt_map: dict[AlternativeHypothesis, str] = {
            AlternativeHypothesis.TWO_SIDED: "two-sided",
            AlternativeHypothesis.LARGER: "greater",
            AlternativeHypothesis.SMALLER: "less",
        }
        return _alt_map[alt]
