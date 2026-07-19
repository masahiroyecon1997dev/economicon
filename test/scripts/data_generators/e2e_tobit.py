import numpy as np
import pandas as pd

# E2E テスト用両側打ち切りデータのサンプルサイズ
N_E2E_TOBIT = 200

# 右側打ち切り値 (E2E テスト側でハードコードする値と一致させること)
RIGHT_CENSORING_LIMIT = 4.0


# DGP: y* = 1.5 + 1.2*x1 + 0.9*x2 + ε, ε ~ N(0, 2)
#
# y_left : 左側打ち切り (left=0)
#          → E2E Step 4 で使用: チェックボックス左のみ ON、右 OFF
# y_both : 両側打ち切り (left=0, right=RIGHT_CENSORING_LIMIT)
#          → E2E Step 5 で使用: 左右両方 ON
#
# 設計根拠:
#   y* の総標準偏差 ≈ sqrt(1.2^2 + 0.9^2 + 4) ≈ 2.4
#   mean(y*) = 1.5 のとき:
#     P(y* < 0) ≈ 0.27  → 左打ち切り率 ~27%
#     P(y* > 4) ≈ 0.20  → 右打ち切り率 ~20%  (y_both)
def generate_e2e_tobit_data(rng: np.random.Generator) -> pd.DataFrame:
    x1 = rng.normal(0.0, 1.0, N_E2E_TOBIT)
    x2 = rng.normal(0.0, 1.0, N_E2E_TOBIT)
    eps = rng.normal(0.0, 2.0, N_E2E_TOBIT)

    y_latent = 1.5 + 1.2 * x1 + 0.9 * x2 + eps

    y_left = np.maximum(0.0, y_latent)
    y_both = np.clip(y_latent, 0.0, RIGHT_CENSORING_LIMIT)

    left_ratio_left = (y_left == 0.0).mean()
    left_ratio_both = (y_both == 0.0).mean()
    right_ratio_both = (y_both == RIGHT_CENSORING_LIMIT).mean()

    print(f"    [e2e_tobit] y_left: left-cens={left_ratio_left:.3f}")
    print(
        f"    [e2e_tobit] y_both: left-cens={left_ratio_both:.3f}, "
        f"right-cens={right_ratio_both:.3f}"
    )

    return pd.DataFrame(
        {
            "x1": x1,
            "x2": x2,
            "y_left": y_left,
            "y_both": y_both,
        }
    )
