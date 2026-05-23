"""漸近正規性シミュレーションサービス"""

from __future__ import annotations

from typing import ClassVar

import numpy as np

from economicon.schemas.simulation import AsymptoticNormalityRequestBody


class AsymptoticNormality:
    """OLS 推定量の漸近正規性をシミュレーションする

    同一パラメータで num_simulations 回 OLS を行い、
    β̂ の標本分布を返す。誤差分布スイッチにより
    CLT の成立・不成立を確認できる。

    誤差タイプ別の挙動:
        normal    : ε ~ N(0, σ²)。n → ∞ で正規分布に収束
        cauchy    : ε ~ Cauchy(0, 1)。CLT 不成立（分散なし）
        endogenous: 省略変数 z による内生性。確率極限 β + γ/2
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {}

    def __init__(
        self,
        body: AsymptoticNormalityRequestBody,
    ) -> None:
        self.sample_size: int = body.sample_size
        self.num_simulations: int = body.num_simulations
        self.true_beta: float = body.true_beta
        self.error_variance: float = body.error_variance
        self.error_type: str = body.error_type
        self.endogeneity_strength: float = body.endogeneity_strength
        self.x_mean: float = body.x_distribution.x_mean
        self.x_variance: float = body.x_distribution.x_variance

    def validate(self) -> None:
        """バリデーション（Pydantic 側で完結）"""

    def execute(self) -> dict:
        """num_simulations 回 OLS を行い β̂ 分布を返す"""
        rng = np.random.default_rng()
        n = self.sample_size
        m = self.num_simulations
        x_std = float(np.sqrt(self.x_variance))

        match self.error_type:
            case "cauchy":
                beta_hat, is_normal, asym_mean, asym_var = self._run_cauchy(
                    rng, n, m, x_std
                )
            case "endogenous":
                beta_hat, is_normal, asym_mean, asym_var = (
                    self._run_endogenous(rng, n, m)
                )
            case _:  # "normal"
                beta_hat, is_normal, asym_mean, asym_var = self._run_normal(
                    rng, n, m, x_std
                )

        return {
            "betaEstimates": beta_hat.tolist(),
            "trueBeta": self.true_beta,
            "isAsymptoticallyNormal": is_normal,
            "asymptoticMean": asym_mean,
            "asymptoticVariance": asym_var,
        }

    @staticmethod
    def _ols_slope(
        x: np.ndarray,
        y: np.ndarray,
    ) -> np.ndarray:
        """行列 (m, n) の各行で OLS 傾き β̂ を計算する"""
        x_c = x - x.mean(axis=1, keepdims=True)
        y_c = y - y.mean(axis=1, keepdims=True)
        return (x_c * y_c).sum(axis=1) / (x_c**2).sum(axis=1)

    def _run_normal(
        self,
        rng: np.random.Generator,
        n: int,
        m: int,
        x_std: float,
    ) -> tuple[np.ndarray, bool, float | None, float | None]:
        """正規誤差: CLT 成立。漸近分散 = σ²/(n·Var(x))"""
        x = rng.normal(loc=self.x_mean, scale=x_std, size=(m, n))
        eps_std = float(np.sqrt(self.error_variance))
        eps = rng.normal(scale=eps_std, size=(m, n))
        y = self.true_beta * x + eps
        beta_hat = self._ols_slope(x, y)
        asym_var = self.error_variance / (n * self.x_variance)
        return beta_hat, True, self.true_beta, asym_var

    def _run_cauchy(
        self,
        rng: np.random.Generator,
        n: int,
        m: int,
        x_std: float,
    ) -> tuple[np.ndarray, bool, float | None, float | None]:
        """コーシー誤差: CLT 不成立（分散が存在しない）"""
        x = rng.normal(loc=self.x_mean, scale=x_std, size=(m, n))
        eps = rng.standard_cauchy(size=(m, n))
        y = self.true_beta * x + eps
        beta_hat = self._ols_slope(x, y)
        return beta_hat, False, None, None

    def _run_endogenous(
        self,
        rng: np.random.Generator,
        n: int,
        m: int,
    ) -> tuple[np.ndarray, bool, float | None, float | None]:
        """省略変数による内生性モデル

        DGP:
            z ~ N(0, 1), v ~ N(0, 1) 独立
            x = x_mean + z + v          (Var(x) = 2)
            ε = γ·z + η, η ~ N(0, σ²)
            y = β·x + ε

        確率極限: β + γ·Cov(x,z)/Var(x) = β + γ/2
        漸近分散: (γ²+σ²) / (2n)
        """
        gamma = self.endogeneity_strength
        z = rng.standard_normal(size=(m, n))
        v = rng.standard_normal(size=(m, n))
        eta = rng.normal(
            scale=float(np.sqrt(self.error_variance)),
            size=(m, n),
        )
        x = self.x_mean + z + v
        eps = gamma * z + eta
        y = self.true_beta * x + eps
        beta_hat = self._ols_slope(x, y)

        # 確率極限
        plim = self.true_beta + gamma / 2.0
        # 漸近分散: Var(ε) = γ²·Var(z)+Var(η) = γ²+σ²
        eps_var = gamma**2 + self.error_variance
        asym_var = eps_var / (2.0 * n)
        return beta_hat, True, plim, asym_var
