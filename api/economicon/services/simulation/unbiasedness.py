"""不偏性シミュレーションサービス"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np

if TYPE_CHECKING:
    from economicon.schemas.simulation import UnbiasednessRequestBody


class Unbiasedness:
    """OLS 推定量の不偏性をシミュレーションする

    同一母集団から M 回独立にサンプリングして OLS を行い、
    β̂ の標本分布を返す。β̂ の標本平均が真の値 β に収束する
    ことを示すために使用する。

    フロントエンド側での計算:
        累積平均: mean(beta_estimates[:k]) for k=1,...,M
        差分（第 2 プロット縦軸）: 累積平均 - true_beta
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {}

    def __init__(
        self,
        body: UnbiasednessRequestBody,
    ) -> None:
        self.num_trials: int = body.num_trials
        self.sample_size: int = body.sample_size
        self.true_beta: float = body.true_beta
        self.error_variance: float = body.error_variance
        self.x_mean: float = body.x_distribution.x_mean
        self.x_variance: float = body.x_distribution.x_variance

    def validate(self) -> None:
        """バリデーション（Pydantic 側で完結）"""

    def execute(self) -> dict:
        """M 回 OLS を行い β̂ のリストを返す"""
        rng = np.random.default_rng()
        m = self.num_trials
        n = self.sample_size
        x_std = float(np.sqrt(self.x_variance))
        eps_std = float(np.sqrt(self.error_variance))

        # shape: (m, n) — m 回の試行、各試行 n 観測
        x: np.ndarray = rng.normal(loc=self.x_mean, scale=x_std, size=(m, n))
        eps: np.ndarray = rng.normal(scale=eps_std, size=(m, n))
        y = self.true_beta * x + eps

        # 各試行（行）で OLS 傾き β̂ を計算
        x_c = x - x.mean(axis=1, keepdims=True)
        y_c = y - y.mean(axis=1, keepdims=True)
        beta_hat: np.ndarray = (x_c * y_c).sum(axis=1) / (x_c**2).sum(axis=1)

        return {
            "betaEstimates": beta_hat.tolist(),
            "trueBeta": self.true_beta,
        }
