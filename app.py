from __future__ import annotations

import os

import streamlit as st

from payment_copilot.mock_data import list_cases, list_draft_payments
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
    case_by_label = {
        f"{case.case_id} - {case.status} - {case.creditor_name}": case for case in cases
    }
    draft_by_label = {
        f"{case.case_id} - {case.message_type} - {case.creditor_name}": case
        for case in draft_payments
    }

    st.title("AI Payment Copilot")
    st.caption(
        "PoC workspace for pre-validating draft pacs.008 payments, recommending rails, "
        "and investigating exceptions."
    )

    with st.sidebar:
        st.header("Demo Data")
        selected_draft_label = st.radio(
            "Draft payments",
            options=list(draft_by_label.keys()),
        )
        st.divider()
        selected_case_label = st.radio(
            "Payment exceptions",
            options=list(case_by_label.keys()),
        )
        st.divider()
        st.caption("PoC mode")
        st.write("Mock data only")
        st.write("Deterministic pre-validation, rail advice, and diagnosis")
        if os.getenv("OPENAI_API_KEY"):
            st.write("LLM polishing available")
        else:
            st.write("LLM polishing inactive")

    prevalidation_tab, rail_tab, investigation_tab = st.tabs(
        ["Pre-Validation", "Rail Recommendation", "Exception Investigation"]
    )

    with prevalidation_tab:
        _render_prevalidation(draft_by_label[selected_draft_label])

    with rail_tab:
        _render_rail_recommendation(draft_by_label[selected_draft_label])

    with investigation_tab:
        _render_investigation(case_by_label[selected_case_label])


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


def _render_prevalidation(case: PaymentCase) -> None:
    result = prevalidate_payment(case)

    st.subheader(f"{case.case_id}: {case.message_type} Draft Pre-Validation")
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
        st.success("No validation defects detected. This draft is ready for rail selection.")

    st.markdown("### Supporting Rule Evidence")
    if result.evidence:
        for item in result.evidence:
            with st.container(border=True):
                st.caption(f"{item.source} - {item.reference}")
                st.write(item.detail)
    else:
        st.caption("No repair rule evidence needed for a ready draft.")


def _render_rail_recommendation(case: PaymentCase) -> None:
    result = recommend_payment_rails(case)

    st.subheader(f"{case.case_id}: Rail Recommendation")
    st.write(result.summary)

    if result.status == "Blocked":
        st.warning("Resolve pre-validation repair items before selecting a payment rail.")
        return

    top = result.recommendations[0]
    top_left, top_right = st.columns([2, 1])
    with top_left:
        st.markdown("### Recommended Rail")
        st.success(f"{top.name}: {top.rationale}")
    with top_right:
        st.metric("Top Score", top.score)
        st.metric("Settlement", top.settlement_time)

    st.markdown("### Rail Ranking")
    st.dataframe(
        [
            {
                "Rail": option.name,
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
