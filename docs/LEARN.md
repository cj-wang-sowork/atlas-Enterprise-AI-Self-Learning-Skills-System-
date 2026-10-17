# Five-layer learning and reviewed reuse

ATLAS provides a scoped file-access library plus an outcome-reviewed skill registry.
It does not authenticate users, train model weights, automatically execute learned text,
or establish that repeated behavior is correct.

## Authoritative implementation guides

- [ACCESS_CONTROL.md](ACCESS_CONTROL.md): canonical tenant/brand/department/team/owner paths,
  trusted identity construction, authorize-before-read behavior, metadata, and migration.
- [LEARNING_LIFECYCLE.md](LEARNING_LIFECYCLE.md): outcome evidence, independent validation,
  human review, immutable revisions, persistence, revocation, handoff, and comparison.
- [SECURITY.md](../SECURITY.md): screening policy, DLP limitations, filesystem boundary.
- [VERIFICATION.md](VERIFICATION.md): actual measured checks and remaining acceptance work.

## Five audiences, not five global privileges

Enterprise knowledge is shared only inside its tenant. Brand knowledge requires the
selected brand; department/team knowledge requires exact scoped membership. Personal
knowledge is owner-only within its tenant and brand. `@public` does not grant anonymous
or cross-tenant access. A market code or role name never establishes identity.

Legacy `learn/<level>/...` paths are no longer accepted. Use `learn/<tenant>/...` layouts
and exact matching metadata from the access guide. Private runtime data belongs outside
the source checkout and is not suitable for Git.

## Reviewed learning loop

Observe → draft an explicit lesson → attach a measured baseline/candidate outcome →
validate the artifact → approve the exact revision → persist → select an approved
revision for the next task → measure again.

Only distinct, successful, verified, strictly improving outcomes support approval in
this reference implementation. Observations retain occurrence counts but correctness
confidence stays unknown. Humans reject or revoke unsuitable revisions; edits and
rollbacks create pending revisions that need a new review. Transported JSON cannot
carry approval authority into a new registry.

The application supplies authenticated human reviewers and outcome validators; do not
expose their methods as unrestricted agent tools. Keep protected per-scope storage and
serialize registry writes. See the lifecycle guide for a runnable synthetic fixture.

## Evidence is not a marketing benchmark

No historical DeepEval score, market-count claim, compliance certification, or generalized
productivity improvement is asserted by this version. A deterministic security-fixture
comparison measures only those named detector cases. Real task-quality improvement and
non-engineer onboarding time require separately executed representative evaluations.
