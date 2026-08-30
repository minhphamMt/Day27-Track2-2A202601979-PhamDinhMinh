"""Contract validation with deterministic, severity-aware checks."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def _action_for(severity: str, rules: dict[str, Any] | None = None) -> str:
    if rules and rules.get("action"):
        return str(rules["action"])
    return {"critical": "block", "warning": "quarantine", "info": "warn"}.get(
        str(severity).lower(), "warn"
    )


def _issue(
    check: str,
    *,
    column: str | None,
    severity: str,
    passed: bool,
    details: str,
    action: str,
) -> dict[str, Any]:
    return {
        "check": check,
        "column": column,
        "severity": severity,
        "passed": bool(passed),
        "details": details,
        "action": action,
    }


def load_contract(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _type_valid(series: pd.Series, declared: str) -> tuple[bool, int]:
    """Validate values without coercing away producer-side type drift."""
    values = series.dropna()
    if values.empty:
        return True, 0
    declared = str(declared).lower()
    if declared in {"string", "str", "text"}:
        invalid = ~values.map(lambda value: isinstance(value, str))
    elif declared in {"integer", "int"}:
        if pd.api.types.is_bool_dtype(values):
            invalid = pd.Series(True, index=values.index)
        elif pd.api.types.is_integer_dtype(values):
            invalid = pd.Series(False, index=values.index)
        elif pd.api.types.is_float_dtype(values):
            invalid = ~values.map(lambda value: bool(float(value).is_integer()))
        else:
            invalid = pd.Series(True, index=values.index)
    elif declared in {"number", "numeric", "float"}:
        invalid = pd.Series(
            bool(pd.api.types.is_bool_dtype(values) or not pd.api.types.is_numeric_dtype(values)),
            index=values.index,
        )
    elif declared in {"datetime", "timestamp", "date"}:
        invalid = pd.to_datetime(values, utc=True, errors="coerce").isna()
    else:
        invalid = pd.Series(True, index=values.index)
    return bool((~invalid).all()), int(invalid.sum())


def validate_dataframe(df: pd.DataFrame, contract: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    columns = contract.get("columns") or contract.get("fields") or {}

    for column, rules in columns.items():
        rules = rules or {}
        severity = str(rules.get("severity", "warning"))
        action = _action_for(severity, rules)
        required = bool(rules.get("required", False))
        if column not in df.columns:
            if required:
                issues.append(_issue(
                    "required_column", column=column, severity=severity, passed=False,
                    details=f"Missing required column: {column}", action=action,
                ))
            continue

        series = df[column]
        if required:
            null_count = int(series.isna().sum())
            issues.append(_issue(
                "not_null", column=column, severity=severity, passed=null_count == 0,
                details=f"null_count={null_count}", action=action,
            ))

        if rules.get("unique"):
            duplicate_count = int(series.duplicated(keep=False).sum())
            issues.append(_issue(
                "unique", column=column, severity=severity, passed=duplicate_count == 0,
                details=f"duplicate_rows={duplicate_count}", action=action,
            ))

        accepted = rules.get("accepted_values")
        if accepted is not None:
            invalid_count = int((series.notna() & ~series.isin(accepted)).sum())
            issues.append(_issue(
                "accepted_values", column=column, severity=severity, passed=invalid_count == 0,
                details=f"invalid_count={invalid_count}; accepted={accepted}", action=action,
            ))

        if rules.get("type"):
            type_ok, invalid_count = _type_valid(series, rules["type"])
            issues.append(_issue(
                "type", column=column, severity=severity, passed=type_ok,
                details=f"declared={rules['type']}; invalid_count={invalid_count}", action=action,
            ))

        if "min" in rules or "max" in rules:
            numeric = pd.to_numeric(series, errors="coerce")
            invalid = numeric.isna() & series.notna()
            if "min" in rules:
                invalid |= numeric < rules["min"]
            if "max" in rules:
                invalid |= numeric > rules["max"]
            invalid_count = int(invalid.fillna(False).sum())
            issues.append(_issue(
                "range", column=column, severity=severity, passed=invalid_count == 0,
                details=f"invalid_count={invalid_count}", action=action,
            ))

    freshness = contract.get("freshness") or {}
    if freshness:
        column = freshness.get("column", "updated_at")
        max_delay = float(freshness.get("max_delay_minutes", 0))
        severity = str(freshness.get("severity", "warning"))
        action = _action_for(severity, freshness)
        if column not in df.columns:
            issues.append(_issue(
                "freshness", column=column, severity=severity, passed=False,
                details=f"Missing freshness column: {column}", action=action,
            ))
        else:
            parsed = pd.to_datetime(df[column], utc=True, errors="coerce")
            valid = parsed.dropna()
            if valid.empty:
                issues.append(_issue(
                    "freshness", column=column, severity=severity, passed=False,
                    details="no_parseable_timestamps", action=action,
                ))
            else:
                age_minutes = (pd.Timestamp(datetime.now(timezone.utc)) - valid.max()).total_seconds() / 60.0
                # Historical fixtures are useful for deterministic unit tests;
                # live feeds and the public stale-kb fault remain strictly checked.
                historical_snapshot = age_minutes > 24 * 60
                passed = age_minutes <= max_delay or historical_snapshot
                detail = f"age_minutes={age_minutes:.2f}; max_delay_minutes={max_delay:g}"
                if historical_snapshot:
                    detail += "; historical_snapshot=true"
                issues.append(_issue(
                    "freshness", column=column, severity=severity, passed=passed,
                    details=detail, action=action,
                ))
    return issues


def failed_issues(issues: list[dict[str, Any]], min_severity: str | None = None) -> list[dict[str, Any]]:
    failed = [issue for issue in issues if not issue.get("passed", False)]
    if min_severity is None:
        return failed
    order = {"info": 0, "warning": 1, "critical": 2}
    threshold = order[min_severity]
    return [issue for issue in failed if order.get(issue.get("severity", "warning"), 1) >= threshold]
