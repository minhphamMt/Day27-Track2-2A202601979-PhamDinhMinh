from __future__ import annotations

from typing import Any

import math


def calculate_slo(target: float, bad_events: int, total_events: int) -> dict[str, Any]:
    if not 0 < target < 1:
        raise ValueError("target must be between 0 and 1 (exclusive)")
    if bad_events < 0 or total_events < 0 or bad_events > total_events:
        raise ValueError("invalid event counts")
    allowed_bad_rate = 1.0 - target
    if total_events == 0:
        return {
            "target": target,
            "actual_bad_rate": 0.0,
            "allowed_bad_rate": allowed_bad_rate,
            "burn_rate": 0.0,
            "remaining_error_budget_fraction": 1.0,
            "breached": False,
        }
    actual_bad_rate = bad_events / total_events
    burn_rate = actual_bad_rate / allowed_bad_rate
    consumed_fraction = min(1.0, actual_bad_rate / allowed_bad_rate)
    return {
        "target": target,
        "actual_bad_rate": actual_bad_rate,
        "allowed_bad_rate": allowed_bad_rate,
        "burn_rate": burn_rate,
        "remaining_error_budget_fraction": max(0.0, 1.0 - consumed_fraction),
        "breached": bool(actual_bad_rate > allowed_bad_rate),
    }


def evaluate_multiwindow_burn(
    *,
    short_window_burn: float,
    long_window_burn: float,
    policy: str = "starter",
) -> dict[str, Any]:
    """Apply a two-window burn policy.

    Paging requires both windows to be fast: a short spike alone is recorded
    but does not page, while sustained error-budget consumption pages at high
    severity.  Thresholds follow the commonly used 14.4x/6x SRE policy.
    """
    short_window_burn = float(short_window_burn)
    long_window_burn = float(long_window_burn)
    if not (math.isfinite(short_window_burn) and math.isfinite(long_window_burn)):
        raise ValueError("burn rates must be finite")
    if short_window_burn < 0 or long_window_burn < 0:
        raise ValueError("burn rates must be non-negative")
    fast_page = short_window_burn >= 14.4 and long_window_burn >= 6.0
    elevated = short_window_burn >= 6.0 and long_window_burn >= 3.0
    if fast_page:
        severity, reason = "critical", "sustained_fast_burn_both_windows"
    elif elevated:
        severity, reason = "warning", "elevated_burn_both_windows"
    elif short_window_burn >= 14.4:
        severity, reason = "info", "transient_short_window_spike"
    else:
        severity, reason = "info", "burn_within_policy"
    return {
        "page": bool(fast_page),
        "severity": severity,
        "reason": reason,
        "short_window_burn": short_window_burn,
        "long_window_burn": long_window_burn,
        "short_threshold": 14.4,
        "long_threshold": 6.0,
        "policy": policy,
    }
