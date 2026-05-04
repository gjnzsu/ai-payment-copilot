from __future__ import annotations

from payment_copilot.models import LogEvent, PaymentCase, RuleKnowledge

PAYMENT_CASES: tuple[PaymentCase, ...] = (
    PaymentCase(
        case_id="CASE-001",
        payment_id="PMT-2026-0001",
        message_type="pacs.008",
        status="Rejected",
        amount="USD 125,000.00",
        debtor_name="Northstar Trading LLC",
        debtor_agent_bic="BOFAUS3NXXX",
        creditor_name="Alpine Components AG",
        creditor_agent_bic="DEUTDEFFXXX",
        creditor_account=None,
        raw_exception="RJCT: CreditorAccount/Id is mandatory for pacs.008 credit transfer.",
        submitted_at="2026-05-02T09:12:18+08:00",
    ),
    PaymentCase(
        case_id="CASE-002",
        payment_id="PMT-2026-0002",
        message_type="pacs.008",
        status="Failed",
        amount="EUR 42,700.00",
        debtor_name="Harbor Medical Supplies",
        debtor_agent_bic="CHASUS33XXX",
        creditor_name="Novara Pharma SRL",
        creditor_agent_bic="ZZZZDE00XXX",
        creditor_account="DE89370400440532013000",
        raw_exception="FAIL: CreditorAgent/FinInstnId/BICFI failed directory validation.",
        submitted_at="2026-05-02T10:03:44+08:00",
    ),
)


DRAFT_PAYMENTS: tuple[PaymentCase, ...] = (
    PaymentCase(
        case_id="DRAFT-001",
        payment_id="PMT-DRAFT-0001",
        message_type="pacs.008",
        status="Draft",
        amount="USD 125,000.00",
        debtor_name="Northstar Trading LLC",
        debtor_agent_bic="BOFAUS3NXXX",
        creditor_name="Alpine Components AG",
        creditor_agent_bic="DEUTDEFFXXX",
        creditor_account=None,
        raw_exception="Draft pacs.008 pending pre-submit validation.",
        submitted_at="Not submitted",
    ),
    PaymentCase(
        case_id="DRAFT-002",
        payment_id="PMT-DRAFT-0002",
        message_type="pacs.008",
        status="Draft",
        amount="EUR 42,700.00",
        debtor_name="Harbor Medical Supplies",
        debtor_agent_bic="CHASUS33XXX",
        creditor_name="Novara Pharma SRL",
        creditor_agent_bic="ZZZZDE00XXX",
        creditor_account="DE89370400440532013000",
        raw_exception="Draft pacs.008 pending pre-submit validation.",
        submitted_at="Not submitted",
    ),
    PaymentCase(
        case_id="DRAFT-003",
        payment_id="PMT-DRAFT-0003",
        message_type="pacs.008",
        status="Draft",
        amount="USD 250,000.00",
        debtor_name="Northstar Trading LLC",
        debtor_agent_bic="BOFAUS3NXXX",
        creditor_name="Harbor Medical Supplies",
        creditor_agent_bic="CHASUS33XXX",
        creditor_account="US123456789000111222333",
        raw_exception="Draft pacs.008 ready for rail recommendation.",
        submitted_at="Not submitted",
    ),
)


ACTIVE_CREDITOR_AGENT_BICS: tuple[str, ...] = (
    "DEUTDEFFXXX",
    "CHASUS33XXX",
)


RULE_KNOWLEDGE: tuple[RuleKnowledge, ...] = (
    RuleKnowledge(
        rule_id="RULE-PACS008-CDTR-ACCT",
        title="pacs.008 creditor account requirement",
        body=(
            "A pacs.008 customer credit transfer must include a creditor account "
            "identifier when the beneficiary account is required by the receiving "
            "scheme. Missing CreditorAccount/Id is a repairable validation defect."
        ),
        keywords=("pacs.008", "creditor", "account", "missing", "mandatory", "repair"),
    ),
    RuleKnowledge(
        rule_id="RULE-PACS008-CDTR-AGT-BIC",
        title="pacs.008 creditor agent BIC validation",
        body=(
            "CreditorAgent/FinInstnId/BICFI must be a valid and reachable BIC in "
            "bank reference data. Invalid BIC values should be checked against the "
            "directory before retrying or escalated to reference data operations."
        ),
        keywords=("pacs.008", "creditor", "agent", "bic", "invalid", "directory"),
    ),
)


LOG_EVENTS: tuple[LogEvent, ...] = (
    LogEvent(
        timestamp="2026-05-02T09:12:19+08:00",
        payment_id="PMT-2026-0001",
        system="payment-validator",
        level="ERROR",
        message="Validation rejected pacs.008: creditor account identifier is missing.",
    ),
    LogEvent(
        timestamp="2026-05-02T09:12:20+08:00",
        payment_id="PMT-2026-0001",
        system="repair-queue",
        level="INFO",
        message="Payment routed to manual repair queue with field path CdtrAcct/Id.",
    ),
    LogEvent(
        timestamp="2026-05-02T10:03:46+08:00",
        payment_id="PMT-2026-0002",
        system="bic-directory",
        level="ERROR",
        message="BIC ZZZZDE00XXX not found in active creditor agent directory.",
    ),
    LogEvent(
        timestamp="2026-05-02T10:03:48+08:00",
        payment_id="PMT-2026-0002",
        system="payment-orchestrator",
        level="WARN",
        message="Retry suppressed because creditor agent BIC failed reference validation.",
    ),
)


def list_cases() -> list[PaymentCase]:
    return list(PAYMENT_CASES)


def list_draft_payments() -> list[PaymentCase]:
    return list(DRAFT_PAYMENTS)


def get_case(case_id: str) -> PaymentCase:
    for case in PAYMENT_CASES:
        if case.case_id == case_id:
            return case
    raise KeyError(f"Unknown case id: {case_id}")


def get_draft_payment(case_id: str) -> PaymentCase:
    for case in DRAFT_PAYMENTS:
        if case.case_id == case_id:
            return case
    raise KeyError(f"Unknown draft payment id: {case_id}")
