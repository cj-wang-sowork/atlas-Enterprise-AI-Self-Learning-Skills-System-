# Installation Guide

This installs **context files and optional code**, not OpenClaw, Claude Code, Codex CLI, Qwen Code CLI, or Hermes themselves. Install/authenticate those runtimes separately. ChatGPT has a separate manual text-only Starter Kit; no shell is required for that route.

ATLAS is a reference implementation, not a production-ready tenant-isolation service. Prompt instructions do not enforce backend permissions or automatically run learning. Read [ACCESS_CONTROL.md](ACCESS_CONTROL.md), [LEARNING_LIFECYCLE.md](LEARNING_LIFECYCLE.md), and [VERIFICATION.md](VERIFICATION.md) before integrating protected data.

## Requirements

- macOS, Linux, or WSL
- `sh`, `cp`, `mv`, and `mkdir`
- Python 3.9+ for the optional modules and tests; the installer also uses Python for path/source preflight and backup names
- Git, if you clone the repository

No Python packages are required for the workspace or installer.

## Clone

```bash
git clone https://github.com/cj-wang-sowork/atlas-Enterprise-AI-Self-Learning-Skills-System-.git
cd atlas-Enterprise-AI-Self-Learning-Skills-System-
```

## Installer Syntax

```bash
./scripts/install-workspace.sh --target TARGET [--dest PATH] [--force]
```

Targets:

| Target | Destination behavior |
| --- | --- |
| `openclaw` | Installs the workspace to `~/.openclaw/workspace` unless `--dest` is provided |
| `claude` | Installs into a project root passed with `--dest` |
| `codex` | Installs into a project root passed with `--dest` |
| `qwen` | Installs a skill pack to `~/.qwen/skills/atlas-enterprise-ai-self-learning` unless `--dest` is provided |
| `hermes` | Skill pack under `$HERMES_HOME/skills/openclaw-imports/openclaw-workspace-sowork`; `HERMES_HOME` defaults to `~/.hermes`; custom `--dest` overrides it |
| `all` | OpenClaw + Claude + Codex + Qwen + Hermes; `--dest` is only the shared Claude/Codex project root; other targets use defaults |
| `chatgpt` | Exports four manual Starter Kit text files to a required `--dest`; does not configure ChatGPT |

## Backups and safety

- Every existing managed file/directory, including a project launcher, is moved
  to a sibling `NAME.bak.TIMESTAMP-RANDOM` by default. Backup names include
  microseconds and a random suffix; repeated installs do not reuse old backups.
- Launchers are **replaced, not merged**. Review the backup and merge important
  project instructions before starting your agent. A backup is not an active rule.
- Entire managed directories (for example `docs/`, `skills/`, `.atlas-workspace/`
  contents) may be replaced. Keep work in separate directories or retain backups.
- `--force` deletes existing managed items without making new backups. It does
  not delete old sibling backups or unrelated project files. Use it intentionally.
- Source repository destinations, their descendants, and their ancestors are
  rejected. `all` also rejects overlapping destinations and checks **all** target
  roots/managed paths before the first copy, avoiding partial installs from
  detectable path conflicts or missing required source payloads.
- Symlinks (including broken ones) and special files in copied source trees or
  managed destination trees are rejected. Destination parent symlinks are also
  rejected, even with `--force`; use physical paths rather than aliases.
- Preflight is not a transaction/rollback system. Disk-full, permission changes,
  or I/O errors during copying can leave a partial install. Inspect printed
  backup paths before retrying. Do not run concurrent installers or let another
  process mutate the source/destinations while installing.
- Review the source before copying: workspace bundles include `MEMORY.md`,
  `memory/`, `outputs/`, and `TOOLS.md`. Use a clean, sanitized checkout, not a
  personalized workspace with client data. Backups can also contain private data.
- Repeated options, empty values, unknown flags, and missing destinations fail
  before installation. `--help` describes the supported targets.

## OpenClaw

```bash
./scripts/install-workspace.sh --target openclaw
```

Default layout:

```text
~/.openclaw/workspace/
  AGENTS.md
  SOUL.md
  TOOLS.md
  MEMORY.md
  SKILL.md
  skills/
  docs/
  examples/
  scripts/
  starter/chatgpt/
  learn_system.py, security_checker.py, hermes_adapter.py, ...
```

OpenClaw should load `AGENTS.md` on each main session. Customize `SOUL.md`, `TOOLS.md`, and `MEMORY.md` after installation.

## Claude Code

```bash
./scripts/install-workspace.sh --target claude --dest ~/workspace/your-project
```

The installer writes:

```text
your-project/
  CLAUDE.md
  .atlas-workspace/
    AGENTS.md
    SOUL.md
    TOOLS.md
    MEMORY.md
    skills/
    docs/
  .claude/
    skills/
      atlas-enterprise-ai-self-learning/
        SKILL.md
        references/
        templates/
        assets/
```

