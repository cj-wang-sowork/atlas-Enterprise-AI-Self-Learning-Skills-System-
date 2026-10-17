# Controlled paired evaluation

This harness compares **the same task and the same source records** with and without
an added ATLAS reference-skill instruction packet. It measures actual executions,
not a security-fixture comparison or a fabricated model demonstration.

The checked-in pilot is `studies/paired-pilot/REPORT.md`. It contains genuine model
outputs for three fictional marketing briefs, not real customer business proof.

## What the treatment means

- **Baseline:** a complete marketing brief, identical source records, draft-only
  safeguards and an explicit output contract. No ATLAS reference packet.
- **ATLAS reference:** exactly the baseline prompt plus the checked-in
  `skills/brand-positioning.md` workflow packet and its applicability wrapper.
- This is a **reference-skill prompt condition**, not a fully authenticated,
  human-approved self-learning deployment. A file existing in Git does not mean
  a reviewer approved a brand policy or a learned revision.
- No brand guideline, customer result, learned approval or human score is invented.
  Outputs remain drafts. No host identity or learning API is exercised.

## Controls and evidence

Each task appears once per arm. Seeded task order and alternating within-pair
order are fixed before execution. With three pairs, first-arm positions are 2:1,
not perfectly balanced; use an even number of tasks/repetitions for a larger study.

Both arms use the same explicit model, reasoning effort, provider configuration,
CLI version, data, brief, sandbox and available tool policy. The packet is the
only prompt difference. Extra prompt tokens are part of the treatment, not free.
The provider can change its backend; the requested model identifier is pinned,
but an unreturned model build/version remains unknown.

Working directories are separate, empty and outside all Git repositories.
Codex uses `--ignore-user-config --ignore-rules --ephemeral
--skip-git-repo-check --sandbox read-only`, plus
`project_doc_max_bytes=0`. No repository `AGENTS.md`, `MEMORY.md`, other arm output,
or private runtime profile is intentionally loaded. Existing authorized CLI auth
is reused in place; credentials are never copied into the study.

The prompt forbids all tools and network tasks. Read-only is **not** the same as
an OS-enforced no-read/no-network sandbox. Completed tool events are checked and
make the run fail; absent events are not proof against an unreported provider
operation. This pilot recorded zero tool events in either arm.

Every arm retains its prompt, original final-response bytes, sanitized event log,
output SHA-256, measured process wall time, exit status, returned usage and gates.
Errors/timeouts are retained. No retry, output repair or best-of-N selection is
performed. Missing usage and dollar costs are `null`, not estimated from a
subscription. Cache-token fields are reported as returned, not added to input
counts. Wall time includes CLI startup and network latency, not human work.

`dataset_digest` is SHA-256 of canonical JSON (UTF-8, sorted keys, compact
separators); file-byte hashes are separately recorded. `manifest.sha256` locks
the final manifest and its artifact digests. Git anchors the resulting files;
these hashes are integrity checks, not authenticated signatures.

## Run safely

Python 3.9+ on a POSIX system and an authorized Codex CLI are required. The runtime
harness has no non-standard Python dependencies. Importing `evaluation` or
`evaluation.paired` does not execute a provider. The JSON schemas are in
`evaluation/schemas/`; the Python validator additionally checks source/task ID
uniqueness and regex validity.

First run a single nonsecret smoke request against the explicit model. If it is
rejected, retain the failure and stop rather than guessing another model. The
pilot's original CLI 0.133.0 failed; a separately authorized scratch-only npm
installation of 0.163.0 succeeded. No global CLI or user config was upgraded.
Do not repeat that pilot: its eight-invocation allowance has already been used.

For a **new, separately authorized** experiment, use a compatible isolated CLI:

```sh
CODEX="/absolute/path/to/compatible/isolated/codex"
"$CODEX" --version
python3 -m evaluation.paired run \
  --dataset studies/paired-pilot/fixtures/tasks.json \
  --packet studies/paired-pilot/fixtures/reference-packet.txt \
  --output "$HOME/.hermes/cache/scratch/paired-new-plan" \
  --scratch-root "$HOME/.hermes/cache/scratch/paired-new-taskdirs" \
  --codex-binary "$CODEX" --model gpt-6-astra --max-calls 6 \
  --timeout-seconds 90 --total-timeout-seconds 540 --seed 17
```

This creates a **dry plan**, with all runs `not_run`. Use a new output directory
and add `--execute` only after authorization to make the six actual calls.
The runner never overwrites an existing output directory. The per-study call
budget must cover the whole schedule and cannot exceed eight. Smoke calls are
separate and must be included in the operator's overall allowance.

An explicit `--provider-command-json '["/absolute/executable", "{prompt}",
"{output}"]'` adapter is also supported. It is argv, never a shell command; it
must implement the Codex JSONL protocol and write the final response to `{output}`
or emit an `agent_message`. No provider response is synthesized. A new provider
requires its own matched configuration/version evidence; the Codex controls are
not magically enforced for arbitrary executables.

Verify the committed pilot without making model calls:

```sh
python3 -m evaluation.paired verify studies/paired-pilot/run-20261017
python3 -m unittest discover -s tests -p test_paired_evaluation.py -v
```

## Deterministic checks are not business-quality scores

- `format`: JSON draft contract, headline count/word limits, nonempty claims/gaps.
- `source_refs`: every explicit claim cites supplied source IDs.
- `claim_allowlist`: each explicit claim text exactly equals its cited record.
- `required_facts`: task-required substrings occur in the explicit claims array.
- `forbidden_claims`: lexical regex scan over the **entire response**, including
  gaps. This is a coarse screening flag, not semantic truth verification.
- `tool_free`: zero completed non-message/non-reasoning/non-plan item events.

Creative prose can imply unsupported claims despite passing these checks.
Conversely, a disclaimer can trigger the lexical scan. The pilot actually
contains that false positive; the frozen results were **not** rescored to hide it.
A 3/3 versus 2/3 gate count is therefore not evidence that ATLAS produced better
business copy. The execution-time harness snapshot is preserved; later validation
hardening is separately explained in the report.

## Independent human evaluation (not performed yet)

Use `studies/paired-pilot/HUMAN_RUBRIC.md`. Give each independent rater only a
copy of `run-20261017/human-scoring.json` and the rubric, not the manifest,
prompts, report, source snapshot or `unblinding-DO-NOT-SHARE.json`. The form embeds
original outputs under opaque randomized IDs and leaves all ratings blank.
Style can still disclose a condition; blinding is attempted, not guaranteed.

Recruit at least two independent domain raters. Preserve their separate forms,
then unblind and report paired differences and disagreement. Record measured
editing time with a timer, not a language-model estimate. Define customer task
sampling, KPI windows, acceptance criteria and approval authority before any
representative business-impact study. Until those steps happen, human quality,
productivity benefit, ROI and generalized superiority remain **unmeasured**.
