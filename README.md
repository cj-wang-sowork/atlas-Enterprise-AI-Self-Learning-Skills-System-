# ATLAS Enterprise AI Self-Learning Skills System

ATLAS is a portable agent workspace, reusable prompt pack, and optional Python reference implementation for reviewed learning from repeated work. It is **not a production-ready multi-tenant service**: copying instructions does not enforce privacy, authenticate users, or connect a runtime to the Python backend. Start with sanitized examples and verify the integration you actually use.

The same repository can be installed for:

| Runtime | Support model |
| --- | --- |
| OpenClaw | Installs the full workspace into `~/.openclaw/workspace` |
| Claude Code | Adds a project `CLAUDE.md` launcher, workspace context, and a skill pack |
| Codex CLI | Uses Codex's `AGENTS.md` instruction discovery |
| Qwen Code CLI | Installs a `SKILL.md` pack under `~/.qwen/skills` |
| Hermes Agent | Installs a `SKILL.md` pack under `$HERMES_HOME/skills` (default `~/.hermes/skills`) |
| ChatGPT | **Manual Starter Kit** for Project instructions and sanitized context; no local/backend execution |

## Try the first job before installing

For the shortest SoWork demonstration, copy the single card in
[TRY_SOWORK_NOW.md](starter/chatgpt/TRY_SOWORK_NOW.md). It supplies three checked
public-source snapshots and asks for actual first work plus QA, not five rounds
of role/KPI setup. This is chat-local prompt context, **not** a backend connection,
automatic learning, guaranteed cross-chat retrieval or proven product uplift.
The [generic first-win card](starter/chatgpt/FIRST_WIN.md) works for other tasks;
Project setup and manual rule retention come after evaluating the first output.
See the [real SoWork A/B prompt-proxy report](studies/sowork-acquisition/REPORT.md)
for original outputs and the 20-company comparison sheet. It is not a ChatGPT UI
test or proof of better sales outcomes; C remains blocked pending real reviews.

## What You Get

- A clear agent boot sequence in `AGENTS.md`
- Persona, memory, tool, identity, and heartbeat templates
- Three reusable skills: brand positioning, web research, and content writing
- A five-layer learning methodology for enterprise, brand, department, team, and personal context
- Python modules for market routing, access control, security checks, pattern learning, and cross-market intelligence
- A POSIX shell/Python 3 installer for OpenClaw, Claude Code, Codex CLI, Qwen Code CLI, Hermes, or all five
- A separate [ChatGPT Starter Kit](docs/CHATGPT_STARTER.md) for non-engineers; no terminal required

## Verified implementation and boundaries

The earlier core-hardening regression evidence is in [VERIFICATION.md](docs/VERIFICATION.md), including
collected tests, the pinned detector-fixture comparison, and explicit unverified
production, live-runtime, usability, and business-benefit criteria. See
[ACCESS_CONTROL.md](docs/ACCESS_CONTROL.md) for the intentional scoped-API migration and
[LEARNING_LIFECYCLE.md](docs/LEARNING_LIFECYCLE.md) for reviewed versioned reuse.

## Authenticated E2E and measured evaluation milestone

Use a **full source checkout** for these optional integration/research tools; installing
workspace prompt files does not wire them into a live agent runtime.

- [Trusted identity example](docs/IDENTITY_INTEGRATION.md): pinned RS256 verification,
  server-owned grants, role checks and genuine subprocess restart/cross-user reuse.
  The issuer, users and human approvals in acceptance fixtures are synthetic; no
  production external IdP or browser OAuth flow has been connected.
- [Controlled paired pilot](studies/paired-pilot/REPORT.md): six actual model task
  calls on three explicitly fictional marketing briefs, same model/data per pair.
  It does **not** establish business-quality improvement; the apparent lexical gate
  advantage contains a false positive, and the reference arm was slower in this pilot.
- [Non-engineer ChatGPT study](docs/CHATGPT_USABILITY_STUDY.md): participant/observer
  protocol and durable recorder. No real participant has completed this study;
  human success/time metrics remain unmeasured, not replaced by agent QA.

See [E2E acceptance](docs/E2E_ACCEPTANCE.md) for executable evidence and outstanding
human/customer/live-IdP gates. The core library remains standard-library-only;
optional signature verification installs `integrations/requirements-oidc.txt`.

