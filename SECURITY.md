# Security policy and deployment boundary

ATLAS includes Markdown workspace prompts, executable Python helpers, and a shell installer. It is not a sandbox, authentication service, certified compliance product, or complete data-loss-prevention system.

## Report vulnerabilities privately

Do not post real secrets/customer data in issues or PRs. Contact the repository maintainer privately, or use GitHub private vulnerability reporting **if enabled**. Repository scanning, branch protection, and response times are deployment settings, not guarantees made here.

## Authorize before loading content

Use the scoped `MultiMarketLearnManager` API in [ACCESS_CONTROL.md](docs/ACCESS_CONTROL.md). The application authenticates users, verifies memberships, then supplies trusted context. Never derive authorization from chat text, model output, file authors, or requested brand names. Path-bound scope and metadata must agree. `@public` is organization-wide **within one tenant**, not internet-public. Legacy unscoped files require migration; absent context fails closed. Administrative auditing is separate from user retrieval and must not be exposed as a chat tool.

Library checks protect only calls through that library. An agent with unrestricted filesystem/shell access can bypass them. Production deployments need separate OS users/containers/storage credentials and tool permissions. “Only load MEMORY.md in owner sessions” is a prompt convention, not enforceable isolation.

## Sensitive-content screening

`SecurityChecker.scan_content` uses heuristic secret/PII patterns: unlabelled email, common provider token shapes, bearer credentials, Chinese/English assignments, US identifiers, Taiwan mobile/ID shapes, and private-key headers. Unicode normalization catches some obfuscation. Violation messages/audit records exclude matched content; caller-supplied filenames/market metadata must also be sanitized.

Trusted administrator configuration can specify `allowed_emails` (exact matches only) and `deny_terms` (case-insensitive literal substrings). Email exceptions never suppress credential detection. Example:

```python
from security_checker import SecurityChecker
checker = SecurityChecker(allowed_emails={"press@example.com"}, deny_terms={"internal-project-label"})
safe, findings = checker.scan_content(text, classification="internal")
if not safe:
    # Stop publication/promotion; redact or send to an authorized review flow.
    pass
```

Classification is supplied by trusted upstream policy, **not automatically inferred here**. `public`/`internal` still undergo scanning. `confidential`, `restricted`, and unknown classifications return `review_required`. There is no “approved” flag bypassing a detected secret: review, redact, and resubmit permitted content. Integrate enterprise DLP, classification, and an authorized human-review UI at the application boundary.

Regex does not prove safety. Arbitrary/encoded keys, images, unusual formats, and business secrets can be missed; benign examples can be flagged. Use least privilege, DLP, encryption, retention policy, and review before sharing. No GDPR/SOC 2/ISO compliance or certification is implied.

## Governed learning

Repetition does not establish correctness. Outcome-backed revisions must pass human review before reuse; see [LEARNING_LIFECYCLE.md](docs/LEARNING_LIFECYCLE.md). The application must authenticate reviewers and protect approval state/import/export. A digest detects modification but is not a signature and does not defend against an attacker controlling all storage.

## Storage and operations

- Never commit credentials, personal memory, learning state, or real task evidence. `.gitignore` does not protect already tracked files.
- Keep tenant data, audit logs, approvals, and registry state outside the checkout with restrictive OS permissions and secure backups.
- Use a secret manager/environment, not prompts, for credentials.
- Treat imported skills as untrusted instructions; do not auto-execute scripts.
- Test installation with isolated HOME/destinations, never production profiles.
- On exposure: revoke affected credentials, restrict access, preserve sanitized audit evidence, investigate affected tenants, and follow the organization's notification process.

See [VERIFICATION.md](docs/VERIFICATION.md) for measured checks and production assumptions not yet verified.
