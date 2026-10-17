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
python3 scripts/compare_security.py
```

The comparison requires the pinned baseline Git object; use a full clone or fetch history. Installed context bundles are not Git clones and cannot reproduce that comparison without repository history.

## Automated acceptance results

The recorded run collected **58 test methods** (not 58 independent business trials):

- Scoped access: **12 methods PASS**. Tenant/brand/department/team/personal separation, trusted-context requirement, malformed scope/header, authorized hierarchy, traversal and symlink denial; body-read spies check denial before content retrieval.
- Sensitive content: **9 methods PASS**. Unlabelled email, provider-key shapes, English/Chinese/JSON assignments, Unicode obfuscation, Taiwan PII shapes, exact email exceptions, deny terms, classification review gate, non-echoing audit, and the same policy in learning audits.
- Learning lifecycle: **19 methods PASS**. Repeated failures do not authorize reuse; distinct verified outcomes and human review gate promotion; immutable revisions, rejection/revocation, rollback, stale-instance protection, imports, persistence/tampering, and version-bound reuse/outcome comparison.
- Installation: **17 methods PASS**, with multiple target subcases. Real shell execution for OpenClaw, Claude, Codex, Qwen, Hermes, `all`, and manual ChatGPT export; isolated homes, importable installed Python modules, backups/repeats/force, preflight conflicts and unsafe paths. No actual runtime profile was modified.
- Comparative harness: **1 method PASS**. Same 17 deterministic fixtures against baseline `525dcc2b27aa0c745c4ce7b1dfcf8672d4a4abd1` and the candidate: **5/17 → 17/17 correct**. These are curated detector fixtures with benign negative controls, not a representative DLP recall estimate.

The documented synthetic lesson was also approved, reopened by a fresh consumer, reused, and compared after restart. The fixture's metric values are illustrative test inputs, **not measured customer results**. No LLM or live agent runtime was invoked by that demonstration.

### Integration issue found and corrected

The first integrated installer run failed because macOS's default temporary path used the `/var` symlink alias, which the installer deliberately rejects. Test sandboxes now use canonical physical paths; safety checks were not weakened. The combined suite was rerun successfully. Production users must likewise use physical paths rather than symlink aliases.

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
