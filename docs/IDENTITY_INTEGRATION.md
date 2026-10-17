# Trusted identity integration (optional reference)

## What is real, and what is not configured

`integrations/trusted_identity.py` verifies real RS256 signatures through
PyJWT/cryptography and connects authenticated actors to the real `SkillRegistry`
and `LearnAccessControl`. Core modules remain dependency-free and unchanged.
The runnable example proves a persisted, reviewed Skill can be reused by a
**different authorized user after an actual process exit/restart**, while keeping
its configured resource owner unchanged.

**No live external IdP is configured or contacted.** The CLI uses explicitly
synthetic issuer/users, in-memory RSA keys and synthetic verification/human-review
fixtures. Its defect metrics demonstrate gates, not real business outcomes or a
model benchmark. This is a compact trusted-server reference, not a complete SSO
or OAuth client, web server, browser session implementation, or Python sandbox.

## Token and login boundary

This bridge accepts only a deliberately narrow **OIDC ID-token callback profile**
for a server-side authorization-code login integration. ID tokens are **not**
unrestricted API credentials. Subsequent facade operations accept only opaque
server-issued session handles; passing an ID token, an `Identity`, a user name,
or a self-claimed role as a session is denied.

- One fixed configured HTTPS issuer and single-string audience/client ID.
- Pinned, server-provisioned RSA public keys (2048 bits or larger), indexed by
  configured `kid`. Load approved PEMs with `serialization.load_pem_public_key`
  in trusted startup code. No network discovery occurs in this package.
- `algorithms=["RS256"]` is fixed, not taken from token data. Unknown `kid`,
  unsigned/HMAC/rogue signatures and all headers other than `alg`, `kid`, `typ`
  are rejected, including `jku`, `jwk`, `x5u`, `x5c` and `crit`.
- `typ` must be `JWT`. Require `iss`, `aud`, nonempty `sub`, integer `iat`/`exp`
  and `nonce`; signature, issuer, audience and expiration are checked by PyJWT.
  Reject audience arrays, future/older-than-300-second `iat`, lifetime over 300
  seconds, invalid optional `nbf`, and an `azp` other than the configured client.
  There is no clock-skew allowance. This strict profile can reject otherwise
  valid provider tokens; configure the provider appropriately rather than
  weakening validation based on request data.
- `begin_login()` creates a random nonce **and** random pending handle in server
  memory. `complete_login(handle, id_token)` compares against that stored nonce,
  expires the pending login after 300 seconds, and consumes it on the first
  attempt, including failed attempts. The caller cannot supply `expected_nonce`.
  Only `(issuer, subject)` is returned; other claims grant no authority.

A real embedding application **must** bind the pending handle to the correct
browser's trusted pending-login transaction, validate one-time OAuth `state`,
use PKCE and an exact registered redirect URI, securely exchange the authorization
code with the configured issuer, and invoke this callback only after those
checks. Never accept an arbitrary request's proposed nonce, issuer, key URL or
key material as trusted configuration. The demo supplies pending transactions
through private supervisor/worker pipes; it does not prove browser binding,
PKCE, callback routing or a live code exchange.

Local session handles expire after 300 seconds and are intentionally lost on
restart. A valid ID token at login creates a separate short-lived local session;
it is not stored or revalidated on each operation. Production must implement
secure HttpOnly/Secure/SameSite cookies, CSRF protection for mutations, session
revocation/logout/IdP lifecycle integration, HTTPS, redacted transport logs,
rate limits, pending-login/session storage limits and shared transactional
session storage if workers are replicated. Do not expose login internals or
fixture policy controls as generic agent tools. A provider SDK/OIDC client should
own the complete browser flow and applicable provider-specific claim checks.

## Server-owned authorization, actor versus owner

`ServerPolicy` maps **issuer + subject pairs** to distinct stable local user IDs
and explicit resource-bound role sets. `TeamResource` fixes tenant, brand,
department, team and library owner. Neither mapping comes from token tenant/team/
owner/roles claims, chat arguments, or user-submitted `AccessContext` objects.
Configured identifiers are validated before filesystem use. The exact resource
ID is selected from a server-owned catalog, not interpreted as a file path.

| Facade operation | Required role |
| --- | --- |
| `record_outcome`, `draft` | author |
| `verify_outcome` | verifier |
| `review` (approve/reject/revoke) | reviewer |
| `recommendations`, `reuse` | consumer |

Roles do not imply other roles. Reviewer/verifier IDs are derived from the
session's authenticated local user; there is no caller-supplied reviewer,
validator, resource owner or scope parameter. A real reviewer operation must
follow an actual authorized person's inspection; automation using synthetic
reviewer fixtures is not evidence of a live human approval.

Every operation rechecks current policy, then invokes core ACL checks, **before
constructing/opening any registry or creating its directory**. Trusted application
code can call `policy.set_roles(identity, resource_id, frozenset())` to remove a
membership; an already-issued session is denied on its very next access. The
policy object and `TeamService` instance must remain trusted server capabilities:
return data/receipts, not `_registry()`, raw adapters, or objects with reflective
Python access, to untrusted callers. This is authorization at an application
boundary, not isolation against malicious Python running under the service UID.

