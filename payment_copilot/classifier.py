from __future__ import annotations

from payment_copilot.models import Classification, PaymentCase


def classify_exception(case: PaymentCase) -> Classification:
    text = " ".join(
        [
            case.raw_exception,
            case.status,
            case.creditor_agent_bic,
            case.creditor_account or "",
        ]
    ).lower()

    if "creditoraccount" in text or "creditor account" in text or not case.creditor_account:
        return Classification(
            code="MISSING_CREDITOR_ACCOUNT",
            category="Validation",
            severity="High",
            summary="Missing creditor account prevents pacs.008 validation.",
        )

    if "bic" in text or "bicfi" in text or "directory" in text:
        return Classification(
            code="INVALID_CREDITOR_AGENT_BIC",
            category="Routing",
            severity="High",
            summary="Invalid creditor agent BIC prevents payment routing.",
        )

    return Classification(
        code="UNKNOWN_PAYMENT_EXCEPTION",
        category="Unknown",
        severity="Medium",
        summary="The payment exception does not match a known PoC pattern.",
    )
