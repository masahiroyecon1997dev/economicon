"""一致性シミュレーションサービス（逐次 OLS）"""

from __future__ import annotations

from typing import ClassVar

import numpy as np

from economicon.schemas.simulation import ConsistencyRequestBody

# OLS が成立するために必要な最小サンプルサイズ（切片+傾きで 2 パラメータ）
_MIN_N_FOR_OLS: int = 2
# Sxx がこれ未満のとき説明変数の分散がほぼ 0 と見なす
_NEAR_ZERO_THRESHOLD: float = 1e-12


def _online_ols(x: np.ndarray, y: np.ndarray) -> list[float]:
    """n=2〜len(x) まで逐次 OLS を行い β̂ のリストを返す

    逐次加算による O(n) アルゴリズム:
        β̂_n = (Σx_i·y_i - n·x̄·ȳ) / (Σx_i² - n·x̄²)

    Returns
    -------
    list[float]
        長さ len(x)-1 のリスト（n=2, 3, ..., len(x) に対応）
    """
    results: list[float] = []
    sum_x = 0.0
    sum_y = 0.0
    sum_xx = 0.0
    sum_xy = 0.0

    for i in range(len(x)):
        xi = float(x[i])
        yi = float(y[i])
        sum_x += xi
        sum_y += yi
        sum_xx += xi * xi
        sum_xy += xi * yi
        n = i + 1

        if n < _MIN_N_FOR_OLS:
            continue

        # β̂ = (Σxy - Σx·Σy/n) / (Σx² - (Σx)²/n)
        denom = sum_xx - sum_x * sum_x / n
        if abs(denom) < _NEAR_ZERO_THRESHOLD:
            # 説明変数の分散がほぼ 0（数値的退化）
            results.append(float("nan"))
            continue
        numer = sum_xy - sum_x * sum_y / n
        results.append(numer / denom)

    return results


class Consistency:
    """OLS 推定量の一致性をシミュレーションする

    1 つのデータ生成過程から n=2〜n_max まで累積的に
    OLS を行い、サンプルサイズ増加に伴う収束軌跡を返す。

    endogenous=True の場合は省略変数モデルを使用し、
    推定値がバイアスを持ちながら別の確率極限に収束する様子を示す。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {}

    def __init__(self, body: ConsistencyRequestBody) -> None:
        self.n_max: int = body.n_max
        self.true_beta: float = body.true_beta
        self.error_variance: float = body.error_variance
        self.endogenous: bool = body.endogenous
        self.endogeneity_strength: float = body.endogeneity_strength
        self.x_mean: float = body.x_distribution.x_mean
        self.x_variance: float = body.x_distribution.x_variance

    def validate(self) -> None:
        """バリデーション（Pydantic 側で完結）"""

    def execute(self) -> dict:
        """n=2〜n_max の OLS 推定値の軌跡を返す"""
        rng = np.random.default_rng()

        if self.endogenous:
            x_arr, y_arr, prob_limit = self._gen_endogenous(rng)
        else:
            x_arr, y_arr, prob_limit = self._gen_exogenous(rng)

        beta_estimates = _online_ols(x_arr, y_arr)
        return {
            "nValues": list(range(2, self.n_max + 1)),
            "betaEstimates": beta_estimates,
            "trueBeta": self.true_beta,
            "probabilityLimit": prob_limit,
        }

    def _gen_exogenous(
        self,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """外生性が成立するデータ生成過程

        x ~ N(x_mean, x_variance), ε ~ N(0, σ²)
        確率極限 = true_beta
        """
        x_std = float(np.sqrt(self.x_variance))
        eps_std = float(np.sqrt(self.error_variance))
        x = rng.normal(loc=self.x_mean, scale=x_std, size=self.n_max)
        eps = rng.normal(scale=eps_std, size=self.n_max)
        y = self.true_beta * x + eps
        return x, y, self.true_beta

    def _gen_endogenous(
        self,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """省略変数による内生性ありのデータ生成過程

        DGP:
            z ~ N(0, 1), v ~ N(0, 1) 独立
            x = x_mean + z + v          (Var(x) = 2)
            y = β·x + γ·z + η, η ~ N(0, σ²)

        確率極限: β + γ·Cov(x,z)/Var(x) = β + γ/2
        """
        gamma = self.endogeneity_strength
        eps_std = float(np.sqrt(self.error_variance))
        n = self.n_max
        z = rng.standard_normal(size=n)
        v = rng.standard_normal(size=n)
        eta = rng.normal(scale=eps_std, size=n)
        x = self.x_mean + z + v
        y = self.true_beta * x + gamma * z + eta
        prob_limit = self.true_beta + gamma / 2.0
        return x, y, prob_limit