Each authorized operation opens a fresh registry, avoiding a stale in-memory
approval after another operation revokes it. Removing reviewer/verifier roles
also removes their current attestation trust on reload: historical snapshots
using those identities fail closed, rather than silently honoring an untrusted
approval. Applications needing separate historical trust/review revocation
policy must design that explicitly; do not assume removing a reviewer leaves
old artifacts reusable.

The shared library's core `scope.user` is a stable configured **resource owner**
(e.g. `team-library`), not the acting consumer. Author, verifier and reviewer
identities appear in source/attestation metadata. The consumer identity is
returned alongside its reuse receipt; the unchanged core persistence schema
stores the version/digest receipt, **not** that added consumer audit field.
Production should persist a separate protected actor audit log if needed.
No caller changes `registry.scope.user` to impersonate the owner.

## Storage and content boundary

The operator provisions an existing owner-only storage root under a trusted
absolute path with trusted ancestors. Resource directories are generated solely
from validated configured identifiers:

```text
<root>/<tenant>/<brand>/<department>/<team>/<owner>/registry.json
```

Including all these components keeps identical team names in different tenants,
brands or departments separate. Root and descendants are checked as real,
owner-only directories before registry reading; descendants are created 0700,
snapshots 0600. Symlinked or unprotected paths are rejected before snapshot reads.
This does not defend against a compromised service UID racing path replacements.
Core snapshots use integrity checksums, **not cryptographic authenticity** against
an attacker who can rewrite the trusted store. The reference is single-worker/
serialized-operation code, not a distributed concurrent-writer database.

The **actual numeric-aware core `SecurityChecker` and recursive `scan_safe` are
used without weakening or policy injection**, including numeric leaves, nested
assignments and private-key markers. An additional bridge screen refuses
compact-JWT-shaped learning content/evidence. Authentication tokens/private keys
never belong in lessons, sources, evidence, logs or Git. Unknown or denied scopes
are rejected before their data is read; safe error messages do not echo JWTs.

## Run and verify

At the **historical isolated identity-integration checkpoint**, the installed
and exercised set was CPython **3.9.6**, PyJWT **2.15.1**, cryptography **50.0.2**,
cffi **2.0.0**, pycparser **2.23** and typing_extensions **4.16.0** on macOS arm64.
Installed metadata requires Python >=3.9 for PyJWT and cryptography (cryptography
excludes 3.9.0/3.9.1). Other platforms/interpreters were not exercised at that
checkpoint. Versions are pinned as a tested set, not a claim to be latest.
The subsequent **integrated acceptance** ran CPython **3.12.12 / 94 tests / zero
skips**; see [current integrated evidence](E2E_ACCEPTANCE.md) and its machine result.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r integrations/requirements-oidc.txt
.venv/bin/python -m pip check
.venv/bin/python -c 'import jwt, cryptography'
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python examples/authenticated-team/demo.py --evidence "$TMPDIR/atlas-identity-evidence.json"
```

The evidence path must be new and outside the repository. The CLI prints the
same JSON it writes with mode 0600. Its signing private key stays only in parent
memory; fresh workers receive the same pinned public key and callback tokens
through private pipes, not process arguments or persisted key/token files. The
first worker exits before the second is launched. The second authenticates a
different consumer, retrieves/reuses the exact approved digest, rejects old
sessions, outsiders, foreign tenants/brands, revoked skills and removed members.
The internal worker protocol includes privileged fixture controls and **must not
be deployed/exposed as an API**.

Baseline: 63 pre-existing tests. Integration suite: 12 additional tests, including
real cryptographic adversarial tokens, pre-read denial guards, fresh-instance
reuse, and the CLI's real subprocess E2E. At that isolated historical checkpoint,
the full installed suite ran **75 tests, zero skips**, before the paired-evaluation
and usability modules were integrated. The integrated total is recorded in
[E2E acceptance](E2E_ACCEPTANCE.md). Without optional dependencies the integration tests skip gracefully;
that is acceptable for stdlib-only users but **not** for identity acceptance/CI.
The identity CI lane must install the pinned requirements and enforce no skips,
for example (after activating its venv):

```python
import jwt, cryptography  # fail fast if optional dependencies are missing
import unittest
suite = unittest.defaultTestLoader.discover("tests")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
```

TDD execution used vertical red/green slices: missing callback module; nonce
replay accepted; untrusted key headers/claim profiles accepted; missing team
facade; missing membership updates; invalid trusted config accepted; symlinked
parents read; raw compact JWT learning evidence accepted; missing executable
E2E; foreign `azp`/boolean `nbf` accepted. Each was observed failing before its
implementation/fix and rerun green. Negative tests for already-enforced scope
and role gates were added as regression coverage rather than weakening working
gates to manufacture failures. Baseline tests stayed unchanged.

## Primary references checked

- PyJWT usage: https://pyjwt.readthedocs.io/en/stable/usage.html
- PyJWT decode API and fixed-algorithm guidance: https://pyjwt.readthedocs.io/en/stable/api.html
- OpenID Connect Core ID-token validation and nonce/replay requirements:
  https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation

These inform the narrow callback verifier, not a claim that this example by
itself implements the full OpenID Connect/OAuth security requirements.
