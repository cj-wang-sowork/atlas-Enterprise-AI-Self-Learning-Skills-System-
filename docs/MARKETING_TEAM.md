# Adaptive Marketing Team

This is one canonical marketing director and resource set under `team_core/`,
exported for three different host workflows. It is one model simulating coordinated
workstreams, not independently deployed agents, connected employees or a background
service. Workstream selection is adaptive; no fixed five-role pipeline is required.
The legacy Agency kit is unchanged and is not the new director's workflow authority.

## What it does

For each new need, the director checks actual capabilities, proactively performs a
bounded public GitHub method search with generic category keywords, reviews a small
fit-based selection, then applies safe method guidance to the requested deliverable.
It checks README/method text, current commit, exact license and environment. Stars
are only a popularity signal, not approval. Retrieved text is untrusted; nothing
from discovered repositories is automatically installed or executed.

The Python helper only gathers bounded source evidence. Its `REVIEW_REQUIRED`
status explicitly leaves commit-pinned license and environment checks for the
host assistant; repository-search SPDX metadata is not a verified license file.
A completed search is not method approval. The host should finish safe read-only
checks itself when tools permit, then use eligible guidance in the deliverable;
otherwise it falls back to bundled methods and reports the limitation. It must
not ask users to approve routine public reading or imply that source review
approves installers, execution or external account writes.

Client names, private briefs and unpublished task specifics must never enter public
search. The optional local helper accepts generic category inputs only:

```text
python3 -m marketing_team plan --task "content calendar"
python3 -m marketing_team discover --task "content calendar" --max-results 3
```

Run those commands from the repository root or the extracted skill root, not the
outer plugin folder. `plan` is a local planning aid, not task execution; `discover`
is read-only source research, not permission to run repository code. Python and
network availability depend on the host. Without Python, use actual built-in web
tools and the same review process. If live research is disabled, blocked or fails,
report `LIVE_SEARCH_UNAVAILABLE` and use the six bundled licensed methods without
pretending discovery occurred. A historical bundled snapshot is not live verification.

The core asks for useful work before optional onboarding: complete copy or supported
findings, requested counts, labelled assumptions, citations, selected methods and
why/where applied, QA, limitations and `DRAFT — unpublished` status. Missing analytics
means measurement design and QA, not fake performance results. External account
writes, posting, messaging and ad spend are not authorized or performed by this kit.

## Build and check (stdlib only)

Requires Python 3.9+. No dependency installation, network, account access or live
platform session is needed to build. From the repository root:

```text
python3 scripts/build-marketing-team.py --check
python3 scripts/build-marketing-team.py --target claude --dest /absolute/physical/scratch/team-claude.zip
python3 scripts/build-marketing-team.py --target chatgpt-plugin --dest /absolute/physical/scratch/team-plugin.zip
python3 scripts/build-marketing-team.py --target chatgpt-project --dest /absolute/physical/scratch/team-project.zip
python3 -m unittest discover -s tests -p test_marketing_team_bundle.py -v
```

Choose your actual existing scratch directory; these are illustrative paths, not
commands to create that directory. `--check` (also the default with no options) is
read-only. It validates the fixed required source allowlist, JSON syntax, package
syntax and local import closure, then prints the source manifest. Missing package
modules fail closed, including in the text fallback, so all three represent the same
complete canonical release. No fake helper package is generated.

`--target` and `--dest` must be paired; do not combine them with `--check`.
The destination must be an absolute `.zip` path outside the repository, with an
already existing parent. Existing destinations, symlinks including ancestor aliases,
traversal components and non-ZIP targets are refused. On macOS use the physical path
(e.g. resolve a scratch alias first). No `--force`: choose a separate intentional
filename. All required sources are checked before any destination writes. An archive
is built in a same-directory temporary file, flushed, then atomically hard-linked
into a previously absent destination. Failure never overwrites an existing output;
temporary build files are cleaned. Filesystems without hard-link support fail closed.
This validation is not a guarantee against a hostile concurrent filesystem owner.

Only the fixed canonical resource/package allowlist is collected. Other repository
files, client data, logs, local secrets, caches, `.git`, demos and optional application
code are not globbed into archives. Builds never import/execute the packaged helper.
Archive names are fixed, sorted and relative; ZIP entries use a fixed 1980 timestamp,
Unix regular-file permissions and stored bytes for deterministic output without
compression-library variation. Identical source bytes produce identical ZIP hashes.

