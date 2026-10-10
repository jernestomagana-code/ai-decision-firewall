"""Your wrapper. Start with check_source_of_truth() and policy.json.

Flow: call Ezio -> read its signals -> check your persona's source of truth -> apply policy
-> decision (+ reason, evidence) -> audit log -> run the mock action only if approved.

Run one input:  python3 wrapper.py customer_support "Your 30% loyalty discount applies to the Pro plan."
Score yourself: python3 evaluate.py customer_support
"""
import csv
import json
import math
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import audit
import mock_actions
from ezio_client import EzioError, analyze

HERE = Path(__file__).resolve().parent
PERSONAS = HERE.parent / "personas"
POLICY = json.loads((HERE / "policy.json").read_text())

APPROVE, HOLD, BLOCK = "APPROVE", "HOLD_FOR_REVIEW", "BLOCK"
RANK = {APPROVE: 0, HOLD: 1, BLOCK: 2}


@dataclass
class Signals:
    tier: str
    score: float
    summary: str
    accuracy_status: str
    claims_total: int
    claims_verified: int
    claims_contradicted: int
    tone: float
    bias: float
    agreement: float
    claims: list = field(default_factory=list)


@dataclass
class Finding:
    level: str
    message: str


@dataclass
class Decision:
    decision: str
    reason: str
    evidence: list
    ezio: dict


