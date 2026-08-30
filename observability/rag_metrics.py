from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from observability.anomaly import zscore_detector


def approximate_token_lengths(texts: Iterable[str]) -> list[int]:
    # Deliberately simple proxy; no tokenizer/model download needed.
    return [len(str(t).split()) for t in texts]


def detect_text_length_shift(
    current_texts: Iterable[str],
    baseline_batch_means: Iterable[float],
    *,
    threshold: float = 3.0,
) -> dict[str, Any]:
    lengths = approximate_token_lengths(current_texts)
    baseline = list(baseline_batch_means)
    if not lengths or not baseline:
        return {
            "is_anomaly": False,
            "score": 0.0,
            "method": "text_length_zscore",
            "reason": "empty_input",
            "metric": "mean_text_length",
            "current_mean": 0.0,
        }
    current_mean = float(np.mean(lengths)) if lengths else 0.0
    result = zscore_detector(current_mean, baseline, threshold=threshold)
    result["metric"] = "mean_text_length"
    result["current_mean"] = current_mean
    return result


def detect_embedding_norm_shift(
    current_norms: Iterable[float], baseline_norms: Iterable[float]
) -> dict[str, Any]:
    """Detect a shift in pre-computed embedding norms.

    Norms are intentionally accepted as inputs so this check is deterministic
    and does not download an embedding model during the lab.
    """
    current = np.asarray(list(current_norms), dtype=float)
    baseline = np.asarray(list(baseline_norms), dtype=float)
    current = current[np.isfinite(current)]
    baseline = baseline[np.isfinite(baseline)]
    if current.size == 0 or baseline.size < 3:
        return {"is_anomaly": False, "score": 0.0, "method": "embedding_norm_mad", "reason": "insufficient_history"}
    median = float(np.median(baseline))
    mad = float(np.median(np.abs(baseline - median)))
    current_median = float(np.median(current))
    delta = abs(current_median - median)
    if mad == 0:
        score = float("inf") if delta > 0 else 0.0
    else:
        score = 0.6745 * delta / mad
    return {
        "is_anomaly": bool(score > 3.5),
        "score": float(score),
        "method": "embedding_norm_mad",
        "reason": f"baseline_median={median:.4f}, current_median={current_median:.4f}, mad={mad:.4f}",
        "current_mean": float(np.mean(current)),
        "baseline_mean": float(np.mean(baseline)),
    }