## Quick Install

```bash
git clone https://github.com/cj-wang-sowork/atlas-Enterprise-AI-Self-Learning-Skills-System-.git
cd atlas-Enterprise-AI-Self-Learning-Skills-System-
```

Install for one runtime:

```bash
./scripts/install-workspace.sh --target openclaw
./scripts/install-workspace.sh --target claude --dest ~/workspace/your-project
./scripts/install-workspace.sh --target codex --dest ~/workspace/your-project
./scripts/install-workspace.sh --target qwen
./scripts/install-workspace.sh --target hermes
```

ChatGPT users: download the repository ZIP, open `starter/chatgpt/README.md`, and follow the manual Project setup. The [walkthrough](docs/CHATGPT_STARTER.md) targets a first task in about 10 minutes, but this is not a measured or guaranteed result. Live ChatGPT UI setup has not been verified.

Install for all five local agent runtimes (not ChatGPT):

```bash
./scripts/install-workspace.sh --target all --dest ~/workspace/your-project
```

For `--target all`, `--dest` is the shared Claude/Codex project root, with separate `CLAUDE.md` and `AGENTS.md` launchers. OpenClaw, Qwen, and Hermes use their default locations (Hermes honors `HERMES_HOME`). This can modify several existing workspaces; read [backup and replacement rules](docs/INSTALLATION.md#backups-and-safety) first. ChatGPT export is separate: `--target chatgpt --dest /path/to/manual-kit`.

## Runtime Details

### OpenClaw

```bash
./scripts/install-workspace.sh --target openclaw
```

Default destination: `~/.openclaw/workspace`

OpenClaw loads the workspace files directly. After installation, customize:

- `SOUL.md` for persona and tone
- `TOOLS.md` for local environment notes
- `MEMORY.md` for curated long-term context
- `skills/` for reusable workflows

### Claude Code

```bash
./scripts/install-workspace.sh --target claude --dest ~/workspace/your-project
```

The installer writes:

- `CLAUDE.md` in the project root
- `.atlas-workspace/` with the full workspace bundle
- `.claude/skills/atlas-enterprise-ai-self-learning/SKILL.md`

The generated `CLAUDE.md` points to the workspace context and skill prompts. Existing launchers are backed up by default, not merged; review and merge your project rules before use.

### Codex CLI

```bash
./scripts/install-workspace.sh --target codex --dest ~/workspace/your-project
```

Codex reads `AGENTS.md` files before it works. The installer writes a project `AGENTS.md` launcher and `.atlas-workspace/` bundle so Codex can discover the same workflow and skill instructions from the repository root.

### Qwen Code CLI

```bash
./scripts/install-workspace.sh --target qwen
```

Default destination: `~/.qwen/skills/atlas-enterprise-ai-self-learning`

Qwen Code discovers skills from `~/.qwen/skills/` and `.qwen/skills/`. This installer creates a Qwen-compatible skill directory with `SKILL.md`, references, templates, and bundled prompt skills.

Use a custom Qwen skill location if needed:

```bash
./scripts/install-workspace.sh --target qwen --dest ~/.qwen/skills/my-atlas-skill
```

### Hermes Agent

```bash
./scripts/install-workspace.sh --target hermes
```

Default: `~/.hermes/skills/openclaw-imports/openclaw-workspace-sowork`.
With `HERMES_HOME` set, the same relative path is placed under that home.
For an explicit profile, prefer `--dest /absolute/profile/home/skills/openclaw-imports/openclaw-workspace-sowork` rather than guessing the active CLI profile.
The pack has `SKILL.md`, references, `assets/skills/`, and a complete
`templates/workspace/` including Python modules. Use `hermes skills list` to
inspect discovery, then load the name shown by your installation. No Hermes
configuration, credentials, gateway, or automatic learning hook is created.

## How To Use

After installation, ask your agent for one of the bundled workflows:

```text
Run brand positioning for our product.
Research competitors in the Japan market.
Write a LinkedIn post for this launch.
Analyze this repository and update the learning notes.
```

For Qwen Code, inspect the skill list in your installed version and select the ATLAS skill. CLI flags vary; check that version’s help instead of assuming an invocation flag. Installation tests verify files/imports, not live model behavior.

## Methodology

ATLAS separates reusable learning by audience and risk:

| Layer | Purpose | Typical content | Sharing rule |
| --- | --- | --- | --- |
| Enterprise | Organization-wide operating knowledge | Cross-market patterns, standards, policies | Shared broadly |
| Brand | Brand identity and messaging | Voice, positioning, approved claims | Shared with brand owners |
| Department | Function-specific playbooks | Marketing, sales, product, engineering workflows | Internal to department |
| Team | Local execution learning | Experiments, retrospectives, tactical decisions | Team-only |
| Personal | Individual preferences and notes | Private working style, drafts, local context | Never committed |

These are intended sharing rules, not a security guarantee. An instruction file cannot stop an agent or another OS user from reading accessible files. A production integration needs trusted identity, authorization on each protected operation, controlled storage, audit/revocation, and reviewed learning promotion. See [access control](docs/ACCESS_CONTROL.md) and [learning lifecycle](docs/LEARNING_LIFECYCLE.md).

Read the full methodology in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Architecture

```text
User request
  -> Runtime context instructions (OpenClaw, Claude, Codex, Qwen, Hermes)
  -> Workspace boot sequence (AGENTS, SOUL, TOOLS, MEMORY)
  -> Skill workflow selection (brand, research, content, custom)
  -> Five-layer learning policy
  -> Optional Python learning modules
  -> Output, audit notes, and reusable learning updates
```

Core Python modules:

| Module | Role |
| --- | --- |
| `learn_system.py` | Five-layer learning files and access validation |
| `market_router.py` | Market registration, context, routing, and stats |
| `security_checker.py` | Credential, PII, path, and access marker checks |
| `hermes_adapter.py` | Observation, verified outcomes, reviewed lesson promotion, and reuse comparison |
| `skill_registry.py` | Scoped revision history, human approvals, persistence, revocation, and import distrust |
| `market_intelligence.py` | Cross-market insights, anomalies, and health reports |

The installer includes **all root `*.py` modules**, including `skill_registry.py` when present. Full workspace bundles contain them at the workspace root; skill packs contain them in `templates/workspace/`. Run code explicitly from that directory or integrate it yourself. Installing prompts does not invoke the backend or automatically observe/review/promote lessons. ChatGPT uses manual text context only.

## Verify Installation

Run the sandbox installation suite from the repository root:

```bash
python3 -m unittest discover -s tests -p test_installer.py -v
```

Tests isolate `HOME`, `HERMES_HOME`, and destinations; no real profiles are installed. They cover every target, module imports, repeated installs/backups, force replacement, malformed arguments, overlaps, symlinks, and `all` preflight. See [verification scope](docs/VERIFICATION.md). These checks are not runtime/model/UI end-to-end tests.

Check the known Python modules compile (installed import checks are in the suite above):

```bash
python3 -m py_compile learn_system.py market_router.py security_checker.py hermes_adapter.py market_intelligence.py
```

## Documentation

| Document | Purpose |
| --- | --- |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Detailed installation and layout guide |
| [docs/CHATGPT_STARTER.md](docs/CHATGPT_STARTER.md) | Manual non-engineer Project setup and first task |
| [docs/ACCESS_CONTROL.md](docs/ACCESS_CONTROL.md) | Backend authorization boundaries and integration obligations |
| [docs/LEARNING_LIFECYCLE.md](docs/LEARNING_LIFECYCLE.md) | Candidate/review/promotion lifecycle and limits |
| [docs/VERIFICATION.md](docs/VERIFICATION.md) | Executed checks versus unverified integrations |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Architecture, learning model, and rationale |
| [docs/LEARN.md](docs/LEARN.md) | Five-layer learning reference |
| [SECURITY.md](SECURITY.md) | Security policy and sensitive-data rules |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution workflow |

## Security Rules

- Never commit API keys, credentials, personal memory, or raw conversation logs.
- Keep `MEMORY.md` for direct owner sessions only.
- Keep personal learning outside shared git history.
- Review `TOOLS.md` before sharing a workspace because it may describe local hosts or operational details.

## License

MIT. See [LICENSE](LICENSE).
