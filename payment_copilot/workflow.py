from __future__ import annotations

from payment_copilot.classifier import classify_exception
from payment_copilot.llm import polish_explanation
from payment_copilot.models import (
    Diagnosis,
    Evidence,
    InvestigationStep,
    PaymentCase,
    RecommendedAction,
)
from payment_copilot.rag import retrieve_rule_knowledge
from payment_copilot.tools import query_payment_logs


def investigate_payment(case: PaymentCase) -> Diagnosis:
    classification = classify_exception(case)
    rules = retrieve_rule_knowledge(case, limit=2, classification_code=classification.code)
    logs = query_payment_logs(case.payment_id)
    evidence = _build_evidence(rules, logs)
    root_cause = _root_cause(classification.code)
    action = _recommended_action(classification.code)

    timeline = [
        InvestigationStep(
            name="Classify exception",
            status="Complete",
            detail=f"{classification.category}: {classification.summary}",
        ),
        InvestigationStep(
            name="Retrieve rule knowledge",
            status="Complete",
            detail=f"Found {len(rules)} matching rule reference(s).",
        ),
        InvestigationStep(
            name="Query payment logs",
            status="Complete",
            detail=f"Found {len(logs)} operational log event(s).",
        ),
        InvestigationStep(
            name="Recommend next action",
            status="Complete",
            detail=f"{action.action_type}: {action.description}",
        ),
    ]

    deterministic_explanation = (
        f"{root_cause} The diagnosis is based on {len(evidence)} evidence item(s) "
        f"from rules and mock operational logs."
    )
    explanation, explanation_source = polish_explanation(deterministic_explanation)
    return Diagnosis(
        case=case,
        classification=classification,
        root_cause=root_cause,
        evidence=evidence,
        recommended_action=action,
        timeline=timeline,
        explanation=explanation,
        explanation_source=explanation_source,
    )


def _build_evidence(rules, logs) -> list[Evidence]:
    evidence = [
        Evidence(source="Rule Knowledge", reference=rule.rule_id, detail=rule.body)
        for rule in rules
    ]
    evidence.extend(
        Evidence(
            source=f"Mock Log: {event.system}",
            reference=event.timestamp,
            detail=event.message,
        )
        for event in logs
    )
    return evidence


def _root_cause(code: str) -> str:
    if code == "MISSING_CREDITOR_ACCOUNT":
        return "Creditor account is missing from the pacs.008 message."
    if code == "INVALID_CREDITOR_AGENT_BIC":
        return "Creditor agent BIC is invalid or absent from active bank reference data."
    return "The payment failure does not match a known PoC root cause."


def _recommended_action(code: str) -> RecommendedAction:
    if code == "MISSING_CREDITOR_ACCOUNT":
        return RecommendedAction(
            action_type="Repair",
            description=(
                "Populate creditor account from the source instruction, "
                "then resubmit the pacs.008."
            ),
            owner="Payment repair analyst",
        )
    if code == "INVALID_CREDITOR_AGENT_BIC":
        return RecommendedAction(
            action_type="Escalate",
            description=(
                "Escalate to bank reference data operations to validate the BIC "
                "before retry."
            ),
            owner="Reference data operations",
        )
    return RecommendedAction(
        action_type="Review",
        description="Route the payment to a senior operations analyst for manual investigation.",
        owner="Payment operations lead",
    )
