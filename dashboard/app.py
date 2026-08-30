from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "latest_metrics.json"
HISTORY = ROOT / "data" / "history" / "metrics_history.csv"

st.set_page_config(page_title="Data Reliability Lab", layout="wide")
st.title("Data Reliability Game Day")
st.caption("Evidence-first view of contract, anomaly, lineage and SLO signals.")

if not REPORT.exists():
    st.warning("Run `make baseline` first to generate reports/latest_metrics.json")
    st.stop()

report = json.loads(REPORT.read_text(encoding="utf-8"))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Orders rows", report["orders_rows"])
c2.metric("Freshness (min)", f"{report['freshness_minutes']:.1f}")
c3.metric("Contract failures", report["failed_contract_checks"])
c4.metric("Critical failures", report["critical_contract_failures"])
c5.metric("KB contract failures", report.get("kb_failed_contract_checks", 0))

st.subheader("Current signals")
st.json({
    "row_count_anomaly": report["row_count_anomaly"],
    "kb_text_length_signal": report["kb_text_length_signal"],
    "contract_slo": report["contract_slo"],
})

history = pd.read_csv(HISTORY)
st.subheader("Historical row count")
st.line_chart(history.set_index("date")[["row_count"]])

st.subheader("Example blast radius")
st.write("stg_orders -> " + " -> ".join(report["sample_blast_radius_from_stg_orders"]))

st.subheader("SLO and incident status")
slo = report["contract_slo"]
st.json({
    "target": slo["target"],
    "actual_bad_rate": slo["actual_bad_rate"],
    "allowed_bad_rate": slo["allowed_bad_rate"],
    "burn_rate": slo["burn_rate"],
    "remaining_error_budget_fraction": slo["remaining_error_budget_fraction"],
    "breached": slo["breached"],
    "incident_status": "investigate" if report.get("kb_failed_contract_checks", 0) else "healthy",
    "runbook": "reports/incident_report.md",
})
