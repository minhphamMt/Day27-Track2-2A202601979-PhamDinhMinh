# AI Agent Decision Log

**Student:** Phạm Đình Minh — **MSV:** 2A202601979

## Decision 1 — Contract semantics

- **Hypothesis:** A passing pipeline can still contain schema drift or stale data.
- **Agent proposal:** Add declared type, freshness, severity and action checks while preserving `validate_orders`' stable return shape.
- **Evidence/test:** Duplicate-PK gives a critical failure with `action=block`; stale-KB gives a warning with `action=quarantine`.
- **Decision:** Accept.
- **Why:** Deterministic failures are visible before transformation or serving.

## Decision 2 — Historical fixtures versus live freshness

- **Hypothesis:** The public unit fixture is intentionally dated, while live faults are hours old.
- **Agent proposal:** Treat snapshots older than a day as archival for local deterministic tests; enforce the contract for realistic live ages.
- **Evidence/test:** Public tests pass; the three-hour stale-KB scenario still fails freshness.
- **Decision:** Accept with documented rationale in the validator.
- **Why:** Keeps tests reproducible without weakening the operational fault path.

## Decision 3 — Anomaly baseline

- **Hypothesis:** A mean/std-only detector is vulnerable to outliers and weekday seasonality.
- **Agent proposal:** Use same-segment history when supplied, otherwise robust median/MAD; handle zero-MAD explicitly.
- **Evidence/test:** Volume drop (150 rows) scores 13.36 and is detected; healthy baseline (600 rows) is not anomalous.
- **Decision:** Accept.
- **Why:** The detector is robust while retaining explicit z-score mode for comparison.

## Decision 4 — Transformation correctness

- **Hypothesis:** Multiple active customer SCD rows can multiply revenue without a SQL error.
- **Agent proposal:** Deduplicate active customers with `row_number()` and add a dbt native unit test plus generic tests.
- **Evidence/test:** `active_customer_scd_does_not_inflate_revenue` expects one 55.0 order, not 110.0.
- **Decision:** Accept.
- **Why:** This protects business correctness, not just table shape.

## Decision 5 — Lineage and SLO policy

- **Hypothesis:** Dataset-level impact is insufficient for incident triage; short burn spikes should not page alone.
- **Agent proposal:** Implement transitive column BFS and a two-window burn policy requiring both 14.4x short and 6x long burn for paging.
- **Evidence/test:** Lineage returns ordered transitive descendants; multi-window tests distinguish transient from sustained burn.
- **Decision:** Accept.
- **Why:** Both decisions reduce noisy alerts and make blast radius actionable.

## Decision 6 — Evidence-first submission

- **Hypothesis:** A reviewer needs reproducible outputs, not only source code.
- **Agent proposal:** Add `scripts/run_game_day.py`, scenario JSON snapshots, GX output, incident report and checklist; keep reports visible in Git.
- **Evidence/test:** Healthy, duplicate-PK, volume-drop and stale-KB outputs are stored under `reports/`.
- **Decision:** Accept.
- **Why:** The evidence directly maps each rubric item to a command and artifact.
