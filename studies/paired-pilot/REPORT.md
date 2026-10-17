# ATLAS / non-ATLAS controlled paired pilot

The **72-test** record in `verification.json` is the historical isolated paired-
evaluation checkpoint, not the integrated suite total. Subsequent integrated
acceptance ran **94 tests with zero skips**; see [E2E acceptance](../../docs/E2E_ACCEPTANCE.md).
Original model outputs and the historical checkpoint are preserved unchanged.

## Outcome and claim boundary

On October 17, 2026, **all six actual paired task executions completed**: three
fictional marketing briefs, one fresh run per arm. No model outputs were invented,
repaired, selected from retries or substituted. All original final-response texts
and actual provider usage events are retained.

**This pilot does not establish a business-quality or productivity benefit for
ATLAS.** Independent human review is **not run**, with **zero raters** and no
selected participant. No customer conversion, revenue, ROI or measured human
editing time exists. Internal failure notifications are not human study input.

The treatment is the **reference-skill prompt condition**, not an authenticated,
human-approved self-learning deployment. Brand approval, protected knowledge
loading, learning promotion and publication were neither supplied nor performed.

## Scope and controls

- All three tasks and organizations are explicitly `source_kind: fictional`:
  a Seattle repair workshop, US salon scheduling service, and Austin pantry kit.
  They are plausible marketing exercises, **not real customer cases** or a
  representative task sample. Each has three fixed factual source records.
- Both arms receive the identical brief, source records and JSON response contract,
  with the same draft/evidence safeguards. Baseline is a fully specified normal
  request, not deliberately missing information.
- The reference arm alone adds the exact checked-in
  `skills/brand-positioning.md` packet and an applicability wrapper. Its examples
  are reference workflow material, not evidence for these fictional businesses.
- Requested model: **gpt-6-astra**, reasoning **low**, OpenAI provider through
  **Codex CLI 0.163.0**. Backend-resolved model/build was not returned and remains
  null. Temperature and generation seed are provider defaults, not controlled
  sampling claims. Seed **17** controls only the schedule.
- Same CLI/config/sandbox/tool policy for both arms; independent empty task
  directories outside repositories. User config/rules and project docs are
  disabled by recorded flags. The prompt forbids tools and external research;
  event logs show **zero tool calls**. Read-only is not OS-enforced no-read or
  no-network isolation; provider event completeness is a limitation.
- Task order is seeded and first arm alternates baseline/reference/baseline.
  Three pairs cannot give exact 1:1 first-arm balance. No conversations or arm
  outputs are passed to later calls. The longer packet's tokens are a real
  treatment overhead, not controlled away.
- Per-call deadline 90 seconds, total deadline 540 seconds, six planned calls.
  One execution per arm/task; no task retries. All failures would remain in the
  manifest. Actual paired failures: **0**.

## Actual results (not human quality scores)

| Condition | Executions completed | All narrow gates passed | Total wall seconds | Mean wall seconds | Input tokens | Cached input tokens (subset) | Output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 3/3 | 2/3 | 27.357 | 9.119 | 50,131 | 36,864 | 811 |
| atlas_reference | 3/3 | 3/3 | 30.674 | 10.225 | 56,287 | 36,864 | 857 |

Total paired-study elapsed wall time, including orchestration: **58.043
seconds**. Per-call times include startup/network/model work, not human labor.
The reference condition took **3.317 seconds more aggregate wall time
(+12.12%)** in this one small sample. This is not a stable latency estimate.
Both arms returned zero reasoning-output and zero cache-write tokens. Token
fields are exactly those returned by `turn.completed`; cached tokens are not
added to input totals. **Dollar cost is unknown/null**: no provider billing was
available, and subscription access is not a cost estimate.

| Task | First condition | Baseline seconds | Reference seconds | Baseline all gates | Reference all gates |
|---|---|---:|---:|---|---|
| harbor-workshop | baseline | 9.138 | 11.889 | True | True |
| loom-scheduler | atlas_reference | 9.560 | 9.248 | True | True |
| sprout-crate | baseline | 8.659 | 9.537 | False | True |

### The apparent gate advantage is a false positive, not a quality win

