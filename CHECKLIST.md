# Day 27 Submission Checklist

**Student:** Phạm Đình Minh  
**MSV:** 2A202601979

## Phase 0 — Baseline

- [x] Environment created from `requirements.txt`
- [x] `make reset` equivalent completed
- [x] Healthy baseline generated with 0 order and KB contract failures
- [x] `pytest tests_public -q` passes 15/15

## Phase 1 — Contract and validation

- [x] Required/null/unique/accepted/range checks retained
- [x] Type validation for integer, number, string and datetime
- [x] Freshness validation from YAML contract
- [x] Severity and action mapping (`block`, `quarantine`, `warn`)
- [x] Duplicate-PK fault detected

## Phase 2 — dbt protection

- [x] Generic data tests in staging and mart schemas
- [x] Singular non-negative revenue test
- [x] dbt native unit test for completed revenue
- [x] SCD duplicate-active-row unit test and SQL deduplication

## Phase 3 — Anomaly detection

- [x] Explicit z-score mode retained
- [x] Robust MAD mode with zero-MAD handling
- [x] `auto` mode supports same-segment history and known-event suppression
- [x] Volume-drop fault detected from metrics, not a hard-coded row count

## Phase 4 — Lineage and blast radius

- [x] Dataset transitive BFS
- [x] Column transitive BFS
- [x] dbt manifest graph parser retained
- [x] KB blast radius documented in incident report

## Phase 5 — SLO and RAG signals

- [x] SLO, actual/allowed bad rate, burn rate and remaining budget
- [x] Multi-window burn policy distinguishes transient/sustained burn
- [x] RAG text-length signal
- [x] RAG embedding-norm drift signal

## Phase 6/7 — Incident and submission

- [x] Healthy, duplicate-PK, volume-drop and stale-KB evidence snapshots
- [x] `reports/incident_report.md` completed
- [x] `reports/agent_log.md` contains six decisions with evidence
- [x] GX suite, ValidationDefinition and Checkpoint run successfully
- [x] `.gitignore` audited: `reports/` and required evidence are not ignored
