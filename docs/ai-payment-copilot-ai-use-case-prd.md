# AI Payment Copilot AI Use Case PRD

## 1. Executive Summary

AI Payment Copilot helps payment operations teams prevent, repair, route, and investigate payment issues before they become costly operational exceptions. The production use case will provide AI-assisted pre-validation, repair recommendation, payment rail recommendation, and exception investigation for `pacs.008` credit transfer workflows. The business goal is to improve straight-through processing, reduce manual repair effort, shorten investigation time, and provide auditable recommendation evidence for operational decisioning.

The current PoC uses mock data and deterministic rules. The production target is a GKE-deployed application that integrates with shared `ai-gateway-service`, `ai-rag-service`, and `ai-sre-observability`, plus enterprise payment systems such as payment hub, bank reference data, rail configuration, operational logs, compliance services, and case management.

## 2. Problem Statement

Payment operations analysts and payment product teams need to process payments accurately, quickly, and safely across multiple rails. Today, missing payment fields, stale reference data, invalid BICs, rail constraints, cutoff misses, and unclear exception evidence can cause payment rejects, failed routing, SLA breaches, manual rework, and delayed customer outcomes.

The pain is highest when analysts must manually inspect ISO 20022 fields, search rule documents, check logs, validate reference data, and decide whether to repair, reroute, escalate, or hold a payment. The business impact includes lower STP rates, higher operations cost, slower exception resolution, and increased operational and compliance risk.

## 3. Target Users

- **Primary user:** Payment operations analyst responsible for reviewing draft or failed payments.
- **Secondary user:** Payment operations lead monitoring exception trends, repair productivity, and recommendation quality.
- **Supporting users:** Reference data operations, compliance operations, SRE/platform team, and payment product owner.

## 4. AI Use Case Scope

In scope:

- Pre-validate draft `pacs.008` payments before submission.
- Recommend suggest-only payment repairs with evidence.
- Recommend payment rail options for ready payments.
- Investigate failed or rejected payments using logs, rules, and payment context.
- Generate concise business explanations using governed model access through `ai-gateway-service`.
- Retrieve governed rule and policy evidence through `ai-rag-service`.
- Emit telemetry, traces, metrics, and audit events through `ai-sre-observability`.

Out of scope for initial production pilot:

- Automatic payment repair submission.
- Automatic rail execution or payment release.
- Autonomous compliance decisioning.
- Replacing human approval for high-risk or high-value payment actions.

## 5. AI User Stories

### Story 1: AI Payment Pre-Validation

**Use case**

- **As a** payment operations analyst,
- **I want to** pre-validate a draft payment before it is submitted,
- **so that** I can prevent avoidable rejects and improve straight-through processing.

**Input data and knowledge sources**

- Draft payment instruction, including message type, amount, currency, debtor, creditor, debtor agent BIC, creditor agent BIC, creditor account, requested execution date, and payment ID.
- ISO 20022 validation rules.
- Bank reference data for BIC and participant reachability.
- Scheme and rail-specific mandatory-field rules from `ai-rag-service`.
- Payment hub context for draft status and source instruction metadata.

**Output data format**

```json
{
  "payment_id": "PMT-DRAFT-0001",
  "status": "Needs Repair",
  "issues": [
    {
      "code": "MISSING_CREDITOR_ACCOUNT",
      "severity": "High",
      "field_path": "CdtrAcct/Id",
      "explanation": "The draft pacs.008 is missing the creditor account identifier.",
      "repair_suggestion": "Populate creditor account from the source instruction before submission.",
      "evidence_references": ["RULE-PACS008-CDTR-ACCT"]
    }
  ],
  "trace_id": "generated-trace-id"
}
```

**Acceptance criteria**

