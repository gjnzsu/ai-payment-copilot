from __future__ import annotations

import re

from payment_copilot.mock_data import RULE_KNOWLEDGE
from payment_copilot.models import PaymentCase, RuleKnowledge


def retrieve_rule_knowledge(case: PaymentCase, limit: int = 3) -> list[RuleKnowledge]:
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

    ranked = sorted(
        RULE_KNOWLEDGE,
        key=lambda rule: _score(rule, query_terms),
        reverse=True,
    )
    return [rule for rule in ranked if _score(rule, query_terms) > 0][:limit]


def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9.]+", text.lower()))


def _score(rule: RuleKnowledge, query_terms: set[str]) -> int:
    keyword_matches = sum(1 for keyword in rule.keywords if keyword.lower() in query_terms)
    body_terms = _terms(f"{rule.title} {rule.body}")
    body_matches = len(query_terms.intersection(body_terms))
    return keyword_matches * 3 + body_matches
