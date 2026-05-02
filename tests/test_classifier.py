from payment_copilot.classifier import classify_exception
from payment_copilot.mock_data import get_case


def test_missing_creditor_account_case_classifies_as_validation_exception():
    case = get_case("CASE-001")

    result = classify_exception(case)

    assert result.code == "MISSING_CREDITOR_ACCOUNT"
    assert result.category == "Validation"
    assert "creditor account" in result.summary.lower()


def test_invalid_creditor_agent_bic_case_classifies_as_routing_exception():
    case = get_case("CASE-002")

    result = classify_exception(case)

    assert result.code == "INVALID_CREDITOR_AGENT_BIC"
    assert result.category == "Routing"
    assert "bic" in result.summary.lower()
