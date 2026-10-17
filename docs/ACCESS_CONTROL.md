# Scoped learning-file access

## Trust boundary

`MultiMarketLearnManager` authorizes a canonical **path scope before opening a
learning file**, then validates its bounded metadata header before reading its
body. Tenant, brand, department, team and personal ownership are not inferred
from a market code or a `LearningLevel` supplied by a caller.

The embedding application must authenticate the user and obtain memberships
from its trusted identity/authorization store. Construct `AccessContext` on the
server from that identity, **not from user input, a prompt, an LLM tool argument,
frontmatter, or unverified client claims**. `AccessContext` is an immutable value
object, not an authentication provider, signed token, or verifier. Possession of
a Python constructor does not establish an authenticated identity.

```python
from learn_system import AccessContext, LearningLevel, MultiMarketLearnManager

# These values must come from the application's authenticated session and ACLs.
identity = AccessContext(
    tenant_id="acme",
    brand_id="alpha",
    user_id="alice",
    department_ids=frozenset({"marketing"}),
    team_ids=frozenset({("marketing", "social")}),
)
manager = MultiMarketLearnManager("/srv/atlas/workspace")
files = manager.load_learn_files(identity)
team_files = manager.load_learn_files(identity, level=LearningLevel.TEAM)
us_files = manager.get_market_context("us-en", identity)
one_file = manager.load_learn_file(
    manager.learn_root / "acme/team/alpha/marketing/social/notes.md", identity
)
```

An identity selects one tenant and one brand. Department memberships are local to
that tenant/brand. Team memberships are `(department_id, team_id)` pairs local to
that tenant/brand, not globally unique display names. The application should
construct a separate context after authorizing a tenant/brand switch. Identity
identifiers must match `[A-Za-z0-9][A-Za-z0-9_-]{0,127}` exactly; they are not
normalized. Membership collections must be immutable `frozenset` values.

## Canonical resource paths and policy

Paths are relative to the trusted workspace's `learn` directory. `...` represents
optional nested folders followed by a `.md` file; nesting does not change scope.

| Level | Canonical path | Required marker | Readers |
| --- | --- | --- | --- |
| Enterprise | `learn/<tenant>/enterprise/.../file.md` | `@public` | Any authenticated identity in **that tenant** |
| Brand | `learn/<tenant>/brand/<brand>/.../file.md` | `@internal` | Selected tenant and brand |
| Department | `learn/<tenant>/department/<brand>/<department>/.../file.md` | `@internal` | Department members or members of a team in that department |
| Team | `learn/<tenant>/team/<brand>/<department>/<team>/.../file.md` | `@team-private` | Exact department/team membership in selected tenant/brand |
| Personal | `learn/<tenant>/personal/<brand>/<owner>/.../file.md` | `@private` | Exact owner in selected tenant/brand |

`@public` means within-tenant, **not Internet-public or cross-tenant**. A team
member can read its department, brand and enterprise ancestors. Department
membership alone does not grant all of its teams. Personal files are owner-only;
there is no level-based administrator exception. Same-named teams in different
brands or departments do not share access. A market filter never grants access.

## Required metadata

Use a UTF-8 flat `key: value` header, delimited by exact `---` lines with newlines.
The opening fence must be the first line. Headers are limited to 16 KiB including
fences. Duplicate keys, malformed entries, missing/unterminated fences, invalid
UTF-8, empty values and unknown/mismatched access markers are rejected. Simple
matching quotes around scalar values are accepted; this is **not a general YAML
parser** and YAML nesting, aliases, collections and multiline scalars must not
be used for authorization fields.

Example: `learn/acme/team/alpha/marketing/social/notes.md`:

```text
---
tenant_id: acme
level: team
access: @team-private
brand_id: alpha
department_id: marketing
team_id: social
market: us-en
author: alice
---
Learning body.
```

Every file requires `tenant_id`, `level`, and `access`. Add exactly the scope
identifiers represented by its path:

- Enterprise: no additional scope identifiers.
- Brand: `brand_id`.
- Department: `brand_id`, `department_id`.
- Team: `brand_id`, `department_id`, `team_id`.
- Personal: `brand_id`, `owner_id`.

All these authorization fields must match the path exactly. Additional scope
fields that do not apply to the level also cause rejection. Non-authorization
metadata such as `market`, `author`, and `created` does not grant permissions;
`author` is not the personal owner. Missing `author`/`created` retain display
fallbacks, but scope fields have **no defaults**.

## Read and failure behavior

1. Require an application-supplied `AccessContext`; dictionaries and old level-only
   callers are denied.
2. Derive and authorize the canonical path scope. Cross-scope paths are rejected
   without opening their metadata or body.
