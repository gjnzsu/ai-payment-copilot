from __future__ import annotations

import os
from dataclasses import replace

import streamlit as st

from payment_copilot.mock_data import ACTIVE_CREDITOR_AGENT_BICS, list_cases, list_draft_payments
from payment_copilot.models import PaymentCase
from payment_copilot.prevalidation import prevalidate_payment
from payment_copilot.rail_recommendation import recommend_payment_rails
from payment_copilot.workflow import investigate_payment

st.set_page_config(
    page_title="AI Payment Copilot",
    layout="wide",
)


def main() -> None:
    cases = list_cases()
    draft_payments = list_draft_payments()
    exception_cases = [case for case in cases if case.case_id.startswith("CASE-")]
    draft_cases = [
        case for case in draft_payments if case.case_id.startswith("DRAFT-")
    ]
    case_by_label = {
        f"{case.case_id} - {case.status} - {case.creditor_name}": case
        for case in exception_cases
    }
    draft_by_label = {
        f"{case.case_id} - {case.message_type} - {case.creditor_name}": case
        for case in draft_cases
    }
    st.session_state.setdefault("mock_repaired_drafts", {})

    st.title("AI Payment Copilot")
    st.caption(
        "PoC workspace for pre-validating draft pacs.008 payments, applying mock repairs, "
        "recommending schemes / rails, and investigating exceptions."
    )

    with st.sidebar:
        st.header("Demo Data")
        st.caption("PoC mode")
        st.write("Mock data only")
        st.write("Deterministic pre-validation, rail advice, and diagnosis")
        if os.getenv("OPENAI_API_KEY"):
            st.write("LLM polishing available")
        else:
            st.write("LLM polishing inactive")

    draft_workflow_tab, exception_workflow_tab = st.tabs(
        ["Draft Payment Workflow", "Payment Exception Workflow"]
    )

    with draft_workflow_tab:
        st.caption("Use this workflow before payment submission.")
        selected_draft_label = st.selectbox(
            "Draft payment",
            options=list(draft_by_label.keys()),
            key="draft_payment_selector",
        )
        selected_draft = _apply_mock_repair_state(draft_by_label[selected_draft_label])
        validation_result = _render_prevalidation(selected_draft)
        st.divider()
        repaired = _render_repair_step(selected_draft, validation_result)
        st.divider()
        selected_draft = _apply_mock_repair_state(selected_draft) if repaired else selected_draft
        _render_scheme_rail_recommendation(selected_draft)

    with exception_workflow_tab:
        st.caption("Use this workflow after a payment is rejected or failed.")
        selected_case_label = st.selectbox(
            "Payment exception",
            options=list(case_by_label.keys()),
            key="payment_exception_selector",
        )
        selected_case = case_by_label[selected_case_label]
        _render_investigation(selected_case)


def _payment_rows(case: PaymentCase) -> list[dict[str, str]]:
    return [
        {"Field": "Payment ID", "Value": case.payment_id},
        {"Field": "Submitted", "Value": case.submitted_at},
        {"Field": "Amount", "Value": case.amount},
        {"Field": "Debtor", "Value": case.debtor_name},
        {"Field": "Debtor Agent BIC", "Value": case.debtor_agent_bic},
        {"Field": "Creditor", "Value": case.creditor_name},
        {"Field": "Creditor Agent BIC", "Value": case.creditor_agent_bic},
        {"Field": "Creditor Account", "Value": case.creditor_account or "Missing"},
    ]


def _apply_mock_repair_state(case: PaymentCase) -> PaymentCase:
    repaired_values = st.session_state["mock_repaired_drafts"].get(case.case_id)
    if not repaired_values:
        return case
    return replace(case, **repaired_values)


def _mock_repair_values(case: PaymentCase) -> dict[str, str]:
    values: dict[str, str] = {
        "status": "Draft - Mock Repaired",
        "raw_exception": (
            "Mock repair applied. Draft pacs.008 is ready for scheme / rail recommendation."
        ),
    }
    if not case.creditor_account:
        values["creditor_account"] = "MOCK-REPAIRED-CREDITOR-ACCOUNT"
    if case.creditor_agent_bic not in ACTIVE_CREDITOR_AGENT_BICS:
        values["creditor_agent_bic"] = ACTIVE_CREDITOR_AGENT_BICS[0]
    return values


def _render_workflow_progress(current_step: int) -> None:
    labels = [
        "1. Pre-validate",
        "2. Repair",
        "3. Recommend Scheme / Rail",
        "4. Investigate Exception",
    ]
    cols = st.columns(len(labels))
    for index, label in enumerate(labels, start=1):
        with cols[index - 1]:
            if index < current_step:
                st.success(label)
            elif index == current_step:
                st.info(label)
            else:
                st.caption(label)


