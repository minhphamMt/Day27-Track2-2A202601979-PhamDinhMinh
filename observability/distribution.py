"""Distribution drift signals without requiring a heavyweight statistics stack."""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def detect_distribution_shift(
    current_values: Iterable[float],
    baseline_values: Iterable[float],
    *,
    ratio_threshold: float = 3.0,
) -> dict[str, Any]:
    cur = np.asarray(list(current_values), dtype=float)
    base = np.asarray(list(baseline_values), dtype=float)
    cur = cur[np.isfinite(cur)]
    base = base[np.isfinite(base)]
    if cur.size == 0 or base.size == 0:
        return {"is_anomaly": False, "score": 0.0, "method": "robust_distribution", "reason": "empty_input"}

    cur_mean, base_mean = float(np.mean(cur)), float(np.mean(base))
    mean_scale = max(abs(base_mean), np.finfo(float).eps)
    mean_ratio = max(abs(cur_mean) / mean_scale, mean_scale / max(abs(cur_mean), np.finfo(float).eps))

    cur_std, base_std = float(np.std(cur)), float(np.std(base))
    if base_std == 0:
        spread_ratio = float("inf") if cur_std > 0 else 1.0
    elif cur_std == 0:
        spread_ratio = float("inf")
    else:
        spread_ratio = max(cur_std / base_std, base_std / cur_std)

    quantiles = np.asarray([0.05, 0.25, 0.5, 0.75, 0.95])
    base_q = np.quantile(base, quantiles)
    cur_q = np.quantile(cur, quantiles)
    iqr = float(np.quantile(base, 0.75) - np.quantile(base, 0.25))
    scale = max(iqr, base_std, np.finfo(float).eps)
    quantile_score = float(np.max(np.abs(cur_q - base_q)) / scale)
    score = float(max(mean_ratio, spread_ratio, quantile_score))
    return {
        "is_anomaly": bool(score >= ratio_threshold),
        "score": score,
        "method": "robust_distribution",
        "reason": (
            f"baseline_mean={base_mean:.3f}, current_mean={cur_mean:.3f}, "
            f"mean_ratio={mean_ratio:.3f}, spread_ratio={spread_ratio:.3f}, "
            f"quantile_score={quantile_score:.3f}, threshold={ratio_threshold}"
        ),
    }
