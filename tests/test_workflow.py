from payment_copilot.mock_data import get_case
from payment_copilot.workflow import investigate_payment


def test_workflow_diagnoses_missing_creditor_account_with_evidence_and_action():
    diagnosis = investigate_payment(get_case("CASE-001"))

    assert diagnosis.classification.code == "MISSING_CREDITOR_ACCOUNT"
    assert "Creditor account is missing" in diagnosis.root_cause
    assert diagnosis.evidence
    assert diagnosis.recommended_action.action_type == "Repair"
    assert "populate creditor account" in diagnosis.recommended_action.description.lower()


def test_workflow_diagnoses_invalid_bic_with_evidence_and_action():
    diagnosis = investigate_payment(get_case("CASE-002"))

    assert diagnosis.classification.code == "INVALID_CREDITOR_AGENT_BIC"
    assert "Creditor agent BIC is invalid" in diagnosis.root_cause
    assert diagnosis.evidence
    assert diagnosis.recommended_action.action_type == "Escalate"
    assert "bank reference data" in diagnosis.recommended_action.description.lower()


def test_workflow_uses_deterministic_explanation_when_llm_is_not_configured(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    diagnosis = investigate_payment(get_case("CASE-001"))

    assert diagnosis.explanation_source == "Deterministic"
    assert "evidence item" in diagnosis.explanation
