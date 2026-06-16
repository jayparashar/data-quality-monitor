"""
data-quality-monitor: validator.py

Core quality check logic for tabular datasets.
Supports null rate checks, type validation, schema presence, and basic drift detection.
"""

from dataclasses import dataclass, field
from typing import Any
import statistics


@dataclass
class ValidationResult:
    passed: bool
    check: str
    message: str
    column: str = ""
    details: dict = field(default_factory=dict)


def check_schema_presence(data: list[dict], expected_columns: list[str]) -> list[ValidationResult]:
    """Verify all expected columns are present in the dataset."""
    results = []
    if not data:
        results.append(ValidationResult(
            passed=False,
            check="schema_presence",
            message="Dataset is empty — cannot validate schema.",
        ))
        return results

    actual_columns = set(data[0].keys())
    for col in expected_columns:
        present = col in actual_columns
        results.append(ValidationResult(
            passed=present,
            check="schema_presence",
            column=col,
            message=f"Column '{col}' {'found' if present else 'MISSING'} in dataset.",
        ))
    return results


def check_null_rates(data: list[dict], threshold: float = 0.10) -> list[ValidationResult]:
    """Flag columns where null rate exceeds threshold (default 10%)."""
    results = []
    if not data:
        return results

    columns = data[0].keys()
    total_rows = len(data)

    for col in columns:
        null_count = sum(1 for row in data if row.get(col) is None or row.get(col) == "")
        null_rate = null_count / total_rows
        passed = null_rate <= threshold
        results.append(ValidationResult(
            passed=passed,
            check="null_rate",
            column=col,
            message=(
                f"Column '{col}' null rate: {null_rate:.1%} "
                f"({'OK' if passed else f'EXCEEDS threshold of {threshold:.0%}'})"
            ),
            details={"null_count": null_count, "total_rows": total_rows, "null_rate": null_rate},
        ))
    return results


def check_type_consistency(
    data: list[dict], expected_types: dict[str, type]
) -> list[ValidationResult]:
    """Check that column values match expected Python types, ignoring nulls."""
    results = []
    if not data:
        return results

    for col, expected_type in expected_types.items():
        mismatches = []
        for i, row in enumerate(data):
            val = row.get(col)
            if val is None or val == "":
                continue
            if not isinstance(val, expected_type):
                mismatches.append({"row": i, "value": val, "type": type(val).__name__})

        passed = len(mismatches) == 0
        results.append(ValidationResult(
            passed=passed,
            check="type_consistency",
            column=col,
            message=(
                f"Column '{col}': {'all values match' if passed else f'{len(mismatches)} type mismatch(es)'} "
                f"expected type '{expected_type.__name__}'."
            ),
            details={"mismatches": mismatches[:5]},  # cap detail output at 5 examples
        ))
    return results


def check_numeric_drift(
    data: list[dict],
    baseline_stats: dict[str, dict[str, float]],
    tolerance: float = 0.25,
) -> list[ValidationResult]:
    """
    Detect distribution drift in numeric columns.
    Compares current mean against a baseline mean.
    Flags columns where the relative shift exceeds the tolerance (default 25%).
    """
    results = []
    if not data:
        return results

    for col, baseline in baseline_stats.items():
        values = [row[col] for row in data if row.get(col) is not None and isinstance(row[col], (int, float))]
        if not values:
            results.append(ValidationResult(
                passed=False,
                check="numeric_drift",
                column=col,
                message=f"Column '{col}': no numeric values found for drift check.",
            ))
            continue

        current_mean = statistics.mean(values)
        baseline_mean = baseline.get("mean", 0)

        if baseline_mean == 0:
            drift = 0.0
        else:
            drift = abs(current_mean - baseline_mean) / abs(baseline_mean)

        passed = drift <= tolerance
        results.append(ValidationResult(
            passed=passed,
            check="numeric_drift",
            column=col,
            message=(
                f"Column '{col}' mean drift: {drift:.1%} "
                f"(baseline={baseline_mean:.2f}, current={current_mean:.2f}) "
                f"{'OK' if passed else 'DRIFT DETECTED'}"
            ),
            details={"baseline_mean": baseline_mean, "current_mean": current_mean, "drift_pct": drift},
        ))
    return results


def run_all_checks(
    data: list[dict],
    expected_columns: list[str] | None = None,
    null_threshold: float = 0.10,
    expected_types: dict[str, type] | None = None,
    baseline_stats: dict[str, dict[str, float]] | None = None,
    drift_tolerance: float = 0.25,
) -> dict[str, Any]:
    """
    Run all configured quality checks and return a summary report.
    """
    all_results: list[ValidationResult] = []

    if expected_columns:
        all_results.extend(check_schema_presence(data, expected_columns))

    all_results.extend(check_null_rates(data, threshold=null_threshold))

    if expected_types:
        all_results.extend(check_type_consistency(data, expected_types))

    if baseline_stats:
        all_results.extend(check_numeric_drift(data, baseline_stats, tolerance=drift_tolerance))

    passed = [r for r in all_results if r.passed]
    failed = [r for r in all_results if not r.passed]

    return {
        "total_checks": len(all_results),
        "passed": len(passed),
        "failed": len(failed),
        "pass_rate": len(passed) / len(all_results) if all_results else 0.0,
        "results": all_results,
        "failed_checks": failed,
    }
