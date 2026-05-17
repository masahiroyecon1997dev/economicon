"""信頼区間シミュレーションサービス"""

from __future__ import annotations

from typing import ClassVar

import numpy as np
from scipy import stats

from economicon.schemas.simulation import ConfidenceIntervalSimRequestBody


class ConfidenceIntervalSim:
    """信頼区間の被覆確率をシミュレーションする

    M 回のサンプリングを行い、各試行の信頼区間と
    真の値との包含関係を一括返却する。
    アニメーションはフロントエンドが担当する。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {}

    def __init__(
        self,
        body: ConfidenceIntervalSimRequestBody,
    ) -> None:
        self.ci_type: str = body.ci_type
        self.trials: int = body.trials
        self.sample_size: int = body.sample_size
        self.confidence_level: float = body.confidence_level
        self.true_mean: float = body.true_mean
        self.true_variance: float = body.true_variance

    def validate(self) -> None:
        """バリデーション（Pydantic 側で完結）"""

    def execute(self) -> dict:
        """M 回サンプリングして各試行の信頼区間を返す"""
        rng = np.random.default_rng()
        alpha = 1.0 - self.confidence_level
        std = float(np.sqrt(self.true_variance))

        # shape: (trials, sample_size)
        samples: np.ndarray = rng.normal(
            loc=self.true_mean,
            scale=std,
            size=(self.trials, self.sample_size),
        )

        if self.ci_type == "mean":
            lowers, uppers, true_value = self._mean_ci(samples, alpha)
        else:
            lowers, uppers, true_value = self._variance_ci(samples, alpha)

        intervals = [
            {
                "lower": float(lowers[i]),
                "upper": float(uppers[i]),
                "containsTrue": bool(lowers[i] <= true_value <= uppers[i]),
            }
            for i in range(self.trials)
        ]
        return {
            "trueValue": true_value,
            "confidenceLevel": float(self.confidence_level),
            "intervals": intervals,
        }

    def _mean_ci(
        self,
        samples: np.ndarray,
        alpha: float,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """t 分布による平均の信頼区間を計算する"""
        true_value = float(self.true_mean)
        means = samples.mean(axis=1)
        stds = samples.std(axis=1, ddof=1)
        t_crit = float(
            stats.t.ppf(
                1.0 - alpha / 2.0,
                df=self.sample_size - 1,
            )
        )
        margin = t_crit * stds / np.sqrt(self.sample_size)
        return means - margin, means + margin, true_value

    def _variance_ci(
        self,
        samples: np.ndarray,
        alpha: float,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """χ² 分布による分散の信頼区間を計算する"""
        true_value = float(self.true_variance)
        sample_vars = samples.var(axis=1, ddof=1)
        df = self.sample_size - 1
        chi2_low = float(stats.chi2.ppf(alpha / 2.0, df=df))
        chi2_high = float(stats.chi2.ppf(1.0 - alpha / 2.0, df=df))
        # 区間: ((n-1)s² / χ²_{1-α/2}, (n-1)s² / χ²_{α/2})
        lowers = df * sample_vars / chi2_high
        uppers = df * sample_vars / chi2_low
        return lowers, uppers, true_value
