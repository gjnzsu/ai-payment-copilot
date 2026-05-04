# AI Payment Copilot PoC

A greenfield Streamlit prototype for payment operations teams pre-validating draft
`pacs.008` payments, recommending payment rails, and investigating failed or
rejected payments.

## What It Shows

- A pre-submit validation workspace for draft `pacs.008` payments.
- Suggest-only repair recommendations for predicted validation and routing defects.
- A deterministic payment rail recommendation workspace for ready draft payments.
- A payment investigation workspace with two mock exception cases.
- Deterministic validation and exception classification.
- Lightweight rule knowledge retrieval over mock payment rules.
- Mock operational log lookup.
- An agentic investigation workflow that explains root cause, evidence, and next action.

## Demo Cases

- `DRAFT-001`: draft `pacs.008` would fail because creditor account is missing.
- `DRAFT-002`: draft `pacs.008` would fail because creditor agent BIC is invalid.
- `DRAFT-003`: valid high-value domestic USD draft recommended for wire payment.
- `CASE-001`: `pacs.008` rejected because creditor account is missing.
- `CASE-002`: `pacs.008` failed because creditor agent BIC is invalid.

## PoC Scope

- Pre-validation is shown in a dedicated Streamlit tab beside exception investigation.
- Repair is suggest-only; the PoC does not mutate or auto-repair draft payments.
- Rule scope is limited to missing creditor account and invalid creditor agent BIC.
- Rail recommendation is mock-data only and compares Wire, RTP, ACH, SEPA, and SWIFT.

## Run

```powershell
uv run streamlit run app.py
```

## Test

```powershell
uv run pytest -q
uv run ruff check .
```
