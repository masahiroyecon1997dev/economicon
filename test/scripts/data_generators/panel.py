import numpy as np
import pandas as pd

from data_generators.helpers import N_ENTITIES, N_PANEL, N_PERIODS


# 大きめの個体効果を入れて FE/RE の識別を明瞭にする。
def generate_panel_data(rng: np.random.Generator) -> pd.DataFrame:
    entity_ids = np.repeat(np.arange(1, N_ENTITIES + 1), N_PERIODS)
    time_ids = np.tile(np.arange(1, N_PERIODS + 1), N_ENTITIES)

    entity_effects = rng.normal(0.0, 5.0, N_ENTITIES)
    alpha = np.repeat(entity_effects, N_PERIODS)

    x1 = rng.normal(0.0, 4.0, N_PANEL)
    x2 = rng.normal(0.0, 3.0, N_PANEL)
    eps = rng.normal(0.0, 1.5, N_PANEL)
    y = 1.0 + 3.0 * x1 - 2.0 * x2 + alpha + eps

    return pd.DataFrame(
        {
            "entity_id": entity_ids.astype(float),
            "time_id": time_ids.astype(float),
            "y": y,
            "x1": x1,
            "x2": x2,
        }
    )
