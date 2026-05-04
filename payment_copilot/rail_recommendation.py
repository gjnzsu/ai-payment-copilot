from __future__ import annotations

from dataclasses import dataclass

from payment_copilot.models import PaymentCase, RailRecommendation, RailRecommendationResult
from payment_copilot.prevalidation import prevalidate_payment


@dataclass(frozen=True)
class RailProfile:
    rail_id: str
    name: str
    fee: str
    settlement_time: str
    supported_currencies: tuple[str, ...]
    max_amount: float | None
    domestic_only: bool
    base_score: int


RAIL_PROFILES: tuple[RailProfile, ...] = (
    RailProfile(
        rail_id="WIRE",
        name="Wire Payment",
        fee="High",
        settlement_time="Same business day",
        supported_currencies=("USD",),
        max_amount=None,
        domestic_only=True,
        base_score=88,
    ),
    RailProfile(
        rail_id="RTP",
        name="Real-Time Payments",
        fee="Medium",
        settlement_time="Seconds, 24/7",
        supported_currencies=("USD",),
        max_amount=100_000.00,
        domestic_only=True,
        base_score=86,
    ),
    RailProfile(
        rail_id="ACH",
        name="ACH",
        fee="Low",
        settlement_time="1-2 business days",
        supported_currencies=("USD",),
        max_amount=1_000_000.00,
        domestic_only=True,
        base_score=72,
    ),
    RailProfile(
        rail_id="SEPA",
        name="SEPA Credit Transfer",
        fee="Low",
        settlement_time="Same or next business day",
        supported_currencies=("EUR",),
        max_amount=None,
        domestic_only=False,
        base_score=80,
    ),
    RailProfile(
        rail_id="SWIFT",
        name="SWIFT",
        fee="High",
        settlement_time="1-3 business days",
        supported_currencies=("USD", "EUR"),
        max_amount=None,
        domestic_only=False,
        base_score=64,
    ),
)


def recommend_payment_rails(case: PaymentCase) -> RailRecommendationResult:
    validation = prevalidate_payment(case)
    if validation.status != "Ready":
        return RailRecommendationResult(
            case=case,
            status="Blocked",
            summary="Repair validation issues before recommending a payment rail.",
            recommendations=[],
        )

    recommendations = [_score_rail(profile, case) for profile in RAIL_PROFILES]
    recommendations.sort(key=lambda item: (item.eligible, item.score), reverse=True)
    top = recommendations[0]
    return RailRecommendationResult(
        case=case,
        status="Recommended",
        summary=f"{top.name} is recommended for this draft payment.",
        recommendations=recommendations,
    )


def _score_rail(profile: RailProfile, case: PaymentCase) -> RailRecommendation:
    currency, amount = _parse_amount(case.amount)
    debtor_country = _bic_country(case.debtor_agent_bic)
    creditor_country = _bic_country(case.creditor_agent_bic)
    is_domestic = debtor_country == creditor_country
    reasons: list[str] = []
    eligible = True
    score = profile.base_score

    if currency not in profile.supported_currencies:
        eligible = False
        score = 0
        reasons.append(f"{profile.name} does not support {currency} in this PoC.")

    if profile.domestic_only and not is_domestic:
        eligible = False
        score = 0
        reasons.append(f"{profile.name} is modeled as domestic-only.")

    if profile.max_amount is not None and amount > profile.max_amount:
        eligible = False
        score = 0
        reasons.append(
            f"Payment amount exceeds {profile.rail_id} limit of {profile.max_amount:,.0f}."
        )

    if eligible:
        reasons.extend(_eligible_reasons(profile, currency, amount, is_domestic))

    return RailRecommendation(
        rail_id=profile.rail_id,
        name=profile.name,
        eligible=eligible,
        score=score,
        fee=profile.fee,
        settlement_time=profile.settlement_time,
        rationale=" ".join(reasons),
        reasons=reasons,
    )


def _eligible_reasons(
    profile: RailProfile,
    currency: str,
    amount: float,
    is_domestic: bool,
) -> list[str]:
    if profile.rail_id == "WIRE":
        return [
            f"Best fit for high-value domestic {currency} payments.",
            "Supports same-business-day bank transfer with strong operational familiarity.",
        ]
    if profile.rail_id == "RTP":
        return [
            "Fastest settlement option for eligible domestic payments.",
            "Best when immediate finality is more important than limit flexibility.",
        ]
    if profile.rail_id == "ACH":
        return [
            "Lower-cost domestic option.",
            "Best when settlement speed is less urgent.",
        ]
    if profile.rail_id == "SEPA":
        return [
            "Strong fit for EUR regional payments.",
            "Lower cost than correspondent-bank routes in supported markets.",
        ]
    if profile.rail_id == "SWIFT":
        if is_domestic:
            return [
                f"Can carry {currency} payment instructions but is not optimal domestically.",
                "Better suited to cross-border correspondent banking scenarios.",
            ]
        return [
            "Broadest global reach for cross-border bank payments.",
            "Useful when local or instant rails are unavailable.",
        ]
    return [f"Eligible for {amount:,.2f} {currency} payment."]


def _parse_amount(amount: str) -> tuple[str, float]:
    currency, raw_value = amount.split(" ", maxsplit=1)
    return currency, float(raw_value.replace(",", ""))


def _bic_country(bic: str) -> str:
    return bic[4:6]