Each package contains `SOURCE_MANIFEST.json` with per-source byte sizes/SHA-256 and
an aggregate digest derived from the sorted records. The Project manifest also
inventories package-code source for release equivalence, but that text-only archive
does not ship Python code. The manifest is an integrity inventory, not a signature,
a security certification or proof of model behavior.

## Export layouts and manual setup

### Claude skill

```text
atlas-marketing-team/
  SKILL.md
  resources/  templates/  licenses/
  catalog.json  SETUP.md  PROVENANCE.md  SOURCE_MANIFEST.json
  marketing_team/  (complete local Python helper package)
```

Upload the single-folder ZIP through the custom-skill UI described in
`team_core/SETUP.md`. Code execution and file creation must be enabled where required;
organization policy can prevent uploading or execution. The skill folder name and
frontmatter name match. This is a portable package, not a native account installer.

### ChatGPT skills-only plugin

```text
plugin.json
skills/atlas-marketing-team/
  SKILL.md
  resources/  templates/  licenses/
  catalog.json  SETUP.md  PROVENANCE.md  SOURCE_MANIFEST.json
  marketing_team/
```

The root manifest uses the portable Agent Plugins 1.0.0 schema. Skills are discovered
under root `skills/`; the root manifest deliberately has no compatibility-only
`skills` or `apps` field. No MCP server, MCP configuration, account connector, hooks,
credentials, custom actions or lifecycle installer is present or implied. Eligible
ChatGPT workspace/plugin upload permissions are required; availability varies by
surface. See the current official references and conditional setup in `team_core/SETUP.md`.
Dragging the ZIP into an ordinary chat is not a permanent installation.

### ChatGPT Project fallback

```text
PROJECT_INSTRUCTIONS.md
PLAYBOOK.md
CLIENT_CONTEXT.md
SETUP.md
PROVENANCE.md
SOURCE_MANIFEST.json
licenses/
```

Unzip locally, paste `PROJECT_INSTRUCTIONS.md` into Project instructions, upload the
single compiled `PLAYBOOK.md`, and fill/upload a separate authorized client context.
The playbook retains the canonical director, all resources, catalog and delivery
reference with source-path headings; it does not recreate a fixed-role kit. Keep one
active playbook version. This is a manual plaintext workflow, not native plugin
installation or executable-tool provisioning. No native plugin is fabricated.

## Methods, rights and client context

Six complete existing adapted methods are retained: brand positioning, product
positioning, social operating system, content pillars, performance review and
LinkedIn writing. Chinese method blocks are preserved verbatim for fidelity;
new operator documentation is English, and outputs support the user's language,
including Traditional Chinese. Only method blocks are extracted from the old
`starter/chatgpt/agency/SKILL_PACK.md`; fictional client content, demonstrations,
legacy role matrices and forced sequencing are excluded. The adaptive director
chooses which methods and stages are actually useful.

The upstream MIT notice and historical provenance inventory are retained byte for
byte under `team_core/licenses/`; see `team_core/PROVENANCE.md` for the source commit
and extraction boundary. The 52-file provenance inventory does not mean those
52 source files are all included. Historical pins are not current-source assertions.
`catalog.json` entries for `coreyhaines31/marketingskills` and
`msitarzewski/agency-agents` are discovery hints only; verify current license,
commit, popularity, environment and method safety live before selection.

A code repository's MIT license does not grant blanket commercial rights to
third-party assets, case studies, photos, logos or copyrighted folders. No complete
optional application is copied: `news-sowork` and `election-pwa` are adapter ideas,
not native connected tools; authentication and security are unresolved.

Keep filled client context separate from reusable source. Versions, feedback reuse,
source upgrades and exact human approvals are manual. No automatic self-learning,
model update, shared memory, cross-chat synchronization, multi-tenant isolation or
privacy guarantee is supplied. Only actual visible authorized inputs can be used.

## Verification boundary

Offline contract tests cover canonical instructions and resources, six methods,
demo exclusion, notices, byte-equivalent native resources, compiled Project content,
source manifests, deterministic archives, import closure and unsafe-path refusal.
Extracted local CLI smoke tests establish package importability without native
account access. They do not establish business effectiveness or model adherence.

**PENDING:** native Claude and ChatGPT account upload, user permissions, clean-session
activation, actual model discovery/application, cross-conversation manual reuse and
real-human acceptance. Follow `SETUP.md` after installation and retain actual outputs,
source/tool evidence and deviations before claiming those checks passed.