def parse_signals(resp):
    try:
        verdict, dims = resp["verdict"], resp["dimensions"]
        acc = dims["accuracy"]
        if verdict["tier"] not in ("GREEN", "YELLOW", "RED") or acc["status"] not in ("scored", "not_scored", "unavailable"):
            raise ValueError("invalid tier or accuracy status")
        scores = [verdict["score"]] + [dims[d]["score"] for d in ("tone", "bias", "agreement")]
        if acc["status"] == "scored":
            scores.append(acc["score"])
        if any(isinstance(s, bool) or not isinstance(s, (int, float)) or not math.isfinite(s) or not 0 <= s <= 100 for s in scores):
            raise ValueError("scores must be finite numbers between 0 and 100")
        if not isinstance(verdict["summary"], str) or not isinstance(resp.get("claims", []), list):
            raise ValueError("invalid summary or claims")
        return Signals(
            tier=verdict["tier"], score=verdict["score"], summary=verdict["summary"],
            accuracy_status=acc["status"], claims_total=acc.get("claims_total", 0),
            claims_verified=acc.get("claims_verified", 0), claims_contradicted=acc.get("claims_contradicted", 0),
            tone=dims["tone"]["score"], bias=dims["bias"]["score"], agreement=dims["agreement"]["score"],
            claims=resp.get("claims", []),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise EzioError("malformed mock response", resp) from e


@lru_cache(maxsize=None)
def load_source_of_truth(persona):
    """Every .json and .csv file in the persona folder, keyed by file name (for example sot['policies'])."""
    data = {}
    for f in sorted((PERSONAS / persona).iterdir()):
        if f.stem in ("practice_set", "business_rules"):
            continue
        if f.suffix == ".json":
            data[f.stem] = json.loads(f.read_text())
        elif f.suffix == ".csv":
            with f.open() as handle:
                data[f.stem] = list(csv.DictReader(handle))
    return data


def check_source_of_truth(text, context, sot):
    """Compare factual customer claims with the supplied company records.

    Rules inspect all relevant clauses, so a correct price cannot hide a wrong SLA.
    An unmentioned fact is not treated as false.
    """
    if "policies" not in sot or "price_sheet" not in sot:
        return []
    rules, rows = sot["policies"], {r["plan"].lower(): r for r in sot["price_sheet"]}
    lower = text.lower().replace("–", "-")
    findings = []

    def add(level, message):
        if message not in [f.message for f in findings]:
            findings.append(Finding(level, message))

    def amount(raw):
        words = {"zero": 0, "four": 4, "seven": 7, "fourteen": 14,
                 "fifteen": 15, "nineteen": 19, "twenty": 20, "twenty-four": 24,
                 "thirty": 30, "forty-nine": 49, "forty eight": 48,
                 "seventy-nine": 79, "ninety-nine": 99}
        return float(words[raw.lower()]) if raw.lower() in words else float(raw.replace(",", ""))

    number = r"(?:\d+(?:\.\d+)?|zero|fourteen|fifteen|nineteen|twenty|twenty-four|thirty|forty-nine|seventy-nine|ninety-nine)"
    money = rf"(?:\$\s*{number}|{number}\s+dollars?)"
    plans = "|".join(rows)
    # Price clauses can contain multiple figures. Match each plan independently.
    for plan, row in rows.items():
        for match in re.finditer(rf"\b{plan}\b(?:(?![.;!?]).){{0,70}}?({money})\s*(?:/\s*mo(?:nth)?|per\s+month|monthly)", lower):
            raw = match.group(1).replace("$", "").strip().split(" dollar")[0]
            claimed = amount(raw)
            annual = bool(re.search(r"annual(?:ly)?|yearly|billed yearly", match.group(0)))
            expected = float(row["annual_price_per_month_usd"] if annual else row["monthly_price_usd"])
            if abs(claimed - expected) > .011:
                add(BLOCK, f"{row['plan']} {'annual effective' if annual else 'monthly'} price is ${expected:g}, but draft says ${claimed:g} (price_sheet.csv).")
            else:
                add(APPROVE, f"Verified {row['plan']} {'annual effective' if annual else 'monthly'} price ${expected:g} in price_sheet.csv.")
    # Also recognize 'Business is $99/mo' and variants without the word plan.
    for match in re.finditer(rf"\b({plans})\b[^.;!?]{{0,55}}?\$\s*(\d+(?:\.\d+)?)\s*/\s*mo\b", lower):
        plan, claimed = match.group(1), float(match.group(2))
        expected = float(rows[plan]["monthly_price_usd"])
        if claimed != expected:
            add(BLOCK, f"{rows[plan]['plan']} monthly price is ${expected:g}, but draft says ${claimed:g} (price_sheet.csv).")
        else:
            add(APPROVE, f"Verified {rows[plan]['plan']} monthly price ${expected:g} in price_sheet.csv.")

    discounts = rules["discounts"]
    for kind, rule in (("loyalty", discounts["loyalty"]), ("annual", discounts["annual_billing"])):
        for match in re.finditer(rf"(?:({number})\s*%[^.;!?]{{0,45}}\b{kind}\b|\b{kind}\b[^.;!?]{{0,45}}?({number})\s*%)", lower):
            claimed = amount(match.group(1) or match.group(2))
            if claimed != rule["percent"]:
                add(BLOCK, f"{kind.title()} discount is {rule['percent']}%, but draft says {claimed:g}% (policies.json).")
            else:
                add(APPROVE, f"Verified {kind} discount at {claimed:g}% in policies.json.")
        if re.search(rf"\b{kind}\b[^.;!?]{{0,55}}\b(discount|off|qualif|appl)", lower):
            plan = str(context.get("plan", "")).lower()
            explicit = re.search(rf"\b({plans})\b", lower)
            plan = explicit.group(1) if explicit else plan
            if plan and plan not in [p.lower() for p in rule["applies_to"]]:
                add(BLOCK, f"{kind.title()} discount is not available on {plan.title()} (policies.json).")
            if kind == "loyalty":
                tenure = context.get("customer_tenure_months")
                if tenure is None or not isinstance(tenure, (int, float)):
                    add(HOLD, "Customer tenure is needed to verify loyalty eligibility.")
                elif tenure < rule["min_tenure_months"]:
                    add(BLOCK, f"Loyalty requires {rule['min_tenure_months']} months; customer has {tenure} (policies.json).")
                else:
                    add(APPROVE, f"Verified {tenure:g}-month tenure meets loyalty minimum of {rule['min_tenure_months']} months.")
    if not discounts["stacking_allowed"] and re.search(r"(?:combin|stack|together|both)[^.;!?]{0,85}(?:loyalty|annual)|(?:loyalty|annual)[^.;!?]{0,85}(?:combin|stack)", lower):
        if "loyalty" in lower and "annual" in lower and not re.search(r"(?:cannot|can't|not allowed|never)\s+(?:be\s+)?(?:combin|stack)", lower):
            add(BLOCK, "Loyalty and annual discounts cannot be stacked (policies.json).")

    for match in re.finditer(rf"\b({number})\s*(?:-\s*)?days?[^.;!?]{{0,55}}\brefund|\brefund[^.;!?]{{0,55}}?\b({number})\s*(?:-\s*)?days?", lower):
        claimed = amount(match.group(1) or match.group(2))
        annual = bool(re.search(r"annual|yearly", lower))
        expected = rules["refunds"]["annual_plans_days" if annual else "monthly_plans_days"]
        if claimed != expected:
            add(BLOCK, f"{'Annual' if annual else 'Monthly'} first-payment refund window is {expected} days, but draft says {claimed:g} (policies.json).")
        else:
            add(APPROVE, f"Verified {expected}-day {'annual' if annual else 'monthly'} first-payment refund window in policies.json.")
    if "refund" in lower and re.search(r"(?:any\s*time|first\s+year|one\s+year|12\s+months)", lower):
        add(BLOCK, "Refunds apply only to the first payment, within 14 days for annual or 30 days for monthly plans (policies.json).")

    for match in re.finditer(rf"\b({number})\s*(?:-\s*)?days?[^.;!?]{{0,45}}\b(?:free\s+)?trial|\b(?:free\s+)?trial[^.;!?]{{0,45}}?\b({number})\s*(?:-\s*)?days?", lower):
        claimed = amount(match.group(1) or match.group(2))
        if claimed != rules["free_trial"]["days"]:
            add(BLOCK, f"Free trial is {rules['free_trial']['days']} days, but draft says {claimed:g} (policies.json).")
        else:
            add(APPROVE, f"Verified {claimed:g}-day free trial in policies.json.")
    if "trial" in lower:
        for plan, row in rows.items():
            if re.search(rf"\b{plan}\b", lower) and int(row["free_trial_days"]) == 0 and re.search(r"\b(?:free|trial|eligible|available)\b", lower):
                add(BLOCK, f"{row['plan']} has no free trial (price_sheet.csv).")
        if re.search(r"(?:card|credit card)[^.;!?]{0,25}(?:required|needed|must)|(?:required|need)[^.;!?]{0,20}(?:card|credit card)", lower) and not re.search(r"(?:no|not|without)\s+(?:credit\s+)?card", lower):
            add(BLOCK, "A card is not required for the free trial (policies.json).")
    for plan, row in rows.items():
        for match in re.finditer(rf"\b{plan}\b[^.;!?]{{0,95}}?\b(?:first\s+)?response[^.;!?]{{0,35}}?\b({number})\s*(?:-\s*)?hours?", lower):
            claimed = amount(match.group(1))
            expected = float(row["first_response_hours"])
            if claimed != expected:
                add(BLOCK, f"{row['plan']} first response is within {expected:g} hours, but draft says {claimed:g} (price_sheet.csv).")
            else:
                add(APPROVE, f"Verified {row['plan']} first response within {expected:g} hours in price_sheet.csv.")
    if re.search(r"\b(?:ship|deliver|release|build|add|implement)\w*\b[^.;!?]{0,90}\b(?:feature|integration|export|next\s+(?:week|month)|by\s+\w+)", lower):
        add(HOLD, "Product or delivery commitment needs manager review (business_rules.md).")
    if re.search(r"\b(?:guaranteed|guarantee|you will love|greatest|amazing news)\b", lower):
        add(HOLD, "Guarantee or promotional language needs review (business_rules.md).")
    return findings


def apply_policy(signals, findings, policy):
    decision, reasons = APPROVE, []

    def raise_to(level, reason):
        nonlocal decision
        reasons.append(reason)
        if RANK[level] > RANK[decision]:
            decision = level

    for f in findings:
        if f.level != APPROVE:
            raise_to(f.level, f.message)
    if signals.claims_contradicted:
        raise_to(BLOCK, f"Ezio contradicted {signals.claims_contradicted} checked claim(s)")
    for claim in signals.claims:
        if isinstance(claim, dict) and claim.get("verdict") == "contradicted":
            raise_to(BLOCK, f"Ezio contradicted: {claim.get('claim', 'a factual claim')}")
        elif isinstance(claim, dict) and claim.get("verdict") == "unverifiable":
            raise_to(HOLD, f"Ezio could not verify: {claim.get('claim', 'a factual claim')}")
    for dim, rule in policy["dimension_minimums"].items():
        score = getattr(signals, dim)
        if score < rule["hold_below"]:
            raise_to(HOLD, f"{dim} score {score} is below {rule['hold_below']}")
    if signals.accuracy_status == "not_scored" and policy["when_accuracy_not_scored"] != "ignore":
        raise_to(policy["when_accuracy_not_scored"], "accuracy was not scored (no claims checked)")
    if signals.accuracy_status == "unavailable":
        raise_to(policy["when_accuracy_unavailable"], "fact-check was unavailable")
    tier_decision = policy["tier_decisions"][signals.tier]
    if tier_decision != APPROVE:
        raise_to(tier_decision, f"Ezio tier is {signals.tier} ({signals.score})")
    if not reasons:
        reasons.append(f"Company records show no contradiction; Ezio {signals.tier} {signals.score}, accuracy {signals.accuracy_status}")
    return reasons, decision


def decide(text, context=None, persona="customer_support", scenario=None, audit_log=True):
    context = context or {}
    try:
        response = analyze(text, scenario=scenario)
        signals = parse_signals(response)
    except EzioError as e:
        findings = check_source_of_truth(text, context, load_source_of_truth(persona))
        level = max([POLICY["on_ezio_failure"]] + [f.level for f in findings], key=lambda x: RANK[x])
        result = Decision(level, f"Ezio unavailable: {e}" + ("; " + "; ".join(f.message for f in findings) if findings else "; human verification required"),
                          [f.message for f in findings] or ["Ezio did not return usable evidence; human verification required."],
                          {"error": str(e), "response": e.response})
    else:
        findings = check_source_of_truth(text, context, load_source_of_truth(persona))
        reasons, decision = apply_policy(signals, findings, POLICY)
        result = Decision(
            decision, "; ".join(reasons), [f.message for f in findings] +
            [f"Ezio accuracy: {signals.accuracy_status}; verified {signals.claims_verified}; contradicted {signals.claims_contradicted}"],
            response,
        )
    if audit_log:
        audit.record(persona, text, context, result)
    return result


def gate(text, context=None, persona="customer_support"):
    result = decide(text, context, persona)
    print(f"{result.decision}: {result.reason}")
    if result.decision == APPROVE:
        mock_actions.run_for_persona(persona, text)
    else:
        print("[GATE] action not executed")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('usage: python3 wrapper.py <persona> "<text>" [context-json]')
    gate(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}, sys.argv[1])
