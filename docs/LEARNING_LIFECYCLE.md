# Reviewed outcome learning

`HermesAdapter` separates **frequency**, **measured task outcomes**, and **permission to reuse**.
Observing a pattern, selecting an adaptation mode, importing JSON, or setting a public
`confidence` field never authorizes a rule. Legacy observation methods remain available;
observation confidence stays `0.0` (unknown correctness, not a probability of failure).

## Lifecycle

1. **Observe:** `observe_access`, `observe_violation`, or `learn_market_behavior` collect
   source observations. Repetitions only increment occurrence counts.
2. **Extract a lesson:** supply procedural text to `draft_lesson(pattern_id, content,
   task_ids)`. This library does not invent a lesson using an LLM. The source observation
   and task evidence are snapshotted into revision 1 with state `pending`.
3. **Verify the outcome:** `record_outcome` records a unique task ID, source reference,
   result reference, named metric, baseline/candidate numbers, `higher`/`lower` direction,
   and a literal boolean success. `verify_outcome(..., validator=...)` is an explicit
   attestation by the application's authorized outcome validator, bound to the evidence
   digest. The application must check the actual result artifact and success criteria
   before making this call, including authorization of source/result artifacts in this
   exact scope. References are identifiers, not URLs automatically fetched
   or files automatically executed by this library.
4. **Human approval:** `review_skill(..., reviewer=..., decision="approve")` accepts
   only the latest pending revision with at least one distinct, verified, successful,
   strictly improving task outcome. All supplied evidence must meet that condition.
   Approver, timezone-aware review time, exact artifact digest, and state history are saved.
5. **Persist:** versioned artifacts contain scope, source, evidence, conditions, content,
   creation time, and SHA-256 digest. Governance state/history are separate from artifact
   content. Revisions are logically immutable: all public reads return detached copies;
   edits create new revisions rather than editing old artifacts.
6. **Reuse:** `get_adaptive_recommendations(market, context)` returns only current
   approved revisions whose market and conditions match. `reuse_skill(..., task_id=...)`
   records the approved version/digest selected for a new task. The trusted application
   is responsible for selecting an appropriate context and executing its own workflow.
7. **Compare:** `record_reuse_outcome` attaches a new baseline/candidate comparison to
   that reuse receipt. After outcome verification, `compare_outcome` reports `verified`,
   `improved`, raw `delta = candidate - baseline`, direction, success, and the exact skill
   revision/digest. Before verification, `improved` is `None`. Regressions remain visible;
   neither good nor bad reuse outcomes silently edit, approve, or revoke skills.

A draft can precede verification, but its evidence snapshot then remains unverified.
Use `revise_skill` after verification to create a new pending snapshot for review.
Metric values and their difference must be finite numbers (not strings, booleans, NaN,
or infinity). Task IDs and result references cannot be replayed as new tasks. A result
reference should identify the specific comparative result, not a shared report folder.
These are auditable comparisons, not causal or statistical confidence estimates.

## Trusted application boundary

This is a local Python library, **not an authentication service**. The trusted host must:

- Authenticate the caller, authorize the resource scope, and construct the exact
  `{tenant, brand, team, user}` dictionary. Never take scope or reviewer/verifier
  allowlists from agent-generated content or request JSON without authorization.
- Supply authorized human reviewer IDs and trusted outcome validator IDs at construction.
  An identity string alone proves nothing outside this boundary. Do not expose approval
  or validator methods as unrestricted model tools. The human must inspect the exact
  revision's content and evidence before approval.
- Keep one registry writer/service per data directory and serialize requests to it.
  Multiple agent roles may use the same application-owned adapter. Do not run concurrent
  independent adapter writers or reuse stale independently cached adapter instances;
  construct a fresh instance when handing off a persisted registry between processes.
  Stale snapshot writes and recommendation reads fail closed and require reopening; this
  freshness check is not an interprocess locking protocol for concurrent writers.
- Use a distinct owner-protected data directory per scope and protect its ancestors and
  backups. New directories are `0700`, snapshots `0600`; owner/group/other permissions,
  owner identity (on POSIX), symlinks, scope, digests, review history, outcome attestations,
  and content safety are checked when reopening. Failed writes do not activate memory.
- Treat local SHA-256 values as integrity checks, **not signatures or authentication**.
  An attacker who can write the owner's registry and recompute all metadata is outside
  this library's trust boundary. Copying arbitrary JSON into `registry.json` is not an
  import workflow. Local trusted restart and untrusted transport are separate paths.

Without explicit scope, the old observation API works but outcome/review/import methods
are denied and no reusable rules are returned. The `user` scope field identifies the
application-authorized resource owner, not the name of a worker role. No scope wildcard,
inheritance, cross-tenant, cross-brand, cross-team, or cross-user import is implemented.

