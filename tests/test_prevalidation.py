from payment_copilot.mock_data import get_draft_payment
from payment_copilot.prevalidation import prevalidate_payment


def test_missing_creditor_account_draft_needs_repair_with_field_path_and_suggestion():
    result = prevalidate_payment(get_draft_payment("DRAFT-001"))

    assert result.status == "Needs Repair"
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.code == "MISSING_CREDITOR_ACCOUNT"
    assert issue.field_path == "CdtrAcct/Id"
    assert "populate creditor account" in issue.repair_suggestion.lower()


def test_invalid_creditor_agent_bic_draft_needs_repair_with_reference_data_guidance():
    result = prevalidate_payment(get_draft_payment("DRAFT-002"))

    assert result.status == "Needs Repair"
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.code == "INVALID_CREDITOR_AGENT_BIC"
    assert issue.field_path == "CdtrAgt/FinInstnId/BICFI"
    assert "reference data" in issue.repair_suggestion.lower()


def test_prevalidation_evidence_only_includes_rule_relevant_to_detected_issue():
    result = prevalidate_payment(get_draft_payment("DRAFT-001"))

    rule_references = [
        item.reference for item in result.evidence if item.source == "Rule Knowledge"
    ]

    assert rule_references == ["RULE-PACS008-CDTR-ACCT"]


def test_valid_draft_is_ready_for_submission():
    result = prevalidate_payment(get_draft_payment("DRAFT-003"))

    assert result.status == "Ready"
    assert result.issues == []
    assert result.evidence == []
