from payment_copilot.mock_data import get_draft_payment
from payment_copilot.rail_recommendation import recommend_payment_rails


def test_high_value_ready_usd_draft_recommends_wire_with_rtp_ineligible():
    result = recommend_payment_rails(get_draft_payment("DRAFT-003"))

    assert result.status == "Recommended"
    assert result.recommendations
    assert result.recommendations[0].rail_id == "WIRE"
    assert "high-value domestic USD" in result.recommendations[0].rationale

    rtp_option = next(option for option in result.recommendations if option.rail_id == "RTP")
    assert not rtp_option.eligible
    assert "amount exceeds rtp limit" in rtp_option.rationale.lower()


def test_unrepaired_draft_blocks_rail_recommendation():
    result = recommend_payment_rails(get_draft_payment("DRAFT-001"))

    assert result.status == "Blocked"
    assert result.recommendations == []
    assert "repair" in result.summary.lower()
