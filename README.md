# data-quality-monitor

A lightweight Python utility for validating dataset quality. Checks for null values, type mismatches, schema drift, and basic statistical anomalies across tabular datasets.

Built as a practical example for exploring GitHub Copilot cloud agent Automations — specifically automated issue triage and nightly test regression fixing.

## What it does

- Validates column presence against an expected schema
- Flags null rates above configurable thresholds
- Detects type mismatches between expected and actual column dtypes
- Reports drift when numeric column distributions shift beyond a defined threshold

## Project structure

```
data-quality-monitor/
├── validator.py            # Core quality check logic
├── test_validator.py       # Unit tests
├── requirements.txt        # Dependencies
└── .github/
    ├── copilot-instructions.md       # Custom instructions for cloud agent
    └── automations/
        ├── issue-triage.yml          # Auto-label new issues
        └── nightly-test-fix.yml      # Nightly failing test repair
```

## Setup

```bash
pip install -r requirements.txt
```

## Running tests

```bash
pytest test_validator.py -v
```

## GitHub Copilot Automations

This repo uses two Copilot cloud agent automations:

**Issue Triage** — triggers when a new issue is opened. Copilot reads the content and applies one of four labels: `bug`, `enhancement`, `data-schema`, or `needs-clarification`, with a comment explaining the call.

**Nightly Test Fix** — runs every night at 2am UTC. Checks the main branch for failing unit tests, attempts a fix, and opens a draft PR if any failures are found.

See `.github/automations/` for the configuration files.