- **Positive scenario:** Given a valid draft payment, when the analyst runs pre-validation, then the system returns `Ready` with no repair issues.
- **Negative scenario:** Given a draft missing `CdtrAcct/Id`, when the analyst runs pre-validation, then the system returns `Needs Repair`, field path `CdtrAcct/Id`, severity `High`, and a repair suggestion.
- **Edge scenario:** Given a draft with multiple possible validation issues, when pre-validation runs, then the system returns all detected issues with separate field paths and evidence references.
- **Edge scenario:** Given reference data is unavailable, when pre-validation runs, then the system returns an explicit dependency-unavailable status and does not claim the payment is valid.

**Evaluation metrics**

- Precision of detected validation issues.
- Recall of known mandatory-field and reference-data issues.
- False-ready rate for payments later rejected by validation.
- Reduction in manual validation time.
- STP improvement for payments touched by the copilot.

**Non-functional requirements**

- P95 pre-validation latency under 2 seconds for single-payment checks.
- Deterministic checks must run without LLM dependency.
- All payment identifiers and user actions must be logged with correlation IDs.
- Sensitive payment data must be masked in logs and traces.
- Service must fail closed when required reference data is unavailable.

**Assumptions and dependencies**

- Payment hub exposes draft payment details through API or event stream.
- Bank reference data exposes BIC and participant reachability checks.
- `ai-rag-service` provides governed validation-rule retrieval.
- `ai-sre-observability` receives structured events and traces.

**Guardrails and risk management**

- Human analyst remains responsible for deciding whether to repair or proceed.
- The system must label recommendations as advisory.
- High-severity validation issues block rail recommendation.
- All outputs must include evidence references or dependency-status details.

### Story 2: AI Repair Recommendation

**Use case**

- **As a** payment repair analyst,
- **I want to** receive evidence-backed repair recommendations,
- **so that** I can resolve payment defects faster and reduce repeated rejects.

**Input data and knowledge sources**

- Failed or draft payment data.
- Validation issue codes and field paths.
- Source instruction metadata.
- Payment scheme rules from `ai-rag-service`.
- Reference data checks.
- Historical repair outcomes where available.

**Output data format**

```json
{
  "payment_id": "PMT-2026-0001",
  "recommendation_type": "Repair",
  "recommended_action": "Populate creditor account from the source instruction, then resubmit the pacs.008.",
  "owner": "Payment repair analyst",
  "confidence": "High",
  "evidence": [
    {
      "source": "Rule Knowledge",
      "reference": "RULE-PACS008-CDTR-ACCT",
      "summary": "Creditor account identifier is mandatory for this pacs.008 flow."
    }
  ],
  "human_approval_required": true
}
```

**Acceptance criteria**

- **Positive scenario:** Given a known repairable defect, when repair recommendation runs, then the system returns action type `Repair`, owner, evidence, and clear analyst instructions.
- **Negative scenario:** Given an unknown defect, when repair recommendation runs, then the system returns `Review` or `Escalate` rather than inventing a repair.
- **Edge scenario:** Given conflicting rule evidence, when recommendation runs, then the system flags conflict and routes to manual review.
- **Edge scenario:** Given missing source instruction data, when recommendation runs, then the system recommends data retrieval or escalation instead of fabricating a value.

**Evaluation metrics**

- Repair recommendation precision.
- Analyst acceptance rate.
- Repeat-reject rate after recommended repair.
- Average handling time reduction.
- Escalation appropriateness for non-repairable cases.

**Non-functional requirements**

- P95 recommendation latency under 3 seconds excluding external dependency delays.
- Cost per recommendation target must be tracked, with configurable LLM usage limits.
- Repair suggestions must not include unverified field values.
- All recommendation decisions must be auditable.

**Assumptions and dependencies**

- Source instruction data is accessible for analysts or through payment hub integration.
- `ai-gateway-service` is used only for narrative polishing, not authoritative repair decisioning.
- `ai-rag-service` returns versioned rule evidence.

**Guardrails and risk management**

- No auto-repair in the initial production pilot.
- Human approval is required before resubmission.
- The system must clearly distinguish verified data from suggested analyst action.
- Recommendations with low confidence, missing evidence, or rule conflicts must route to manual review.

### Story 3: AI Payment Rail Recommendation

**Use case**

