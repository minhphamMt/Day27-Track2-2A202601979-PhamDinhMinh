from datetime import datetime, timedelta, timezone

import pandas as pd

from student_api import (
    column_downstream,
    detect_metric,
    rag_embedding_shift,
    slo_status,
    multiwindow_burn,
    validate_orders,
)
from src.contract_validator import load_contract


def test_type_and_freshness_checks_are_reported():
    now = datetime.now(timezone.utc)
    df = pd.DataFrame([{
        "order_id": "not-an-int",
        "customer_id": "C1",
        "amount": 10.0,
        "currency": "USD",
        "status": "completed",
        "created_at": now.isoformat(),
        "updated_at": (now - timedelta(hours=2)).isoformat(),
    }])
    issues = validate_orders(df, "contracts/orders_contract.yaml")
    assert any(i["check"] == "type" and i["column"] == "order_id" and not i["passed"] for i in issues)
    assert any(i["check"] == "freshness" and not i["passed"] for i in issues)


def test_auto_uses_same_segment_history():
    result = detect_metric(
        255,
        [1000, 1001, 999, 1002, 998],
        context={"day_of_week": 5, "same_segment_history": [250, 260, 255, 252, 258]},
    )
    assert result["is_anomaly"] is False
    assert "same_segment" in result["method"]


def test_column_lineage_is_transitive():
    graph = {"column_lineage": {"a": ["b"], "b": ["c"], "c": ["d"]}}
    assert column_downstream(graph, "a") == ["b", "c", "d"]


def test_multiwindow_requires_sustained_burn_to_page():
    assert multiwindow_burn(20, 1)["page"] is False
    assert multiwindow_burn(20, 8)["page"] is True


def test_embedding_norm_shift_is_detected():
    result = rag_embedding_shift([1.5, 1.6, 1.55], [0.99, 1.0, 1.01, 1.0, 0.98])
    assert result["is_anomaly"] is True
