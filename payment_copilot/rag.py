from __future__ import annotations

import re

from payment_copilot.mock_data import RULE_KNOWLEDGE
from payment_copilot.models import PaymentCase, RuleKnowledge

CLASSIFICATION_RULES = {
    "MISSING_CREDITOR_ACCOUNT": {"RULE-PACS008-CDTR-ACCT"},
    "INVALID_CREDITOR_AGENT_BIC": {"RULE-PACS008-CDTR-AGT-BIC"},
}


def retrieve_rule_knowledge(
    case: PaymentCase,
    limit: int = 3,
    classification_code: str | None = None,
) -> list[RuleKnowledge]:
    query_terms = _terms(
        " ".join(
            [
                case.message_type,
                case.raw_exception,
                case.status,
                case.creditor_agent_bic,
                case.creditor_account or "",
            ]
        )
    )

    candidate_rules = _candidate_rules(classification_code)
    ranked = sorted(
        candidate_rules,
        key=lambda rule: _score(rule, query_terms),
        reverse=True,
    )
    return [rule for rule in ranked if _score(rule, query_terms) > 0][:limit]


def _candidate_rules(classification_code: str | None) -> list[RuleKnowledge]:
    if not classification_code:
        return list(RULE_KNOWLEDGE)

    allowed_rule_ids = CLASSIFICATION_RULES.get(classification_code)
    if not allowed_rule_ids:
        return list(RULE_KNOWLEDGE)

    return [rule for rule in RULE_KNOWLEDGE if rule.rule_id in allowed_rule_ids]


def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9.]+", text.lower()))


def _score(rule: RuleKnowledge, query_terms: set[str]) -> int:
    keyword_matches = sum(1 for keyword in rule.keywords if keyword.lower() in query_terms)
    body_terms = _terms(f"{rule.title} {rule.body}")
    body_matches = len(query_terms.intersection(body_terms))
    return keyword_matches * 3 + body_matches