- **As a** payment operations analyst,
- **I want to** receive an explainable rail recommendation for a ready payment,
- **so that** I can choose the rail that best balances speed, cost, eligibility, limits, and operational risk.

**Input data and knowledge sources**

- Validated payment instruction.
- Amount, currency, debtor and creditor country, creditor agent reachability.
- Rail configuration, amount limits, fees, SLA, cutoff windows, holidays, and availability.
- Compliance and sanctions screening status where required.
- Historical rail performance and failure rates where available.

**Output data format**

```json
{
  "payment_id": "PMT-DRAFT-0003",
  "status": "Recommended",
  "recommended_rail": "WIRE",
  "ranked_options": [
    {
      "rail_id": "WIRE",
      "eligible": true,
      "score": 88,
      "fee": "High",
      "settlement_time": "Same business day",
      "reasons": ["Best fit for high-value domestic USD payments."]
    },
    {
      "rail_id": "RTP",
      "eligible": false,
      "score": 0,
      "reasons": ["Payment amount exceeds RTP limit."]
    }
  ],
  "human_approval_required": true
}
```

**Acceptance criteria**

- **Positive scenario:** Given a valid high-value domestic USD payment, when rail recommendation runs, then Wire is recommended if RTP limit is exceeded and Wire is eligible.
- **Negative scenario:** Given a payment with unresolved validation defects, when rail recommendation runs, then the system blocks rail recommendation and instructs the analyst to repair first.
- **Edge scenario:** Given two eligible rails with equal score, when recommendation runs, then the system applies a documented tie-breaker such as lower cost, faster settlement, or configured business priority.
- **Edge scenario:** Given rail configuration is stale or unavailable, when recommendation runs, then the system does not recommend a rail and returns dependency-unavailable status.

**Evaluation metrics**

- Recommendation agreement rate with payment operations policy.
- Rail eligibility accuracy.
- Cost optimization impact.
- SLA adherence after recommended rail selection.
- Exception rate by recommended rail.

**Non-functional requirements**

- P95 rail recommendation latency under 2 seconds with cached rail config.
- Rail config must be versioned and timestamped.
- Recommendations must include explainable reasons and ineligible rail reasons.
- Recommendation cost should be near-zero for deterministic scoring; LLM use is optional for narrative only.

**Assumptions and dependencies**

- Rail configuration and cutoff services are available.
- Payment has completed pre-validation before rail recommendation.
- Business priority weights are governed by payment product and operations leadership.

**Guardrails and risk management**

- Human approval is required before rail execution.
- Compliance holds override rail recommendation.
- High-value threshold rules must be configurable.
- The system must show why non-recommended rails were rejected or ranked lower.

### Story 4: AI Exception Investigation

**Use case**

- **As a** payment operations analyst,
- **I want to** investigate a rejected or failed payment with AI-assisted evidence gathering,
- **so that** I can identify root cause and next action faster.

**Input data and knowledge sources**

- Failed payment details and exception text.
- Operational logs from validator, reference-data service, payment orchestrator, and repair queue.
- Rule knowledge and runbooks from `ai-rag-service`.
- Case history and previous analyst actions.
- Model-generated narrative through `ai-gateway-service`.

**Output data format**

```json
{
  "case_id": "CASE-001",
  "classification": {
    "code": "MISSING_CREDITOR_ACCOUNT",
    "category": "Validation",
    "severity": "High"
  },
  "root_cause": "Creditor account is missing from the pacs.008 message.",
  "recommended_action": {
    "action_type": "Repair",
    "owner": "Payment repair analyst",
    "description": "Populate creditor account from the source instruction, then resubmit the pacs.008."
  },
  "evidence": [],
  "timeline": [],
  "explanation_source": "LLM polished via ai-gateway-service"
}
```

**Acceptance criteria**

