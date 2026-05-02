from __future__ import annotations

from payment_copilot.mock_data import LOG_EVENTS
from payment_copilot.models import LogEvent


def query_payment_logs(payment_id: str) -> list[LogEvent]:
    return [event for event in LOG_EVENTS if event.payment_id == payment_id]
