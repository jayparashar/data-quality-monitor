"""
test_validator.py

Unit tests for data-quality-monitor/validator.py
"""

import pytest
from validator import (
    check_schema_presence,
    check_null_rates,
    check_type_consistency,
    check_numeric_drift,
    run_all_checks,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_DATA = [
    {"customer_id": "C001", "age": 34, "revenue": 1200.50, "region": "West"},
    {"customer_id": "C002", "age": 28, "revenue": 980.00, "region": "East"},
    {"customer_id": "C003", "age": 45, "revenue": 1750.75, "region": "West"},
    {"customer_id": "C004", "age": 31, "revenue": 620.00, "region": "North"},
    {"customer_id": "C005", "age": 52, "revenue": 2100.00, "region": "South"},
]

DATA_WITH_NULLS = [
    {"customer_id": "C001", "age": 34, "revenue": None},
    {"customer_id": "C002", "age": None, "revenue": None},
    {"customer_id": None,   "age": 45, "revenue": 1750.75},
    {"customer_id": "C004", "age": None, "revenue": None},
    {"customer_id": "C005", "age": 52, "revenue": 2100.00},
]

BASELINE_STATS = {
    "age": {"mean": 38.0},
    "revenue": {"mean": 1330.25},
}


# ---------------------------------------------------------------------------
# Schema presence tests
# ---------------------------------------------------------------------------

def test_schema_all_columns_present():
    results = check_schema_presence(SAMPLE_DATA, ["customer_id", "age", "revenue", "region"])
    assert all(r.passed for r in results)


def test_schema_missing_column():
    results = check_schema_presence(SAMPLE_DATA, ["customer_id", "age", "score"])
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].column == "score"


def test_schema_empty_dataset():
    results = check_schema_presence([], ["customer_id"])
    assert not results[0].passed
    assert "empty" in results[0].message.lower()


# ---------------------------------------------------------------------------
# Null rate tests
# ---------------------------------------------------------------------------

def test_null_rate_clean_data():
    results = check_null_rates(SAMPLE_DATA, threshold=0.10)
    assert all(r.passed for r in results)


def test_null_rate_exceeds_threshold():
    results = check_null_rates(DATA_WITH_NULLS, threshold=0.10)
    failed = [r for r in results if not r.passed]
    failed_cols = {r.column for r in failed}
    assert "revenue" in failed_cols
    assert "age" in failed_cols


def test_null_rate_threshold_boundary():
    # Exactly at threshold should pass
    data = [{"score": None if i == 0 else i} for i in range(10)]
    results = check_null_rates(data, threshold=0.10)
    assert results[0].passed


# ---------------------------------------------------------------------------
# Type consistency tests
# ---------------------------------------------------------------------------

def test_type_consistency_all_match():
    results = check_type_consistency(SAMPLE_DATA, {"age": int, "revenue": float})
    assert all(r.passed for r in results)


def test_type_consistency_mismatch():
    bad_data = [
        {"customer_id": "C001", "age": "thirty-four", "revenue": 1200.50},
        {"customer_id": "C002", "age": 28, "revenue": 980.00},
    ]
    results = check_type_consistency(bad_data, {"age": int})
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].column == "age"


# ---------------------------------------------------------------------------
# Numeric drift tests
# ---------------------------------------------------------------------------

def test_no_drift_within_tolerance():
    results = check_numeric_drift(SAMPLE_DATA, BASELINE_STATS, tolerance=0.25)
    assert all(r.passed for r in results)


def test_drift_detected():
    # Revenue has shifted dramatically upward
    drifted_data = [
        {"age": 34, "revenue": 9500.00},
        {"age": 28, "revenue": 8800.00},
        {"age": 45, "revenue": 10200.00},
    ]
    results = check_numeric_drift(drifted_data, BASELINE_STATS, tolerance=0.25)
    revenue_result = next(r for r in results if r.column == "revenue")
    assert not revenue_result.passed


# ---------------------------------------------------------------------------
# run_all_checks integration tests
# ---------------------------------------------------------------------------

def test_run_all_checks_clean_data():
    report = run_all_checks(
        SAMPLE_DATA,
        expected_columns=["customer_id", "age", "revenue", "region"],
        null_threshold=0.10,
        expected_types={"age": int, "revenue": float},
        baseline_stats=BASELINE_STATS,
        drift_tolerance=0.25,
    )
    assert report["failed"] == 0
    assert report["pass_rate"] == 1.0


def test_run_all_checks_returns_summary_keys():
    report = run_all_checks(SAMPLE_DATA)
    for key in ["total_checks", "passed", "failed", "pass_rate", "results", "failed_checks"]:
        assert key in report


# ---------------------------------------------------------------------------
# Intentionally fragile tests — these will fail until fixed
# The nightly Copilot automation is configured to detect and repair these.
# ---------------------------------------------------------------------------

def test_null_rate_detail_keys():
    """Details dict should include null_count, total_rows, null_rate."""
    results = check_null_rates(SAMPLE_DATA)
    for r in results:
        # BUG: checking for a key named "row_count" that doesn't exist in the implementation
        # Copilot should fix this to use "total_rows" instead
        assert "row_count" in r.details


def test_drift_result_has_drift_key():
    """Details dict should expose drift percentage under 'drift_pct'."""
    results = check_numeric_drift(SAMPLE_DATA, BASELINE_STATS)
    for r in results:
        # BUG: checking for wrong key name "drift_percent" instead of "drift_pct"
        assert "drift_percent" in r.details
