# Current rules — human-maintained index

**Approved rules: EMPTY (0)**

Work standard v1 is operating policy, not an approved lesson. There are no
learned rules or completed human-feedback rounds in this starter reference.

Only the human operator updates this current-version index after explicit review
of actual task evidence and actual user feedback. A CandidateLesson must include
ID/revision, feedback meaning, evidence/output reference, rule, scope, exceptions,
and review trigger. The decision must name the exact ID+version, for example:

- `Accept CL-001 v1` accepts only that exact wording and version.
- `Revise CL-001 v1` requests a new revision; the new version remains Candidate.
- `Reject CL-001 v1` rejects that version; do not use it as an approved rule.

These are decision syntax examples, not decisions or preapproved entries. Blank,
Defer, repetition and assistant suggestions do not approve anything. On wording
changes, increment the revision and obtain fresh human approval. After Accept,
the operator manually records exact ID/version, rule text, scope, exceptions,
evidence, reviewer/date, review trigger and active status here; preserve review
history in OUTCOME_REVIEW_LOG.md. Remove/replace superseded versions in supplied
context. Rejected, superseded, expired or ambiguous entries must not be used.

For each task, supply the sanitized current index yourself and check the output's
approved lesson IDs+versions used card. If no current version was actually read,
show none (0), not a remembered or guessed rule. If the context conflicts, omit
the disputed rule and state the limitation until the operator resolves it.

This file is not a backend registry, automatic memory write, access-control
boundary or guarantee of cross-chat retrieval. An assistant cannot maintain it
merely by claiming it saved a lesson. No GitHub fetch or upload is automatic.
