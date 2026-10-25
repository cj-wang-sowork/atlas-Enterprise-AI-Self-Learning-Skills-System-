# ATLAS personal localhost trial

This is a **single-owner local demo**, not production software or a multi-tenant SaaS. Never expose this server with a public bind, reverse proxy, tunnel, shared machine endpoint, or personal OAuth-backed public service.

From the repository root:

```sh
ATLAS_CODEX_BIN=/absolute/path/to/codex python3 -m native_demo --port 8765
```

Open `http://127.0.0.1:8765`. Python 3.9+ and a previously authenticated Codex CLI are required; no runtime Python/JavaScript packages are installed. This app never reads or copies auth files. `ATLAS_CODEX_BIN` must be absolute; otherwise the app resolves `codex` from PATH. Default model is `gpt-6.1-sol`, with reasoning effort `low`; an owner can explicitly override `ATLAS_CODEX_MODEL`. Account/model availability must be tested, not assumed. Unknown-model and authentication/execution failures return errors, never substitute outputs.

The live acceptance used Codex CLI **0.164.0**. Older CLIs can reject the isolation
flags or the selected model. Check `codex --version` and `codex exec --help` first;
use a compatible CLI and a model verified for your own account. Version/model
numbers here describe the tested configuration, not perpetual platform support.

`ATLAS_DEMO_SCRATCH` selects an isolated temporary generation directory. Otherwise the configured TMPDIR or `~/.hermes/cache/scratch` is used. The task goes to Codex over stdin, not a shell argument. Only HOME and PATH are inherited. User config/rules/project instructions are disabled; tools are disabled and the sandbox is read-only. A zero exit code plus successful JSONL terminal turn is required; failed/incomplete/empty or unexpected-tool results are rejected. Original final assistant text is preserved.

## What is actually executed

- `marketing_team.plan_task` selects deterministic workstreams/method IDs. These are functional perspectives of one model, not connected agents or employees.
- When the plan requires new discovery, the existing bounded GET-only GitHub client searches authored generic category keywords; raw task and brand context never become search queries. Public excerpts remain untrusted data. License-at-commit and host review are incomplete, so external sources are not approved/activated; generation uses bundled methods. Discovery is method research, not proof of market facts or marketing results.
- A POST invokes the real local Codex CLI. Input is sent to its model provider; do not enter credentials, sensitive personal data or confidential files. The fictional coffee button fills **input only**, never a result.
- Output is editable Markdown with copy/download of the current text. Human review is still required; nothing is posted, scheduled, purchased or approved.

## Boundaries

Loopback binding only; exact localhost Host/Origin checks; a per-process CSRF token; JSON-only POST; 16 KiB request limit; one active generation and at most 12 HTTP handler connections; 10-second request-read timeout; 150-second total discovery/generation budget (minus elapsed discovery time before invoking Codex). Optional discovery also has its own existing 45-second bounded budget. Response text is limited to 100,000 characters. On POSIX (macOS/Linux), the real CLI transport streams stdout and stderr concurrently with one shared 1,000,000-byte capture budget, enforced during reads rather than after buffering. Timeout or excess output terminates the isolated process group (including ordinary launcher descendants): SIGTERM, up to 0.25 seconds for launcher cleanup/reaping, then SIGKILL for survivors and a wait to reap the direct launcher. Non-child descendants are reaped by their parent or the OS; descendants that deliberately escape the process group are outside this boundary. Unsupported platforms fail closed with `UNSUPPORTED_PLATFORM`. Injected test transports retain their existing call contract; they are not the real subprocess boundary. Provider protocol capture is held only in bounded memory; no task/context/output history is written by this app. Temporary generation directories are deleted after process cleanup. The Codex/provider/account may have their own policies; this is not an enforced tenant privacy guarantee.

Only `/`, `/app.css`, `/app.js`, `/health`, and POST `/api/run` are served. No uploads, filesystem browser, automatic memory, publishing or account-grant flow exists. Request bodies, provider stderr and task contents are not logged. Errors returned to the browser are fixed codes.

## Offline verification

```sh
python3 -m unittest discover -s tests -p test_native_demo.py -v
node --check native_demo/app.js
```

Tests inject synthetic model transports and discovery responses, explicitly not real marketing results. They also run bounded offline executable fixtures for process-group cleanup, stdout/stderr streaming limits, UTF-8 stdin/JSONL handling, and real localhost HTTP handlers. No Codex/model call is needed for these tests. A separate owner-account live model/browser test is needed for end-to-end generation and is not claimed by those unit tests.
