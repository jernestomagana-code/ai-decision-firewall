# AI Decision Firewall — decision policy

**Persona and action.** A customer support lead reviews an AI-written Lumen Cloud email. Only APPROVE runs the local mock send_email action. No real email is sent.

**Evidence sources.** The wrapper calls simulated Ezio over HTTP and independently reads the supplied customer-support price sheet and policies. It checks plan prices, discounts and eligibility, stacking, refunds, trials, and response times. It scans relevant clauses so a correct price cannot hide a wrong response-time promise.

| Condition | Decision | Rationale |
|---|---|---|
| Company fact contradicts supplied data; ineligible discount; stacked discounts; Ezio contradicts a claim | BLOCK | A known false or disallowed statement must not reach a customer, even with an overall GREEN tier. |
| Product or delivery commitment, guarantee, unverifiable Ezio claim, missing eligibility context, unavailable Ezio fact check | HOLD_FOR_REVIEW | A human must verify or revise an unsupported promise. |
| Tone below 65, bias below 55, agreement below 55, or YELLOW/RED overall tier without a contradiction | HOLD_FOR_REVIEW | Weak communication signals warrant review; BLOCK is reserved for material contradictions or explicit policy failures. |
| No contradiction or review trigger | APPROVE | Routine replies and supported facts should pass. |

**Accuracy states.** For scored accuracy, inspect per-claim verdicts and contradicted counts. Not_scored is allowed if independent checks find no issue; routine messages may have no extracted claims. Unavailable accuracy, malformed responses, and exhausted HTTP retries hold unless a company check warrants BLOCK.

**Reliability.** The supplied HTTP client makes at most four attempts, handles 429 and 503 with capped backoff, limits each attempt to 15 seconds and the whole request to 45 seconds, and validates response structure. The gate never runs the mock action on HOLD or BLOCK.

**Audit and review.** Ordinary decisions record UTC time, input, context, Ezio response, evidence, reason, decision, and action status in audit_log.jsonl. A reviewer can record rejection or a revision plan with a reason. Revised drafts must pass the same gate; review notes never trigger an action.
