# Copilot Cloud Agent Instructions

## Project context

This is a Python data quality monitoring utility. It validates tabular datasets against configurable rules: schema presence, null rates, type consistency, and numeric drift detection.

## Code style

- Python 3.11+. Use type hints throughout.
- Follow the existing dataclass pattern in validator.py for any new result types.
- Keep functions single-purpose. Each check function should do one thing.
- No external dependencies beyond the standard library and pytest. Do not add pandas, numpy, or other data libraries without explicit instruction.

## Testing

- All new logic must have corresponding pytest tests in test_validator.py.
- Tests should cover the happy path, edge cases (empty data, null values), and failure cases.
- Do not delete existing tests. If a test is wrong, fix the test to match the correct behavior and explain why in the PR description.

## Pull request standards

- PR title format: `fix: <short description>` or `feat: <short description>`
- PR description should explain what changed, why, and reference the issue number.
- Open as a draft PR unless the change is trivial (e.g. a typo fix).

## What not to do

- Do not refactor working code unless the task explicitly asks for it.
- Do not change function signatures unless necessary to fix the issue.
- Do not add logging frameworks or configuration files not already in the repo.
