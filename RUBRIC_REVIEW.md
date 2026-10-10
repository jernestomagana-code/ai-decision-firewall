# Rubric review

The official README awards 25 points for the persona UI (five criteria worth 5 each) and 25 judge-rubric points (technical execution, problem fit, novelty, demo clarity, practical impact). This is a self-audit, not a judge score.

| Scored area | Evidence in this build | Remaining risk |
|---|---|---|
| Send input, get response | Draft, plan, and tenure go to POST /decide; the server response supplies decision, reason, evidence, and mock action status. Empty text is rejected; text is capped at 20,000 characters; a loading state covers slow calls. | Long degraded calls still take several seconds, so narrate the loading state in a demo. |
| Simulate action | Practice scenarios call the same endpoint. A comparison control runs a supported price, bad loyalty offer, and unauthorized feature promise, showing APPROVE, BLOCK, and HOLD side by side with action status. | Comparison intentionally runs the mock send for its approved sample, so explain that it is local simulation. |
| Clarity of risk | Decision is shown by text and color; customer consequence, key figures, source checks, Ezio tier, accuracy state, and action status are visible. | Numeric figures are highlighted; qualitative claims are explained in the reason/evidence rather than highlighted inside the draft. |
| Resilience and review | HTTP errors show a visible message; degraded Ezio results are reflected in HOLD; reviewers can log proceed-to-recheck or rejection with a reason; audit history is visible. | The UI does not expose a manual chaos-mode switch; demonstrate reliability with the official failure-drill report. |
| Persona fit | Customer plan and tenure feed discount eligibility checks; dashboard language, review workflow, and audit trail match a support lead's send decision. | The send action is intentionally mocked; do not imply a production email integration. |

**Judge-rubric focus.** Explain the independent business check as the distinctive layer: Ezio can report GREEN while private policy data blocks a wrong loyalty offer. The demo should make that contrast visible within 30 seconds. Practical impact is a credible workflow benefit, not a measured financial result; avoid invented savings estimates. Show the signed final result only after the organizer releases the passphrase.

**Submission readiness.** The one-page PDF, README, demonstration script, and Devpost copy are ready. A short screen recording and an accessible GitHub repository still need to be attached; GitHub CLI authentication currently fails. The held-out final run remains pending by rule.