def _render_prevalidation(case: PaymentCase):
    result = prevalidate_payment(case)

    _render_workflow_progress(1 if result.issues else 3)
    st.subheader(f"{case.case_id}: Step 1 - Pre-validate {case.message_type} Draft")
    st.write(case.raw_exception)

    top_left, top_right = st.columns([2, 1])
    with top_left:
        st.markdown("### Draft Payment Details")
        st.dataframe(
            _payment_rows(case),
            hide_index=True,
            width="stretch",
        )
    with top_right:
        st.metric("Validation Status", result.status)
        if result.issues:
            st.metric("Detected Issues", len(result.issues))
        else:
            st.metric("Detected Issues", 0)

    st.markdown("### Repair Recommendations")
    if result.issues:
        for issue in result.issues:
            with st.container(border=True):
                st.caption(f"{issue.code} - {issue.severity} - {issue.field_path}")
                st.write(issue.explanation)
                st.success(issue.repair_suggestion)
    else:
        st.success(
            "No validation defects detected. This draft is ready for scheme / rail recommendation."
        )

    st.markdown("### Supporting Rule Evidence")
    if result.evidence:
        for item in result.evidence:
            with st.container(border=True):
                st.caption(f"{item.source} - {item.reference}")
                st.write(item.detail)
    else:
        st.caption("No repair rule evidence needed for a ready draft.")

    return result


def _render_repair_step(case: PaymentCase, validation_result) -> bool:
    st.subheader(f"{case.case_id}: Step 2 - Repair Recommendation")

    if not validation_result.issues:
        if case.case_id in st.session_state["mock_repaired_drafts"]:
            st.success("Mock repair applied. This draft is ready for scheme / rail recommendation.")
        else:
            st.success("No repair action required. This draft can continue to recommendation.")
        return False

    st.warning("This is a UI prototype repair action. No payment data is submitted or mutated.")
    for issue in validation_result.issues:
        with st.container(border=True):
            st.caption(f"{issue.code} - {issue.field_path}")
            st.write(issue.repair_suggestion)

    if st.button("Apply Suggested Repair", key=f"apply_repair_{case.case_id}"):
        st.session_state["mock_repaired_drafts"][case.case_id] = _mock_repair_values(case)
        st.success("Mock repair applied. This draft is ready for scheme / rail recommendation.")
        return True
    return False


def _render_scheme_rail_recommendation(case: PaymentCase) -> None:
    result = recommend_payment_rails(case)

    st.subheader(f"{case.case_id}: Step 3 - Scheme / Rail Recommendation")
    st.write(result.summary)

    if result.status == "Blocked":
        st.warning("Resolve repair items before scheme / rail recommendation.")
        return

    top = result.recommendations[0]
    top_left, top_right = st.columns([2, 1])
    with top_left:
        st.markdown("### Recommended Scheme / Rail")
        st.success(f"{top.name}: {top.rationale}")
    with top_right:
        st.metric("Top Score", top.score)
        st.metric("Settlement", top.settlement_time)

    st.markdown("### Scheme / Rail Ranking")
    st.dataframe(
        [
            {
                "Scheme / Rail": option.name,
                "Eligible": "Yes" if option.eligible else "No",
                "Score": option.score,
                "Fee": option.fee,
                "Settlement": option.settlement_time,
                "Rationale": option.rationale,
            }
            for option in result.recommendations
        ],
        hide_index=True,
        width="stretch",
    )

    st.markdown("### Decision Factors")
    for option in result.recommendations:
        with st.expander(f"{option.name} - {'Eligible' if option.eligible else 'Not eligible'}"):
            for reason in option.reasons:
                st.write(reason)


def _render_investigation(case: PaymentCase) -> None:
    diagnosis = investigate_payment(case)

    st.caption(
        "Separate post-failure workflow: this exception case is selected independently "
        "from the draft payment used for pre-validation and rail recommendation."
    )

    top_left, top_right = st.columns([2, 1])
    with top_left:
        st.subheader(f"{case.case_id}: {case.message_type} {case.status}")
        st.write(case.raw_exception)
    with top_right:
        st.metric("Classification", diagnosis.classification.category)
        st.metric("Severity", diagnosis.classification.severity)

    payment_col, diagnosis_col = st.columns([1, 1])
    with payment_col:
        st.markdown("### Payment Details")
        st.dataframe(
            _payment_rows(case),
            hide_index=True,
            width="stretch",
        )

    with diagnosis_col:
        st.markdown("### Root Cause")
        st.info(diagnosis.root_cause)
        st.markdown("### Next Best Action")
        st.success(diagnosis.recommended_action.description)
        st.caption(f"Owner: {diagnosis.recommended_action.owner}")

    st.markdown("### Agentic Investigation Timeline")
    for step in diagnosis.timeline:
        with st.expander(f"{step.name} - {step.status}", expanded=True):
            st.write(step.detail)

    st.markdown("### Evidence")
    for item in diagnosis.evidence:
        with st.container(border=True):
            st.caption(f"{item.source} - {item.reference}")
            st.write(item.detail)

    st.markdown("### Copilot Explanation")
    st.caption(f"Explanation source: {diagnosis.explanation_source}")
    st.write(diagnosis.explanation)


if __name__ == "__main__":
    main()