3. Open relative to a workspace directory descriptor using `O_NOFOLLOW` on every
   component from that anchor. Symlinked workspace/learn/tenant directories,
   nested directories, and leaf files are not accepted. Traversal (`..`), paths
   outside `learn`, non-Markdown paths, and non-regular files are rejected.
4. Read only the bounded header through an unbuffered stream, validate metadata
   against the already-authorized path, then read the body from the same open
   file descriptor. There is no whole-file-read-then-filter authorization path.
5. Scan the complete validated header and body with the shared `SecurityChecker`
   before returning any content. Authorization is necessary but does not exempt
   enterprise, brand, or owner-personal content from credential/PII screening.
6. Apply any non-security market filter to authorized, screened files.

`load_learn_file(path, context)` raises on denial/malformed data, unsafe content,
or filesystem errors. Unsafe content raises a generic `ValueError` without
including the detected value. `load_learn_files(context, *, level=None, market=None)`
and `get_market_context(market, context)` omit denied, unsafe, malformed, or
unreadable candidates. Missing/invalid context raises
`PermissionError` rather than returning an apparently successful result. Header
validation may consume up to the header limit when an opening fence is present
but the closing fence is missing; such a file is never returned as learning
context and the body-reading stage is never invoked.

## Explicit administrative audit

`manager.audit_security()` is a **privileged, cross-tenant offline audit**, not a
context-loading API. Restrict invocation and access to its findings at the
application boundary; it does not authenticate an administrator. It intentionally
reads valid files from all tenants to run security checks, returns only counts
and findings, and does not call the scoped context loader.

Unsafe and malformed files produce sanitized `INVALID_RESOURCE` findings and do
not abort the audit; detected content is never echoed. The runtime scanner and
offline validator share `SecurityChecker` policy. Directory symlinks are reported
and not traversed. Invalid/missing audit roots
and traversal I/O errors make the audit non-clean. `files` counts `.md` candidates
examined, including malformed files; directory-symlink findings do not inflate
that count. Findings do not include file bodies. The existing security validator
also flags personal files as unsuitable for Git; this is separate from whether
the authenticated owner can read them at runtime.

## Migration (intentional breaking changes)

- Move legacy `learn/<level>/...` files into the tenant-bound layouts above.
  Files left in the legacy layout are not loaded, and are audit violations.
- Provision and verify path scope and matching metadata through a trusted
  administrative process. Do not move files solely based on unverified metadata.
- Replace level-only `load_learn_files(...)` and
  `get_market_context(market, user_level=...)` calls with authenticated-context
  calls. Calling a loader without context now fails closed.
- Replace `can_access(user_level, resource_level)` with
  `can_access(context, ResourceScope(...))`; constructing a scope alone does not
  authorize a read. The manager remains the path/metadata enforcement boundary.
- `get_accessible_files(user_level, already_loaded_files)` was removed; filtering
  already-read content is not an isolation mechanism.
- `validate_all_files()` was removed. Use `audit_security()` explicitly from
  authorized administrative code, never as a workaround for missing context.

## What this does not isolate

This is application-level file-access policy, **not OS/process filesystem
isolation**. Code running with the process's permissions can bypass Python APIs,
construct identities, invoke the administrative audit, or read files directly.
Descriptor-relative no-follow opens protect against symlink redirection during
opening, but do not make malicious concurrent content writes safe, detect
cross-scope hardlinks, prevent mount changes, or provide a cryptographic binding
between filesystem data and identity.

Keep the workspace anchor and authorization metadata under trusted provisioning;
untrusted users must not be able to create hardlinks, modify scoped contents, or
rewrite directory trees. Use OS ownership/ACLs, separate processes/containers or
volumes, and restricted tool/file access when an agent or tenant needs a real
sandbox. The secure-open implementation requires POSIX descriptor-relative
`os.open`, `O_DIRECTORY` and `O_NOFOLLOW` support (tested on macOS); unsupported
platforms must not substitute permissive opens.

## Regression verification

```sh
python3 -m unittest discover -s tests -p test_access_control.py -v
```

The suite covers authorized hierarchy, cross-tenant/brand/department/team/personal
denials before file parsing, malformed identity and metadata, traversal, nested
paths, symlinks, market filtering, and explicit audit failure reporting. Body-read
spies verify rejected metadata never reaches the body-reading stage. Synthetic
provider keys and unlabelled emails in otherwise authorized enterprise, brand,
and owner-personal files are rejected by direct reads and omitted by list/market
loaders, while safe owner-personal content remains readable. Pattern screening
is defense in depth, not a guarantee of detecting every secret or instruction.
