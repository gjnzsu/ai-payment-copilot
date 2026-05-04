from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PaymentCase:
    case_id: str
    payment_id: str
    message_type: str
    status: str
    amount: str
    debtor_name: str
    debtor_agent_bic: str
    creditor_name: str
    creditor_agent_bic: str
    creditor_account: str | None
    raw_exception: str
    submitted_at: str


@dataclass(frozen=True)
class Classification:
    code: str
    category: str
    severity: str
    summary: str


@dataclass(frozen=True)
class RuleKnowledge:
    rule_id: str
    title: str
    body: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class LogEvent:
    timestamp: str
    payment_id: str
    system: str
    level: str
    message: str


@dataclass(frozen=True)
class Evidence:
    source: str
    reference: str
    detail: str


@dataclass(frozen=True)
class RecommendedAction:
    action_type: str
    description: str
    owner: str


@dataclass(frozen=True)
class InvestigationStep:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    field_path: str
    explanation: str
    repair_suggestion: str


@dataclass(frozen=True)
class PreValidationResult:
    case: PaymentCase
    status: str
    issues: list[ValidationIssue]
    evidence: list[Evidence]


@dataclass(frozen=True)
class Diagnosis:
    case: PaymentCase
    classification: Classification
    root_cause: str
    evidence: list[Evidence]
    recommended_action: RecommendedAction
    timeline: list[InvestigationStep] = field(default_factory=list)
    explanation: str = ""
    explanation_source: str = "Deterministic"
