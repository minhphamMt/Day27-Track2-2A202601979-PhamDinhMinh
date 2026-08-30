"""Robust statistical anomaly detectors used by the stable student API."""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def _values(history: Iterable[float]) -> np.ndarray:
    values = np.asarray(list(history), dtype=float)
    return values[np.isfinite(values)]


def zscore_detector(current: float, history: Iterable[float], threshold: float = 3.0) -> dict[str, Any]:
    values = _values(history)
    if values.size < 3 or not np.isfinite(float(current)):
        return {"is_anomaly": False, "score": 0.0, "method": "zscore", "reason": "insufficient_history"}
    mean = float(np.mean(values))
    std = float(np.std(values))
    delta = abs(float(current) - mean)
    score = float("inf") if std == 0 and delta > 0 else (0.0 if std == 0 else delta / std)
    return {
        "is_anomaly": bool(score > threshold),
        "score": float(score),
        "method": "zscore",
        "reason": f"mean={mean:.3f}, std={std:.3f}, threshold={threshold}",
    }


def mad_detector(current: float, history: Iterable[float], threshold: float = 3.5) -> dict[str, Any]:
    values = _values(history)
    if values.size < 5 or not np.isfinite(float(current)):
        return {"is_anomaly": False, "score": 0.0, "method": "mad", "reason": "insufficient_history"}
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    delta = abs(float(current) - median)
    if mad == 0:
        score = float("inf") if delta > 0 else 0.0
        return {
            "is_anomaly": bool(delta > 0),
            "score": score,
            "method": "mad",
            "reason": f"median={median:.3f}, mad=0.000, zero_mad_fallback=true",
        }
    modified_z = 0.6745 * delta / mad
    return {
        "is_anomaly": bool(modified_z > threshold),
        "score": float(modified_z),
        "method": "mad",
        "reason": f"median={median:.3f}, mad={mad:.3f}, threshold={threshold}",
    }


def detect_anomaly(
    current: float,
    history: Iterable[float],
    *,
    method: str = "auto",
    threshold: float = 3.0,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect a point anomaly, selecting a seasonality-aware robust baseline.

    ``same_segment_history`` is preferred for metrics such as weekday traffic.
    A known planned event suppresses paging but is explicitly recorded in the
    reason so that the decision is auditable.
    """
    context = context or {}
    if method == "mad":
        return mad_detector(current, history, threshold=max(3.5, threshold))
    if method == "zscore":
        return zscore_detector(current, history, threshold=threshold)
    if method != "auto":
        raise ValueError(f"Unsupported method: {method}")

    if context.get("known_event"):
        return {
            "is_anomaly": False,
            "score": 0.0,
            "method": "auto:known_event",
            "reason": f"known_event={context['known_event']}; anomaly_suppressed",
        }

    segment = _values(context.get("same_segment_history", []))
    baseline = segment if segment.size >= 3 else _values(history)
    if baseline.size >= 5:
        result = mad_detector(current, baseline, threshold=max(3.5, threshold))
        result["method"] = "auto:same_segment_mad" if segment.size >= 3 else "auto:mad"
        if context.get("trend"):
            result["reason"] += f"; trend={context['trend']}"
        return result

    result = zscore_detector(current, baseline, threshold=threshold)
    result["method"] = "auto:same_segment_zscore" if segment.size >= 3 else "auto:zscore"
    if segment.size < 3:
        result["reason"] += "; fallback=global_history"
    return result
