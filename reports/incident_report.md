# Incident Report — Data Reliability Game Day

**Student:** Phạm Đình Minh
**MSV:** 2A202601979
**Incident:** stale knowledge-base publication (public `stale_kb` scenario)
**Severity:** P1 — Support Agent answers could use an outdated refund policy.

## Summary

The pipeline process remained healthy and orders continued to load (600 rows),
but the newest KB publication timestamp was three hours behind the run clock.
The order contract and row-count signals stayed healthy, so the KB freshness
contract was the decisive signal. The stale documents were quarantined before
they could become the active RAG knowledge base.

## Detection

- **Signal:** `kb_documents.published_at` freshness contract (`max_delay_minutes=60`).
- **First observed:** 2026-08-30 game-day run (UTC; exact run metadata is in `reports/public-fault-evidence.json`).
- **Observed result:** `kb_failed_contract_checks=1`; orders had 0 failed checks and the row-count anomaly was false.

## Root Cause

The incoming KB batch carried publication timestamps approximately 180 minutes
old. This is a producer freshness violation, not an API/process outage. The
contract validator reported the failure with `severity=warning` and
`action=quarantine`, allowing orders to continue while preventing stale KB
content from being promoted.

## Evidence

1. `reports/game-day-stale_kb.json` records one failed KB contract check while orders remain healthy.
2. `contracts/kb_contract.yaml` declares `published_at` freshness of 60 minutes.
3. `data/baseline/lineage_graph.json` traces `kb_documents -> kb_active_docs -> rag_index -> support_agent`.
4. `reports/public-fault-evidence.json` contains reproducible healthy, duplicate-PK, volume-drop and stale-KB results.

## Blast Radius

```text
kb_documents
  -> kb_active_docs
  -> rag_index
  -> support_agent
```

There is no edge from this KB branch to `fct_daily_revenue` or the CEO revenue
dashboard. Revenue/order consumers therefore remain unaffected.

## Mitigation

1. Quarantine the stale KB batch and retain the last known-good active KB.
2. Notify the `support-ai` data owner with the freshness age and batch ID.
3. Re-publish the documents with a current `published_at` timestamp, then rerun
   contract validation before rebuilding the RAG index.

## Recovery and Verification

- [x] Contract healthy after reset and re-run (`kb_failed_contract_checks=0`).
- [x] dbt tests and transformation checks pass (`tests_public`: 15 passed; dbt flow verified locally).
- [x] Anomaly returned to expected range (`row_count_anomaly=false`).
- [x] SLO/error budget calculation is present in `reports/game-day-healthy.json`.
- [x] SLO worked example is documented: target 99.5%, 2 bad events / 100 requests = 2% actual, 0.5% allowed, burn rate 4x, breach=true.
- [x] Downstream blast radius traced by dataset and column lineage functions.

## Prevention / Action Items

| Action | Owner | Deadline | Why |
|---|---|---|---|
| Enforce the KB freshness contract before promotion | support-ai | 2026-09-05 | Prevent stale policy answers |
| Emit quarantine count and freshness age as SLO metrics | data-platform | 2026-09-07 | Make the signal actionable |
| Add a producer alert at 45 minutes (before the 60-minute block) | data-platform | 2026-09-10 | Leave response headroom |
| Run this four-scenario game day in CI weekly | reliability | 2026-09-12 | Detect regressions in detectors and reports |
