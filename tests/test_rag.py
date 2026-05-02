from payment_copilot.mock_data import get_case
from payment_copilot.rag import retrieve_rule_knowledge


def test_missing_creditor_account_retrieves_account_rule():
    case = get_case("CASE-001")

    rules = retrieve_rule_knowledge(case, limit=2)

    assert rules
    assert rules[0].rule_id == "RULE-PACS008-CDTR-ACCT"
    assert "creditor account" in rules[0].title.lower()


def test_invalid_bic_retrieves_bic_rule():
    case = get_case("CASE-002")

    rules = retrieve_rule_knowledge(case, limit=2)

    assert rules
    assert rules[0].rule_id == "RULE-PACS008-CDTR-AGT-BIC"
    assert "bic" in rules[0].title.lower()
