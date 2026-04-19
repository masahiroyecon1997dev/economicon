from __future__ import annotations

import importlib.metadata
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "test" / "data" / "parquet"
BENCH_DIR = REPO_ROOT / "test" / "benchmarks" / "python" / "synthetic"
SEED = 2024

TOLERANCE_GUIDE = {
    "ols_coef": "atol=1e-12 (nonrobust)",
    "ols_se_hc1": "atol=1e-12",
    "logit_probit_coef": "atol=1e-8 (MLE 収束差)",
    "fe_re_coef": "atol=1e-12",
    "iv_coef": "atol=1e-12",
    "tobit_coef": "atol=1e-6 (py4etrics MLE)",
    "heckman_coef": "atol=1e-8 (2段階 OLS/Probit)",
    "rdd_coef": "atol=1e-4 (rdrobust ローカル多項式)",
    "lasso_ridge_coef_scaled": "atol=1e-8 (sklearn Pipeline)",
    "wls_coef": "atol=1e-12 (statsmodels WLS)",
    "gls_coef": "atol=1e-12 (statsmodels GLS)",
    "fgls_heteroskedastic_coef": "atol=1e-12 (1-step FGLS/WLS)",
    "fgls_ar1_coef": "atol=1e-10 (statsmodels GLSAR iterative_fit)",
}


class NumpyEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


def f(value: Any) -> float:
    return float(value)


def params_to_dict(result: Any, var_names: list[str]) -> dict[str, Any]:
    params = result.params
    bse = result.bse
    tvalues = result.tvalues
    pvalues = result.pvalues
    conf_int = result.conf_int()

    if hasattr(conf_int, "values"):
        conf_int_array = conf_int.values
    else:
        conf_int_array = conf_int

    return {
        "coefficients": {var: f(params[index]) for index, var in enumerate(var_names)},
        "std_errors": {var: f(bse[index]) for index, var in enumerate(var_names)},
        "t_values": {var: f(tvalues[index]) for index, var in enumerate(var_names)},
        "p_values": {var: f(pvalues[index]) for index, var in enumerate(var_names)},
        "conf_int": {
            var: {
                "lower": f(conf_int_array[index, 0]),
                "upper": f(conf_int_array[index, 1]),
            }
            for index, var in enumerate(var_names)
        },
    }


def lm_params_to_dict(result: Any, var_names: list[str]) -> dict[str, Any]:
    conf_int = result.conf_int()
    return {
        "coefficients": {var: f(result.params[var]) for var in var_names},
        "std_errors": {var: f(result.std_errors[var]) for var in var_names},
        "t_values": {var: f(result.tstats[var]) for var in var_names},
        "p_values": {var: f(result.pvalues[var]) for var in var_names},
        "conf_int": {
            var: {
                "lower": f(conf_int.loc[var, "lower"]),
                "upper": f(conf_int.loc[var, "upper"]),
            }
            for var in var_names
        },
    }


def build_linear_diagnostics(result: Any) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    if hasattr(result, "rsquared"):
        diagnostics["r_squared"] = f(result.rsquared)
    if hasattr(result, "rsquared_adj"):
        diagnostics["adj_r_squared"] = f(result.rsquared_adj)
    if hasattr(result, "fvalue"):
        diagnostics["f_test"] = {
            "statistic": f(result.fvalue),
            "p_value": f(result.f_pvalue),
        }
    if hasattr(result, "aic"):
        diagnostics["aic"] = f(result.aic)
    if hasattr(result, "bic"):
        diagnostics["bic"] = f(result.bic)
    if hasattr(result, "llf"):
        diagnostics["log_likelihood"] = f(result.llf)
    return diagnostics


def get_version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def build_meta(
    model: str,
    data_file: str,
    libraries: list[str],
    tolerance_keys: list[str],
    **extra: Any,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "libraries": {library: get_version(library) for library in libraries},
        "seed": SEED,
        "tolerance_guide": {key: TOLERANCE_GUIDE[key] for key in tolerance_keys},
        "data_file": data_file,
        "model": model,
    }
    meta.update(extra)
    return meta


def out_path(name: str) -> Path:
    return BENCH_DIR / f"synthetic_{name}_gold.json"


def write_benchmark(name: str, data: dict[str, Any], meta: dict[str, Any]) -> None:
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "estimates": data}
    with out_path(name).open("w", encoding="utf-8") as file_obj:
        json.dump(payload, file_obj, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    print(f"    -> synthetic_{name}_gold.json")