Claude gets `CLAUDE.md`; Codex gets `AGENTS.md`. Existing launchers are backed up by default (no implicit merge). The Claude-only target does not modify a root `AGENTS.md`. See the [Claude instruction-file documentation](https://code.claude.com/docs/en/memory).

## Codex CLI

```bash
./scripts/install-workspace.sh --target codex --dest ~/workspace/your-project
```

Codex CLI uses `AGENTS.md` in its project instruction chain. See [OpenAI’s instruction discovery guide](https://developers.openai.com/codex/guides/agents-md/). The installer writes:

```text
your-project/
  AGENTS.md
  .atlas-workspace/
    AGENTS.md
    SOUL.md
    TOOLS.md
    MEMORY.md
    skills/
    docs/
```

Start Codex from the project root:

```bash
cd ~/workspace/your-project
codex
```

Verify discovery by asking Codex to summarize the active project instructions.

## Qwen Code CLI

```bash
./scripts/install-workspace.sh --target qwen
```

Default layout:

```text
~/.qwen/skills/
  atlas-enterprise-ai-self-learning/
    SKILL.md
    references/
    templates/
    assets/
```

Use a project-local Qwen skill by choosing a project path:

```bash
./scripts/install-workspace.sh --target qwen --dest ~/workspace/your-project/.qwen/skills/atlas-enterprise-ai-self-learning
```

Inspect the skill list in your installed Qwen Code version (consult its help); do not assume flags from a different release. The expected skill name in the frontmatter is `atlas-enterprise-ai-self-learning`. See [Qwen’s skill documentation](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/).

## Hermes Agent

```bash
./scripts/install-workspace.sh --target hermes
# Or select one explicit profile destination:
./scripts/install-workspace.sh --target hermes --dest /absolute/profile/home/skills/openclaw-imports/openclaw-workspace-sowork
```

Default home is `~/.hermes`, or the `HERMES_HOME` environment variable when set.
The installer does not discover the sticky active CLI profile. For a named
profile, select `--dest` explicitly to avoid changing a different profile.

```text
skills/openclaw-imports/openclaw-workspace-sowork/
  SKILL.md
  references/
  assets/skills/
  templates/workspace/
    AGENTS.md
    skills/
    docs/
    *.py
```

Use `hermes skills list` to inspect discovery and load the name shown by your
installed version. The directory preserves the existing import name; its
`SKILL.md` frontmatter name is `atlas-enterprise-ai-self-learning`, and name
resolution can vary by runtime. Restart/reload the runtime if needed. Consult
[Hermes skills documentation](https://hermes-agent.nousresearch.com/docs/guides/work-with-skills).
The installer does not create Hermes credentials, provider configuration,
a gateway, MCP integration, or automatic learning hooks.

## ChatGPT — manual Project Starter Kit

No shell is needed: download the ZIP and open
[`starter/chatgpt/README.md`](../starter/chatgpt/README.md). Follow
[CHATGPT_STARTER.md](CHATGPT_STARTER.md) for the first task and human review.
Optionally export just the four kit files from a terminal:

```bash
./scripts/install-workspace.sh --target chatgpt --dest ~/Documents/atlas-chatgpt-kit
```

This copies text only. You manually paste instructions, add sanitized context,
review outcomes, and maintain approved lessons. It neither runs ATLAS in ChatGPT
nor connects ChatGPT to backend access control or automatic learning.
Live ChatGPT UI setup and ten-minute usability have not been verified.

## Install Everything

```bash
./scripts/install-workspace.sh --target all --dest ~/workspace/your-project
```

This performs:

1. OpenClaw install to `~/.openclaw/workspace`
2. Claude Code project install to `~/workspace/your-project`
3. Codex project install to `~/workspace/your-project`
4. Qwen global skill install to `~/.qwen/skills/atlas-enterprise-ai-self-learning`
5. Hermes skill install under `$HERMES_HOME/skills/openclaw-imports/openclaw-workspace-sowork` (default home `~/.hermes`)

Claude Code and Codex share `.atlas-workspace/`, but receive separate `CLAUDE.md` and `AGENTS.md` launchers. `all` does **not** configure ChatGPT, create a standalone kit destination, or launch any host runtime. The sanitized kit remains included as reference material inside full workspace bundles. It writes to user-level destinations as well as the project root; use separate custom-target installs if that is not what you want.

## Optional Python Module Check

All root `*.py` files are copied, including `skill_registry.py` when present. Workspace installs place them at the workspace root; Qwen/Hermes/Claude skill packs place a full bundle at `templates/workspace/`. Nothing imports or starts the backend automatically.

The Python files are optional; from the repository or installed bundle root you can check the known modules compile:

```bash
python3 -m py_compile learn_system.py market_router.py security_checker.py hermes_adapter.py market_intelligence.py
```

Check imports from the installed bundle root (or a skill pack's
`templates/workspace/`), not from the original checkout:

```bash
python3 -c "import learn_system, market_router, security_checker, hermes_adapter, market_intelligence"
```

This is an import smoke test, not proof of authorization, lifecycle behavior,
or runtime wiring. Integration must use the actual module APIs and trusted
identity; see the companion access-control and lifecycle guides.

## Sandbox verification

From the repository root:

```bash
python3 -m unittest discover -s tests -p test_installer.py -v
sh -n scripts/install-workspace.sh
```

The suite runs the real shell installer against temporary source checkouts,
`HOME`, `HERMES_HOME`, and destinations, including default paths and `all`.
It verifies installed module imports from the destination, not the source repo.
No real runtime account/profile, model provider, or ChatGPT UI is exercised.
See [VERIFICATION.md](VERIFICATION.md) for integration evidence and limits.

## Troubleshooting

### The installer says the destination overlaps the source repository

Choose a destination outside the cloned repository and not an ancestor of it. For `all`, the project must also not overlap any runtime default destination. This prevents recursive copies and inter-target overwrites.

### Existing project rules changed

The original launcher was backed up by default, not merged. Restore/merge the printed backup into `CLAUDE.md` (Claude) or `AGENTS.md` (Codex) before using the project. `--force` intentionally skips new backups.

### Qwen cannot find the skill

Check that the skill directory contains `SKILL.md` and is inside one of Qwen's skill locations:

- `~/.qwen/skills/`
- `.qwen/skills/`

Restart or reload the session according to your installed runtime’s documentation if needed.

### Codex does not load the instructions

Start Codex from the project root or pass the correct working directory. Confirm the root contains `AGENTS.md`.
