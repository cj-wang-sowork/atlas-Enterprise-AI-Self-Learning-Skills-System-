# Independent blinded draft-review rubric

**Study status: not run. No participant has been selected and no human ratings
have been collected. Internal agent notifications are not participant responses.**

The examples are fictional marketing briefs. They do not establish customer ROI,
conversion improvement or real-world approval. Rate draft readiness against the
provided brief and source records, not against a presumed brand preference.

## Administration

1. Recruit at least two independent marketing/content reviewers who did not
   author the prompts, outputs or report. Record consent, role and conflicts.
2. Supply each rater with their own copy of `run-20261017/human-scoring.json` and
   this rubric only. The six outputs are included unchanged under opaque labels.
   Do not share arm labels, prompts, manifest, this study's report, or unblinding
   key. Do not tell reviewers the automated gate totals or timings.
3. Review each output independently. Keep original forms; never fill missing
   ratings with model-generated or evaluator-invented numbers. If a condition is
   guessed, record that separately before unblinding.
4. Fill rater ID, five 1–5 scores and notes. If measuring editing effort, start a
   timer, edit to an agreed acceptance standard and record elapsed minutes;
   otherwise leave `editing_minutes_measured` null. Do not estimate it from prose.
5. Only after all forms are frozen, join by anonymous ID using the separate key.
   Report paired per-task differences, each rater's result and disagreements.
   Do not silently average away factual errors or omit failed runs.

## Five dimensions (equal reporting weight; do not collapse into ROI)

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| Factual accuracy | Contradicts/introduces unsupported material claims | Sources mostly correct; nonmaterial edits needed | All material claims supported and limitations accurate |
| Brand/audience fit | Conflicts with audience/channel/tone | Generally relevant but generic | Specific to the brief, audience, channel and supplied tone |
| Actionability | Cannot be used as a draft | Useful after substantive editing | Clear proposition, headlines and CTA ready for normal review |
| Clarity | Confusing, inconsistent or difficult to scan | Understandable but wordy/uneven | Concise, distinct headlines and clear language |
| Risk control | Implies approval, evidence or outcomes not supplied | Draft status present, some ambiguity | Draft/approval gaps and claim boundaries handled accurately |

Use 2 for major edits and 4 for minor edits between the anchors. A 5 means ready
**as a draft**, never permission to publish. Explain factual concerns with source
IDs and an exact output excerpt. Creative suggestions may be useful without
being verified business outcomes; review their implications, not only the
machine-readable claims array.

Optional acceptance decision: accept-as-draft / revise / reject, with reasons.
No human decision, score, editing time or acceptance outcome has been supplied.