Both arms passed the JSON format, explicit-claim allowlist, source-reference,
required-fact and tool-event checks on **all three tasks**. The frozen lexical
`forbidden_claims` scan flagged baseline `sprout-crate` because its **gaps** field
says that no evidence supports several claims, including `free delivery`.
See `run-20261017/outputs/run-05.txt`, gaps array (line 29).

That is a disclaimer, not an assertion that delivery is free. It illustrates the
scanner's inability to interpret negation and field context. The recorded 2/3
versus 3/3 gate count is retained unchanged for auditability, **not interpreted as
ATLAS superiority**. This analyst inspection is not an independent human score.
Creative prose remains outside the explicit claims-array entailment check in
both arms and still needs expert review.

## Connectivity recovery and invocation accounting

The original Homebrew CLI **0.133.0** really attempted the explicit model and was
rejected: it requires a newer Codex CLI. `smoke-initial-codex-0.133.0.log` preserves
that failure; a large public model-catalog error body is omitted and marked.
Its wall time was not harness-measured and is unknown, not reconstructed.

The parent then explicitly authorized a scratch-only compatible CLI. npm registry
metadata reported **@openai/codex 0.163.0**, which was installed only under scratch.
A second nonsecret smoke returned `ATLAS_PILOT_SMOKE_OK`, followed by the six
paired task calls. **Eight actual CLI model invocations total: one rejected smoke,
one successful smoke, six completed paired calls.** No alternate model was used
and no further model calls were made. The global CLI remained 0.133.0; user
config/auth files were not deliberately edited or copied. Existing authorized
auth was reused in place. See `provenance.json` for the invocation ledger and npm
package integrity.

## Reproducible evidence

- Baseline repository revision: `8cb5eed2dfa1b8eba2eacc7abdc86a12d4c7535a`.
- Canonical dataset SHA-256: `efaf7037a453606a12158b10e367bfb667f4287ade445803ef5f535653e3f7b0`.
- Original fixture file-byte SHA-256: `8c9a0aa690ebd59e75fa3380ef182f990c89aab5d7afe9e56fb3c3533f4a306f`.
- Reference packet SHA-256: `271413d56bf96e96af39df0acc3177f2e500e7ae520f8c608e14ebd50f8f69f3`; verified byte-for-byte
  against `skills/brand-positioning.md` at that baseline revision.
- Execution-time harness SHA-256: `5792412435f958e8970f350ac7076b88b027302cb71aa46530da5073775996fd`,
  preserved as `runner-at-execution.py.txt`. It was newly written/uncommitted at
  execution; it is not falsely attributed to the earlier repository revision.
- Final manifest SHA-256: `32e3afb874a8b824858fdb73fa35da9b60d2b3f79cf8b756d1f1b8de0f38161d`.
- `run-20261017/manifest.json`: pinned inputs/config/runtime, order, per-arm
  timings, actual usage, failures, scores null and every prompt/output/log digest.
- `run-20261017/prompts/`, `outputs/`, `logs/`: all six original artifacts.
  Logs are sanitized for common credential forms and home-directory paths;
  fictional final-response artifacts are preserved unchanged.
- `run-20261017/human-scoring.json`: opaque shuffled output labels, exact original
  outputs, blank rater fields and null scores. The separately stored unblinding
  key **must not be shared with raters**. Style-based unblinding is possible.
- `HUMAN_RUBRIC.md`: independent review administration and five anchored dimensions.

The main harness later received optimized-Python format-validation hardening
(`assert` removal), preflight rubric/argv validation, stricter task-lock checks,
and deadline handling for children that close their terminal early. The trial
ran ordinary Python 3.9.6, and no result files were rewritten. Rechecking all six
outputs with the hardened code gives the same recorded gates. The execution-time
snapshot remains the authoritative source for the original measurement.

## What is still required for business evidence

Collect separate ratings from at least two independent human domain reviewers,
measure editing time if productivity is a claim, and preserve disagreements.
A larger predeclared study needs authorized real customer tasks, representative
sampling, repeated/counterbalanced runs and measured business KPI windows. No
p-value, statistical significance, human preference or generalized ROI is
asserted by this pilot. See `../../docs/CONTROLLED_EVALUATION.md` for reproduction
and limitations; its verify command does not make model calls.
