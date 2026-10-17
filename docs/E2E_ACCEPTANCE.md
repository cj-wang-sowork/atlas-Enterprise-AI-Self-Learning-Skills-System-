# Authenticated E2E and controlled-evaluation acceptance

This is executable reference-implementation evidence, **not a production-readiness certificate**. It extends main `8cb5eed2dfa1b8eba2eacc7abdc86a12d4c7535a` without pretending that cryptographic fixtures, a fictional-brief model pilot, or an agent-operated recorder are real customers or human users.

## Evidence actually executed

- [Machine-readable acceptance result](e2e-acceptance-results.json): **94 test methods, 0 failures, 0 errors, 0 skips**, on macOS/CPython 3.12.12 with asserted pinned optional dependency versions. [Complete unittest output](e2e-unittest.txt).
- A separate real two-process identity demo returned exit code 0 in both workers. A different authenticated synthetic consumer reused the **identical reviewed Skill digest** after restart; 12 negative checks passed, including forged signatures, foreign scope, nonce replay, removed membership, revoked Skill and unsafe numeric data.
- [Six real model task outputs and paired-pilot report](../studies/paired-pilot/REPORT.md), three explicitly fictional marketing tasks × two conditions. Artifact verification returned `verified: true` with no errors. The execution-time harness is preserved separately from later validation hardening.
- [Recorder CLI QA evidence](../studies/usability/agent-qa-report.json): actual start/step/finish/reopen/report operations, explicitly excluded from human-usability metrics. **No real human has participated.**

The runtime code/test commit at local execution is recorded in the machine result. Later README/CI/report edits do not retrospectively alter original model outputs or make hosted CI already executed. GitHub CI must pass for the final PR head before integration.

## Acceptance status by requirement

### P0 — trustworthy identity source and isolation

**Implemented and executed as a reference integration.** [Identity integration](IDENTITY_INTEGRATION.md) provides pinned RS256 callback verification, one-time trusted nonce consumption, opaque sessions and server-owned resource/role grants. Tenant/brand/department/team isolation is checked before persisted reads. Identity is not accepted from chat arguments or self-asserted role/tenant claims. The shared resource owner stays `team-library`; an authorized consumer is not impersonated as that owner.

The issuer, RSA key, users and approval actors in the demo are **synthetic test fixtures**. They exercise real cryptographic verification and persisted Skill reuse; they are not a live external IdP or evidence that a real person approved a lesson. Full OAuth browser/state/PKCE/session binding, trusted key rotation, authoritative user provisioning, deployment isolation and production operations remain embedding responsibilities.

### P1 — same-task, same-data comparison

**Harness and small pilot executed; business benefit unproven.** Both arms used the same requested model/config/data and a frozen rubric. Baseline aggregate wall time was **27.357 s**; the ATLAS reference-prompt condition was **30.674 s**. Frozen narrow gates were baseline **2/3** and reference **3/3**, but the baseline's sole flag was a **lexical false positive** on a disclaimer denying evidence for “free delivery.” Do not present that difference as better quality or uplift.

The reference arm used a checked-in workflow prompt, **not** a newly learned Skill approved by a real human through the authenticated service. The provider did not expose an independent model build identifier. Human quality ratings have not run; monetary cost remains unknown. A representative customer task study with independent ratings is still required to claim improved business results.

The public repository contains the pilot's allocation key/report. The isolated rating bundle is prepared for attempted blinding, not guaranteed blind; a future real study must keep its fresh allocation key private until independent scores are locked.

### P1 — non-engineer ChatGPT onboarding

**Protocol and durable recorder executed; genuine participant trial pending.** [Participant/observer instructions](CHATGPT_USABILITY_STUDY.md) require actual consent, an observer-attested non-engineer participant, first-attempt timing, step/blocker records and sanitized task evidence. Failure and unfinished sessions remain in the denominator. Agent QA and simulated fixture humans never count.

Observed human participants: **0**. Human success rate and median successful duration: **null**, not 0% or 100%. A consenting non-engineer and observer must perform the real ChatGPT workflow before this acceptance gate can pass. The recorder cannot authenticate a human or prove the task output really came from ChatGPT; those are explicit observer responsibilities.

## Reproduce from a full source checkout

Use a private scratch checkout/virtual environment, not production user profiles. Clear inherited Python import-path settings before dependency validation; the final recorded run asserts both installed metadata and the loaded module locations.

```sh
python3 -m venv .venv
. .venv/bin/activate
unset PYTHONPATH PYTHONHOME PYTHONUSERBASE PYTHONSTARTUP
export PYTHONNOUSERSITE=1
python -m pip install -r integrations/requirements-oidc.txt
python -m pip check
python -c 'import jwt, cryptography, unittest; r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover("tests")); raise SystemExit(0 if r.wasSuccessful() and r.testsRun >= 94 and not r.skipped else 1)'
python examples/authenticated-team/demo.py
python -m evaluation.paired verify studies/paired-pilot/run-20261017
```

These reproduction commands do **not** make provider/model calls. Repeating an actual model study is a separate opt-in command, with an explicit budget and fresh artifacts; see [controlled evaluation](CONTROLLED_EVALUATION.md). Standard-library-only discovery may skip the optional identity tests; that is not an identity acceptance pass. The hosted identity CI lanes explicitly install dependencies and reject skips.

## Outstanding adoption gates

- Configure and exercise an actual external IdP and complete browser/session/deployment security integration.
- Recruit a consenting non-engineer and run the actual ChatGPT Starter Kit trial with an observer; retain evidence and record genuine blocker/time outcomes.
- Agree on representative sanitized customer tasks and independent raters, then preregister and run a fresh business comparison. Treat failure/no improvement as valid evidence.
- Exercise installation/discovery inside each live intended agent runtime. An isolated installer filesystem test or a tool-free Codex prompt call is not proof of the entire ChatGPT/Claude/Codex installation flow.

Do not collapse these outstanding gates into “all E2E complete” simply because the reference suite passes.
