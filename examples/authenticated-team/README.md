# Authenticated team acceptance example

**Synthetic fixtures, not live SSO.** The optional bridge verifies real RS256
signatures using PyJWT/cryptography. Its in-memory fixture issuer is not an
external identity provider. All people, approvals, metrics and resource names in
this harness are explicitly synthetic. The metrics exercise lifecycle gates;
they are not a measured improvement claim about ATLAS.

From the repository root, with Python 3.9+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r integrations/requirements-oidc.txt
.venv/bin/python -m unittest discover -s tests -p test_identity_integration.py -v
.venv/bin/python examples/authenticated-team/demo.py
```

To keep machine-readable proof, pass `--evidence` with a **new path outside the
repository**, for example `$TMPDIR/atlas-identity-evidence.json`. The output file
is created exclusively with mode 0600; an existing file is never overwritten.
The same JSON is printed to stdout. Runtime libraries are temporary and deleted
when the run finishes. No JWT/private key is written to disk or emitted in the
report; private RSA material exists only in supervisor memory.

The harness launches one worker, obtains scoped author/verifier/reviewer sessions,
records synthetic verified evidence, drafts and approves a Skill, **exits the
worker**, then starts another worker with the same pinned public key and store.
A different authenticated consumer reuses the exact approved digest without
changing its owner. It also exercises forged signatures, wrong/replayed nonce,
self-claimed reviewer, outsiders, same-named foreign tenants/brands, revoked
skills, removed memberships and numeric-sensitive content.

`--worker` is an internal privileged subprocess test protocol, not an HTTP
endpoint or a deployable API. Do not expose its stdin to untrusted clients: its
fixture controls deliberately represent trusted policy administration.

See `docs/IDENTITY_INTEGRATION.md` for the trust boundary, narrow callback token
profile, mandatory no-skip verification, and production integration requirements.
