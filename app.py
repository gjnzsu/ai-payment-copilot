from __future__ import annotations

import os

import streamlit as st

from payment_copilot.mock_data import list_cases
from payment_copilot.workflow import investigate_payment

st.set_page_config(
    page_title="AI Payment Copilot",
    layout="wide",
)


def main() -> None:
    cases = list_cases()
    case_by_label = {
        f"{case.case_id} - {case.status} - {case.creditor_name}": case for case in cases
    }

    st.title("AI Payment Copilot")
    st.caption("PoC workspace for diagnosing failed or rejected pacs.008 payments.")

    with st.sidebar:
        st.header("Cases")
        selected_label = st.radio(
            "Payment exceptions",
            options=list(case_by_label.keys()),
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("PoC mode")
        st.write("Mock data only")
        st.write("Deterministic diagnosis")
        if os.getenv("OPENAI_API_KEY"):
            st.write("LLM polishing available")
        else:
            st.write("LLM polishing inactive")

    case = case_by_label[selected_label]
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
            [
                {"Field": "Payment ID", "Value": case.payment_id},
                {"Field": "Submitted", "Value": case.submitted_at},
                {"Field": "Amount", "Value": case.amount},
                {"Field": "Debtor", "Value": case.debtor_name},
                {"Field": "Debtor Agent BIC", "Value": case.debtor_agent_bic},
                {"Field": "Creditor", "Value": case.creditor_name},
                {"Field": "Creditor Agent BIC", "Value": case.creditor_agent_bic},
                {"Field": "Creditor Account", "Value": case.creditor_account or "Missing"},
            ],
            hide_index=True,
            use_container_width=True,
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
