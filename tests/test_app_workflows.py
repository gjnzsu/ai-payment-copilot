from streamlit.testing.v1 import AppTest


def _run_app() -> AppTest:
    return AppTest.from_file("app.py").run(timeout=30)


def test_app_uses_separate_top_level_workflow_tabs_with_stable_selector_keys():
    app = _run_app()

    assert [tab.label for tab in app.tabs] == [
        "Draft Payment Workflow",
        "Payment Exception Workflow",
    ]
    assert app.tabs[0].selectbox[0].key == "draft_payment_selector"
    assert app.tabs[1].selectbox[0].key == "payment_exception_selector"


def test_app_scopes_selectors_and_rendered_content_to_each_workflow():
    app = _run_app()

    draft_tab = app.tabs[0]
    exception_tab = app.tabs[1]

    assert all(option.startswith("DRAFT-") for option in draft_tab.selectbox[0].options)
    assert all(option.startswith("CASE-") for option in exception_tab.selectbox[0].options)
    assert [caption.value for caption in draft_tab.caption[:1]] == [
        "Use this workflow before payment submission."
    ]
    assert [caption.value for caption in exception_tab.caption[:1]] == [
        "Use this workflow after a payment is rejected or failed."
    ]
    assert [subheader.value for subheader in draft_tab.subheader] == [
        "DRAFT-001: pacs.008 Draft Pre-Validation",
        "DRAFT-001: Rail Recommendation",
    ]
    assert [subheader.value for subheader in exception_tab.subheader] == [
        "CASE-001: pacs.008 Rejected"
    ]


def test_app_switches_ready_draft_to_wire_without_changing_exception_workflow():
    app = _run_app()

    app.tabs[0].selectbox[0].set_value(
        "DRAFT-003 - pacs.008 - Harbor Medical Supplies"
    ).run(timeout=30)

    assert [subheader.value for subheader in app.tabs[0].subheader] == [
        "DRAFT-003: pacs.008 Draft Pre-Validation",
        "DRAFT-003: Rail Recommendation",
    ]
    assert any("Wire Payment is recommended" in item.value for item in app.tabs[0].markdown)
    assert [subheader.value for subheader in app.tabs[1].subheader] == [
        "CASE-001: pacs.008 Rejected"
    ]


def test_app_switches_exception_without_changing_draft_workflow():
    app = _run_app()

    app.tabs[1].selectbox[0].set_value("CASE-002 - Failed - Novara Pharma SRL").run(
        timeout=30
    )

    assert [subheader.value for subheader in app.tabs[1].subheader] == [
        "CASE-002: pacs.008 Failed"
    ]
    assert any(
        "Creditor agent BIC is invalid" in item.value for item in app.tabs[1].info
    )
    assert [subheader.value for subheader in app.tabs[0].subheader] == [
        "DRAFT-001: pacs.008 Draft Pre-Validation",
        "DRAFT-001: Rail Recommendation",
    ]