- **Positive scenario:** Given a known failed payment pattern, when investigation runs, then the system returns classification, root cause, evidence, and next best action.
- **Negative scenario:** Given an unknown exception, when investigation runs, then the system avoids unsupported diagnosis and routes to senior manual review.
- **Edge scenario:** Given operational logs are partially unavailable, when investigation runs, then the system reports missing evidence and lowers confidence.
- **Edge scenario:** Given retrieved rule evidence does not match the classification, when investigation runs, then irrelevant evidence must be excluded.

**Evaluation metrics**

- Root-cause classification accuracy.
- Evidence relevance score.
- Analyst time-to-diagnosis reduction.
- Manual review escalation precision.
- Hallucination or unsupported-claim rate.

**Non-functional requirements**

- P95 investigation response under 5 seconds for standard cases.
- LLM narrative must preserve facts and not add new evidence.
- Every diagnosis must include evidence references or an explicit evidence gap.
- All investigation requests must be traceable by case ID and payment ID.

**Assumptions and dependencies**

- Operational logs are queryable by payment ID.
- `ai-rag-service` can retrieve rule and runbook evidence.
- `ai-gateway-service` supports safe narrative generation with policy controls.
- `ai-sre-observability` supports tracing across services.

**Guardrails and risk management**

- Human analyst makes final operational decision.
- Unknown or low-confidence cases must route to manual review.
- LLM output must be grounded in deterministic findings and retrieved evidence.
- Compliance-sensitive cases require additional review before action.

## 6. Success Metrics

Primary success metrics:

- Increase straight-through processing rate for eligible payment flows.
- Reduce average handling time for payment repair and investigation.
- Reduce repeat rejects after analyst repair.

Secondary metrics:

- Analyst recommendation acceptance rate.
- Rail recommendation agreement with policy.
- Evidence relevance score.
- Number of cases routed correctly to manual review.

Guardrail metrics:

- False-ready validation rate.
- Unsupported or hallucinated recommendation rate.
- Security incidents or policy violations.
- P95 latency and cost per recommendation.

## 7. Non-Functional Requirements

- **Latency:** Pre-validation and rail recommendation P95 under 2 seconds; investigation P95 under 5 seconds for standard cases.
- **Cost:** Deterministic checks should not require LLM calls; LLM usage should be routed through `ai-gateway-service` with cost tracking and model limits.
- **Security:** Use authentication, RBAC, least privilege, encrypted transport, masked logs, and secret management.
- **Reliability:** Fail closed for unavailable validation, reference-data, compliance, or rail-config dependencies.
- **Auditability:** Persist recommendation inputs, outputs, evidence references, model/service versions, user identity, and trace IDs.
- **Observability:** Emit structured logs, metrics, traces, and health signals to `ai-sre-observability`.

## 8. Assumptions and Dependencies

- Production deployment target is GKE.
- Shared services exist in the same cluster:
  - `ai-gateway-service`
  - `ai-rag-service`
  - `ai-sre-observability`
- Production integrations will replace mock data:
  - payment hub
  - bank reference data
  - rail configuration and cutoff service
  - operational logs
  - case management
  - compliance and sanctions systems
- Initial production pilot is read-only and advisory.
- Payment operations leadership will define business priority weights for rail scoring.

## 9. Guardrails and Risk Management

- Human-in-the-loop approval is required for repair, resubmission, rail execution, compliance-sensitive decisions, and high-value payment actions.
- Recommendations must include evidence references, dependency status, and confidence/eligibility rationale.
- LLM-generated text must be limited to explanation and summarization unless separately approved.
- The system must not fabricate missing payment field values.
- Low-confidence, unknown, conflicting, or incomplete-evidence cases must route to manual review.
- Compliance holds and sanctions concerns override all recommendation flows.

## 10. Production Readiness Notes

Before production launch, the team must add:

- API/service separation from the Streamlit PoC.
- GKE manifests, container image build, probes, resource limits, and service accounts.
- Auth and RBAC integration.
- Adapter interfaces for enterprise data sources.
- Audit persistence.
- Full observability integration.
- Security review, model governance review, and operational runbooks.
- Pilot evaluation plan with read-only recommendations before enabling any operational action.
