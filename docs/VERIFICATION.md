# Verification and remaining acceptance work

This is **implementation-level automated acceptance**, not a production security certification or a claim that every product/business acceptance criterion is finished.

## Reproducible evidence

- [Machine-readable run](verification-results.json): candidate code commit, execution time, actual Python/platform, collected method counts and remaining checks.
- [Full unittest output](verification-unittest.txt): named test methods and real runner summary.
- [Pinned detector comparison](security-comparison.json): each named fixture's expected and observed baseline/candidate result.

Run from a full Git checkout with Python 3.9+ on POSIX:

```sh
python3 -m unittest discover -s tests -v
sh -n scripts/install-workspace.sh
git diff --check
python3 scripts/compare_security.py
```

The comparison requires the pinned baseline Git object; use a full clone or fetch history. Installed context bundles are not Git clones and cannot reproduce that comparison without repository history.

## Automated acceptance results

The recorded run collected **63 test methods** (not 63 independent business trials):

- Scoped access: **13 methods PASS**. Tenant/brand/department/team/personal separation, trusted-context requirement, malformed scope/header, authorized hierarchy, traversal and symlink denial; body-read spies check denial before content retrieval. Authorized enterprise/brand/personal content is screened before direct/list/market returns; safe owner-personal files remain readable.
- Sensitive content: **10 methods PASS**. Unlabelled email, provider-key shapes, English/Chinese/JSON assignments, Unicode obfuscation, Taiwan PII shapes (including adjacent Chinese prose), exact email exceptions, deny terms, classification review gate, non-echoing audit, shared learning audit policy, and a deterministic hexadecimal-digest negative control.
- Learning lifecycle: **22 methods PASS**. Repeated failures do not authorize reuse; distinct verified outcomes and human review gate promotion; immutable revisions, rejection/revocation, rollback, stale-instance protection, imports, persistence/tampering, version-bound reuse/outcome comparison, rejection of nested non-JSON tuples before observation storage, numeric credential/PII screening, and no-mutation/default restart/import rejection of legacy unsafe numeric data.
- Installation: **17 methods PASS**, with multiple target subcases. Real shell execution for OpenClaw, Claude, Codex, Qwen, Hermes, `all`, and manual ChatGPT export; isolated homes, importable installed Python modules, backups/repeats/force, preflight conflicts and unsafe paths. No actual runtime profile was modified.
- Comparative harness: **1 method PASS**. Same 17 deterministic fixtures against baseline `525dcc2b27aa0c745c4ce7b1dfcf8672d4a4abd1` and the candidate: **5/17 → 17/17 correct**. These are curated detector fixtures with benign negative controls, not a representative DLP recall estimate.

The documented synthetic lesson was also approved, reopened by a fresh consumer, reused, and compared after restart. The fixture's metric values are illustrative test inputs, **not measured customer results**. No LLM or live agent runtime was invoked by that demonstration.

### Integration issue found and corrected

The first integrated installer run failed because macOS's default temporary path used the `/var` symlink alias, which the installer deliberately rejects. Test sandboxes now use canonical physical paths; safety checks were not weakened. The combined suite was rerun successfully. Production users must likewise use physical paths rather than symlink aliases.

## Independent-review blockers corrected with RED → GREEN regressions

1. **Tuple content bypass:** Python's JSON encoder accepted nested tuples while
   recursive screening skipped their contents. `scan_safe` now rejects unsupported
   containers, even benign tuples, before observation state or snapshots are written.
   The pre-fix regression recorded three failing assertions in one method.
2. **Authorized loader content bypass:** valid path scope and metadata previously let
   provider keys and unlabelled emails reach runtime context despite offline audit
   rejection. The common parser now uses the shared `SecurityChecker` before returning
   content. Direct reads raise sanitized errors; list and market loaders omit unsafe
   files; offline audits report invalid resources. The regression first failed all
   six enterprise/brand/personal × provider-key/email subcases. Safe owner access and
   authorize-before-open/bounded-header checks remain covered.

3. **Numeric JSON bypass:** valid numeric values were not screened as credential assignments or PII. The checker now scans the exact canonical JSON representation as well as decoded strings. Four previously failing numeric/nested cases are covered, together with observation no-mutation, protected snapshot reopen rejection, and atomic import rejection. An explicitly permissive test-only policy constructs legacy unsafe fixtures; the default policy must reject them.

During integration, a random SHA-256 substring also triggered the Taiwan mobile
pattern and caused a flaky persistence failure. A deterministic digest negative-control
regression first failed, then passed after ASCII-alphanumeric adjacency was excluded.
Taiwan mobiles adjacent to Chinese prose still fail screening. No arbitrary field is
exempted from scanning. RED logs are kept outside the repository; their local paths
are recorded in the machine-readable report. The final full run is tied to its
committed candidate code, with results committed separately.

## Still NOT verified / not implemented by this reference library

- A non-engineer successfully completing a first ChatGPT task within ten minutes. The manual kit is provided; its target duration is not a measured usability result.
- Authenticated live ChatGPT Project setup or live model behavior/discovery in each supported runtime. File placement/import tests are not UI or agent-runtime end-to-end tests.
- Production identity-provider integration, protected reviewer UI, enterprise DLP/classifier, data retention/deletion, OS/container tenant isolation, concurrent multi-writer registry service, or penetration testing. Trusted application identity and a serialized protected registry are prerequisites.
- Automatic extraction of lessons using an LLM or automatic execution/installation of learned text. Draft content is supplied explicitly; approval does not execute it.
- General productivity/quality superiority over an ordinary AI/prompt workflow. The detector regression does not establish that claim.
- Hosted CI at the time of the recorded local run. The included workflow defines Linux/macOS and Python 3.9/3.12 jobs; only actual completed workflow results can verify those environments.

## Product-benefit comparison protocol (not yet run)

To evaluate the final business claim without inventing results:

1. Freeze a representative, de-identified task set across brand positioning, research and content, with approved brand revisions and independently checked sources.
2. Run a normal AI workflow and ATLAS with the **same model/version, tool budget, inputs, task order policy and success rubric**. Isolate their memory and test on held-out tasks after learning.
3. Predefine output-quality rubric, factual/brand violations, cross-scope leakage, task success, human revision time, elapsed time, model/tool cost and approval effort. Collect real artifacts and measured timings, not model self-scores alone.
4. Use blinded authorized human scoring; count failed tasks and guardrail denials rather than excluding them. Report sample size, raw paired results, uncertainty and regressions.
5. Publish only source-backed aggregates after privacy review. Keep “better on these tasks” separate from a general improvement claim.

Do not mark the unrun checks above as PASS merely because the automated suite is green.
