from payment_copilot.tools import query_payment_logs


def test_log_query_returns_events_for_matching_payment_id():
    events = query_payment_logs("PMT-2026-0001")

    assert len(events) >= 2
    assert all(event.payment_id == "PMT-2026-0001" for event in events)
    assert any("creditor account" in event.message.lower() for event in events)


def test_log_query_returns_empty_list_for_unknown_payment_id():
    assert query_payment_logs("PMT-UNKNOWN") == []
