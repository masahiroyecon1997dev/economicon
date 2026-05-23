"""DID（差の差）合成テストデータ生成モジュール。

DGP:
    y_it = α_i + λ_t + β1*x1_it + β2*x2_it + τ*(treated_i × post_t) + ε_it

    τ (ATT) = 2.5, β1 = 1.5, β2 = -0.8
    entity_effects ~ N(0, 3²), time_effects ~ N(0, 2²)
    x1 = 0.6*entity_component + 0.4*time_component + noise  (FE 非吸収)
    x2 = noise のみ
    ε ~ N(0, 1²)

    N_ENTITIES = 40, N_PERIODS = 8  (N = 320)
    treated = 上位 20 entity, post = time_id >= 4 (treatment_start = 4)
    event_time = time_id - treatment_start  ∈ {-3, -2, -1, 0, 1, 2, 3}
    pre-trend テスト用: 真の前処理係数はすべて 0
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# DID 専用定数
_N_DID_ENTITIES = 40  # パネルの N_ENTITIES(10) より大きく取る
_N_DID_PERIODS = 8
_N_DID = _N_DID_ENTITIES * _N_DID_PERIODS

_TRUE_TAU = 2.5
_TRUE_BETA1 = 1.5
_TRUE_BETA2 = -0.8
_TREATMENT_START = 4  # time_id >= 4 で post=1
_N_TREATED = _N_DID_ENTITIES // 2  # 上位 20 entity が treated


def generate_did_data(rng: np.random.Generator) -> pd.DataFrame:
    """主データセット: 正常な 2×2 拡張 DID パネル。"""
    entity_ids = np.repeat(np.arange(1, _N_DID_ENTITIES + 1), _N_DID_PERIODS)
    time_ids = np.tile(np.arange(1, _N_DID_PERIODS + 1), _N_DID_ENTITIES)

    treated = (entity_ids <= _N_TREATED).astype(float)
    post = (time_ids >= _TREATMENT_START).astype(float)

    # event_time = time_id - treatment_start_period (1-indexed → 0-origin 調整)
    # treatment_start が time_id=4 なので event_time = time_id - 4
    event_time = time_ids - _TREATMENT_START

    # --- 個体効果・時間効果 ---
    entity_effects = rng.normal(0.0, 3.0, _N_DID_ENTITIES)
    time_effects = rng.normal(0.0, 2.0, _N_DID_PERIODS)
    alpha = np.repeat(entity_effects, _N_DID_PERIODS)
    lam = np.tile(time_effects, _N_DID_ENTITIES)

    # --- 共変量 (entity/time 成分を含み FE に吸収されない設計) ---
    entity_comp = np.repeat(rng.normal(0.0, 1.5, _N_DID_ENTITIES), _N_DID_PERIODS)
    time_comp = np.tile(rng.normal(0.0, 1.0, _N_DID_PERIODS), _N_DID_ENTITIES)
    x1 = 0.6 * entity_comp + 0.4 * time_comp + rng.normal(0.0, 0.8, _N_DID)
    x2 = rng.normal(0.0, 1.2, _N_DID)

    eps = rng.normal(0.0, 1.0, _N_DID)
    y = (
        alpha
        + lam
        + _TRUE_BETA1 * x1
        + _TRUE_BETA2 * x2
        + _TRUE_TAU * treated * post
        + eps
    )

    return pd.DataFrame(
        {
            "entity_id": entity_ids,  # int64 (arange)
            "time_id": time_ids,  # int64 (tile of arange)
            "treated": treated,
            "post": post,
            "event_time": event_time,  # int64
            "x1": x1,
            "x2": x2,
            "y": y,
        }
    )


def generate_did_duplicate(df: pd.DataFrame) -> pd.DataFrame:
    """重複行ありデータ（バリデーション確認用）。"""
    dup = pd.concat([df, df.head(1)], ignore_index=True)
    return dup


def generate_did_bad_treatment(df: pd.DataFrame) -> pd.DataFrame:
    """treated 列に 0/1 以外の値が 1 行含まれるデータ（バリデーション確認用）。"""
    bad = df.copy()
    # 最初の 1 行だけ treated=2 にする → API バリデータの "Found 1 non-binary value(s)." に対応
    bad.loc[bad.index[0], "treated"] = 2.0
    return bad


def generate_did_datasets(rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    """全 DID データセットをまとめて返す。"""
    main = generate_did_data(rng)
    return {
        "synthetic_did": main,
        "synthetic_did_duplicate": generate_did_duplicate(main),
        "synthetic_did_bad_treatment": generate_did_bad_treatment(main),
    }
