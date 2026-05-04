from __future__ import annotations

from payment_copilot.mock_data import ACTIVE_CREDITOR_AGENT_BICS
from payment_copilot.models import Evidence, PaymentCase, PreValidationResult, ValidationIssue
from payment_copilot.rag import retrieve_rule_knowledge


def prevalidate_payment(case: PaymentCase) -> PreValidationResult:
    issues = _detect_issues(case)
    evidence = _build_evidence(case, issues)
    status = "Needs Repair" if issues else "Ready"

    return PreValidationResult(
        case=case,
        status=status,
        issues=issues,
        evidence=evidence,
    )


def _detect_issues(case: PaymentCase) -> list[ValidationIssue]:
    if not case.creditor_account:
        return [
            ValidationIssue(
                code="MISSING_CREDITOR_ACCOUNT",
                severity="High",
                field_path="CdtrAcct/Id",
                explanation="The draft pacs.008 is missing the creditor account identifier.",
                repair_suggestion=(
                    "Populate creditor account from the source instruction before submission."
                ),
            )
        ]

    if case.creditor_agent_bic not in ACTIVE_CREDITOR_AGENT_BICS:
        return [
            ValidationIssue(
                code="INVALID_CREDITOR_AGENT_BIC",
                severity="High",
                field_path="CdtrAgt/FinInstnId/BICFI",
                explanation=(
                    "The creditor agent BIC is not present in active bank reference data."
                ),
                repair_suggestion=(
                    "Validate the creditor agent BIC with reference data operations before "
                    "submission."
                ),
            )
        ]

    return []


def _build_evidence(case: PaymentCase, issues: list[ValidationIssue]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for issue in issues:
        rules = retrieve_rule_knowledge(case, limit=1, classification_code=issue.code)
        evidence.extend(
            Evidence(source="Rule Knowledge", reference=rule.rule_id, detail=rule.body)
            for rule in rules
        )
    return evidence