`SecurityChecker` is constructed by default and scans decoded content, structured field
assignments, evidence references, observations, imports, and persisted records. Unsafe
input is rejected, not stored or silently redacted into a different approved artifact.
Structured inputs accept only JSON-compatible dictionaries with string keys, lists,
strings, booleans, null, and finite numeric scalars. Python tuples (including nested
and benign tuples) and other unsupported containers are rejected rather than silently
serialized into lists that bypass decoded-string scanning. Scanning is recursive;
there is no exemption for arbitrary metadata or identifier fields. Phone detection
uses ASCII alphanumeric boundaries so a decimal substring inside a hexadecimal digest
is not misclassified while adjacent Chinese prose still permits Taiwan mobile detection.
Injected scanners are trusted application dependencies. Pattern matching is defense in
depth, not a guarantee that every possible secret or malicious instruction is detected.
Never include credentials, raw sensitive outputs, or bearer URLs in evidence references.
This registry does not install skills into Hermes profiles or automatically execute text.

## Rejection, revocation, edits, rollback, transport

- `decision="reject"`: pending → rejected; that revision cannot later be approved.
- `decision="revoke"`: approved → revoked; that revision is no longer reusable.
- `revise_skill(skill_id, content, task_ids=None)`: create the next pending revision.
  The prior revision remains in history but is no longer current/reusable, even while the
  edit is awaiting approval. Use new task IDs for genuinely new executions.
- `rollback_skill(skill_id, historical_revision, reviewer=...)`: authorized reviewer
  creates a **new pending revision** using historical content/evidence. Rollback is not
  a way to resurrect an approval; review of the new revision is mandatory.
- `registry.get_revision` and `registry.list_skills` expose review/history data, not an
  alternative reuse gate. `list_skills` includes pending/rejected current revisions.
- `export_patterns` exports scoped observations and current skill revisions. Handle this
  user-requested export as sensitive data and store it in an owner-protected directory.
- `import_patterns` validates the entire same-scope bundle atomically. Imported approval,
  history, and verification claims never carry authority: imported skills are pending
  with unverified task evidence and import provenance. Reverify locally, create a new
  evidence snapshot with `revise_skill`, and obtain fresh human approval. Existing skill
  or task identities cannot be overwritten by transport. Legacy unscoped imports are
  rejected; legacy rule dictionaries are ignored, never enabled.

Observations themselves remain in memory unless explicitly exported; approved/draft
skill source snapshots, outcomes, reviews, history, and reuse comparisons persist when
`data_dir` is provided. Omit `data_dir` for a deliberately in-memory registry.

## Minimal runnable fixture example

The numbers/references below are **test fixtures**, not claims about a real task. A real
host must obtain those values from its actual run and validator before calling these APIs.

```python
from tempfile import TemporaryDirectory
from hermes_adapter import HermesAdapter

with TemporaryDirectory() as data_dir:
    options = dict(
        scope={"tenant": "acme", "brand": "atlas", "team": "content", "user": "owner"},
        reviewers={"human:alice"}, verifiers={"runner:qa"}, data_dir=data_dir,
    )
    adapter = HermesAdapter(**options)
    adapter.observe_access("us-en", "team", "write", True)
    pattern_id = next(iter(adapter.patterns))
    adapter.record_outcome(
        task_id="fixture-1", source_ref="fixture://run/1", result_ref="fixture://report/1",
        metric="defects", baseline=5, candidate=1, direction="lower", success=True,
    )
    adapter.verify_outcome("fixture-1", validator="runner:qa")
    pending = adapter.draft_lesson(pattern_id, "Check citations before delivery.", ["fixture-1"])
    approved = adapter.review_skill(pending["skill_id"], 1,
                                    reviewer="human:alice", decision="approve")

    # A second application-owned agent role reopens the same scope after handoff.
    consumer = HermesAdapter(**options)
    available = consumer.get_adaptive_recommendations("us-en", {"action": "write", "success": True})
    assert available[0]["digest"] == approved["digest"]
    consumer.reuse_skill(approved["skill_id"], 1, task_id="fixture-2")
    consumer.record_reuse_outcome(
        task_id="fixture-2", source_ref="fixture://run/2", result_ref="fixture://report/2",
        metric="defects", baseline=5, candidate=2, direction="lower", success=True,
    )
    consumer.verify_outcome("fixture-2", validator="runner:qa")
    comparison = consumer.compare_outcome("fixture-2")
    assert comparison["improved"] is True and comparison["delta"] == -3
    assert HermesAdapter(**options).compare_outcome("fixture-2") == comparison
    print("Reviewed fixture reused and compared after restart:", comparison["improved"])
```

Run acceptance tests with `python3 -m unittest discover -s tests -p test_learning.py -v`.
