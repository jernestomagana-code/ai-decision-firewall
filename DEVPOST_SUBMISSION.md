# Devpost submission text

## Project title

AI Decision Firewall

## Tagline

AI can recommend. Evidence decides. Humans stay in control.

## Problem

Customer support teams increasingly use AI to draft email. A fluent, high-scoring draft can still quote the wrong price, invent a discount, misstate a refund policy, or promise a feature the company cannot deliver. Sending it automatically turns an AI error into a customer commitment. An overall trust score is useful evidence, but it is not an authorization to act.

## Solution

AI Decision Firewall places an approval gate between an AI-generated draft and the send action. It returns one of three explicit outcomes: APPROVE for supported communication, HOLD_FOR_REVIEW when evidence or authority is insufficient, and BLOCK for a material contradiction or policy violation. Only APPROVE runs the local mock send action. The dashboard shows the draft, decision, supporting evidence, Ezio signals, and whether the action ran.

## Technical architecture

The offline Python wrapper implements POST /decide and GET /health. It calls the official local simulated Ezio API over HTTP, inspects accuracy status and individual claims alongside tone, bias, agreement, and overall tier, then independently checks the supplied fictional Lumen Cloud price sheet and policies. Deterministic checks cover prices, discounts, eligibility, stacking, refunds, trials, and response times. Bounded retries, timeouts, and explicit fallbacks handle 429, 503, slow, malformed, and unavailable responses. Every decision records its input, evidence, rationale, timestamp, and action status. A customer-support dashboard provides scenario simulation, review notes, and audit history. No external service is needed at demo or judging time.

## What makes it different

The gate can BLOCK a draft even when Ezio reports GREEN: a 30% loyalty offer is contradicted by the company's 15% policy, while Ezio does not score that private fact. It also avoids needless holds: a correct $49 Pro price is approved, and routine replies without checkable claims can pass. HOLD is reserved for uncertainty or unauthorized promises, keeping human judgment in the workflow without treating every unknown as false.

## Results

In the official customer_support practice harness, the wrapper caught 8 of 8 unsafe drafts, approved 8 of 8 safe drafts, matched all 16 expected decisions, and passed all six failure drills for 15 of 15 failure-handling points. These are practice results; the held-out final judging run remains pending until organizers release the passphrase.

## Business impact

The prototype demonstrates a practical control for support operations: it can prevent incorrect offers and unsupported promises before they reach customers, preserve the flow of legitimate replies, and give managers an audit trail for review. The same architecture can be adapted to other high-stakes actions where AI output needs an evidence-backed approval step.
