#!/usr/bin/env python3
"""Small Great Expectations Core 1.21 example.

This file demonstrates the modern dataframe flow with a few expectations.
Students should extend it into a reusable Expectation Suite / Validation
Definition / Checkpoint and design actions based on severity.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from great_expectations.core.validation_definition import ValidationDefinition

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import great_expectations as gx
except ImportError as exc:  # friendlier classroom failure
    raise SystemExit("great_expectations is not installed. Run: pip install -r requirements.txt") from exc


def main() -> None:
    df = pd.read_csv(ROOT / "data" / "incoming" / "orders.csv")
    context = gx.get_context()

    # Use unique names so re-running inside an ephemeral context is simple.
    data_source = context.data_sources.add_pandas("orders_pandas")
    asset = data_source.add_dataframe_asset(name="orders_dataframe")
    batch_definition = asset.add_batch_definition_whole_dataframe("whole_orders")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="order_id", severity="critical",
            meta={"severity": "critical", "action": "block"},
        ),
        gx.expectations.ExpectColumnValuesToBeUnique(
            column="order_id", severity="critical",
            meta={"severity": "critical", "action": "block"},
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="amount", min_value=0, severity="critical",
            meta={"severity": "critical", "action": "block"},
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="currency", value_set=["USD", "VND"], severity="critical",
            meta={"severity": "critical", "action": "block"},
        ),
    ]

    # Package the expectations into the modern GX Core objects as well as
    # validating them below.  This gives the run a reusable suite/checkpoint
    # boundary and leaves severity/action metadata for downstream actions.
    suite = gx.ExpectationSuite(
        name="orders_contract_suite",
        expectations=expectations,
        meta={"owner": "commerce-data", "actions": {"critical": "block"}},
    )
    validation_definition = ValidationDefinition(
        name="orders_contract_validation",
        data=batch_definition,
        suite=suite,
    )
    checkpoint = gx.Checkpoint(
        name="orders_contract_checkpoint",
        validation_definitions=[validation_definition],
        result_format="SUMMARY",
    )
    context.suites.add(suite)
    context.validation_definitions.add(validation_definition)
    context.checkpoints.add(checkpoint)
    checkpoint_result = checkpoint.run(batch_parameters={"dataframe": df})

    all_ok = True
    for expectation in expectations:
        result = batch.validate(expectation)
        all_ok = all_ok and bool(result.success)
        print(f"{expectation.__class__.__name__:<40} success={result.success}")

    print("\nGX suite/checkpoint result:", "PASS" if checkpoint_result.success else "FAIL")
    print("Severity actions: critical -> block; warning -> quarantine; info -> warn")


if __name__ == "__main__":
    main()
