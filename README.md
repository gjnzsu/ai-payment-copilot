# AI Payment Copilot PoC

A greenfield Streamlit prototype for payment operations teams investigating failed or
rejected `pacs.008` payments.

## What It Shows

- A payment investigation workspace with two mock exception cases.
- Deterministic validation and exception classification.
- Lightweight rule knowledge retrieval over mock payment rules.
- Mock operational log lookup.
- An agentic investigation workflow that explains root cause, evidence, and next action.

## Demo Cases

- `CASE-001`: `pacs.008` rejected because creditor account is missing.
- `CASE-002`: `pacs.008` failed because creditor agent BIC is invalid.

## Run

```powershell
uv run streamlit run app.py
```

## Test

```powershell
uv run pytest -q
uv run ruff check .
```
