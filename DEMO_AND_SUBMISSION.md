# Demo and submission

Record this walkthrough as a short screen video. The [event rules](https://ai-trust.devpost.com/rules) say judging uses submitted materials and does not require a live presentation; judges may still ask to verify the wrapper.

## Two-minute demonstration

1. **0:00–0:20 - Problem.** Open the dashboard. Say: “A polished AI email can still quote the wrong price or promise a discount a customer cannot receive. If a support team sends it automatically, the mistake becomes a customer commitment.”
2. **0:20–0:45 - Safe email.** Click scenario cs-02, “The Pro plan is $49 per month.” Say: “The firewall calls Ezio, then separately checks our price sheet. It approves this supported price, and only then does the mock send run.” Point to APPROVE, the price-sheet citation, and “Mock email sent.”
3. **0:45–1:15 - Unsafe email.** Click scenario cs-07, “Your 30% loyalty discount applies to the Pro plan.” Say: “Ezio's overall score is GREEN, but its accuracy check did not score this private business fact. Our independent policy check finds that loyalty is 15%, so the gate blocks the email before send.” Point to GREEN 94, BLOCK, and “Send prevented.”
4. **1:15–1:40 - Human control.** Click scenario cs-11, the promised custom feature. Say: “This is a promise we cannot verify, so it is held for a lead. We record why we will revise it; the revised draft must pass the same gate.” Enter a short note and click “Proceed to recheck.”
5. **1:40–2:00 - Why it matters.** Say: “For a support operation, this means fewer incorrect commitments, less manual cleanup, and an auditable explanation for every send or stop. The local prototype passed all 16 practice decisions and six failure drills. It runs fully offline and is ready for a judge's surprise draft.”

## Screenshot guidance

- Capture the full dashboard with an approved scenario and action confirmation.
- Capture a blocked GREEN score trap with policy evidence and prevented action visible.
- Capture a held commitment with a saved review note and audit history.
- Show measured results through the official results viewer. Do not edit results files.

## Final submission checklist

- [ ] Demonstrate the local page with the serve command in README.md.
- [ ] State the customer-support persona and gated mock email action in Devpost.
- [ ] Link an accessible repository with setup steps and the one-page policy PDF.
- [ ] Attach screenshots or a short screen recording.
- [ ] Submit the Approval Gate entry before 3:00 PM Pacific on October 10, 2026.
- [ ] When organizers release the passphrase, run the judge command in README.md.
- [ ] Submit the unchanged signed results JSON and readable report.
- [ ] Keep audit_log.jsonl, actions.log, and the final run directory available for judges.
