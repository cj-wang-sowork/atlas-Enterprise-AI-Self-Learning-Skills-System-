# Next milestone: authenticated end-to-end acceptance

Baseline: main commit `8cb5eed2dfa1b8eba2eacc7abdc86a12d4c7535a` (PR #3 merged October 17, 2026, 14:01 Asia/Taipei). The earlier 63-method automated suite and four CI jobs were executed; they are not a live IdP or human-usability study.

## Acceptance matrix

1. **Trusted identity / P0**: optional standard-library-compatible core + explicit cryptographic verifier dependency in integration example. Authenticate signed identities, derive server-owned scoped grants, reject forged/expired/wrong-audience identities and cross-tenant requests before content reads. Demonstrate a reviewed shared skill surviving restart and serving a different authorized user while denying outsiders. Synthetic issuer/key/approval fixtures must be labelled; external production SSO is not implied.
2. **Controlled evaluation / P1**: pin identical task data, model/configuration and rubric across normal and ATLAS reference-skill conditions. Preserve real outputs, hashes, measured timings, usage when available, failed runs and limitations. Actual provider failures are failures, not synthetic results. A small public/fictional pilot is not representative business proof; human quality scoring remains a separate gate.
3. **Non-engineer ChatGPT study / P1**: provide a participant walkthrough, observer protocol and durable evidence recorder. Only actual consenting human non-engineers with observer-attested evidence qualify for human success/time metrics. Agent QA, simulations, unselected participants and missing data never count as successful humans. No human participant has yet been identified.
4. **Integration gates**: test-first changes, full original + new suites, isolated installs/dependencies, no production profile/config/client-data writes, independent review and exact-head CI before merge. Current connected account remains READ on the original repository; do not claim merge until provider read-back proves it.

## Scope limits

No new marketing features, no purported live external IdP deployment without credentials, no fabricated business uplift, no AI standing in for a human user, no automatic public outreach. Keep each limitation visible in reports rather than marking the whole milestone complete from a passing fixture subset.
