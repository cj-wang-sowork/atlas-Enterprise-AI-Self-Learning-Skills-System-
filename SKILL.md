---
name: atlas-enterprise-ai-self-learning
description: >
  Portable enterprise agent workspace and skill pack for OpenClaw, Claude Code,
  Codex CLI, Qwen Code CLI, and Hermes Agent. Provides reusable brand, research, and content
  workflows plus a five-layer methodology for reviewed learning across
  enterprise, brand, department, team, and personal context.
version: "1.3.0"
author: cj-wang-sowork
license: MIT
tags:
  - openclaw
  - claude-code
  - codex-cli
  - qwen-code
  - hermes-agent
  - agent-workspace
  - skills
  - self-learning
  - enterprise-ai
  - knowledge-management
  - security
requirements:
  - OpenClaw, Claude Code, Codex CLI, Qwen Code CLI, or Hermes Agent
  - macOS, Linux, or WSL
  - Python 3 for installer checks/backups and optional learning modules
---

# ATLAS Enterprise AI Self-Learning

Use this skill when a user wants an agent workspace that can be installed across OpenClaw, Claude Code, Codex CLI, Qwen Code CLI, and Hermes Agent, or when they need repeatable brand, research, content, and learning workflows.

## What This Skill Provides

1. A portable workspace bundle with `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md`, and operational templates.
2. Three bundled workflow prompts:
   - `skills/brand-positioning.md`
   - `skills/web-research.md`
   - `skills/content-writer.md`
3. A five-layer learning methodology:
   - Enterprise
   - Brand
   - Department
   - Team
   - Personal
4. Optional Python modules for learning, market routing, security checks, pattern adaptation, and market intelligence.

## When To Activate

Activate this skill when the user asks to:

- Set up or migrate an agent workspace
- Install the workspace for OpenClaw, Claude Code, Codex CLI, Qwen Code CLI, or Hermes Agent
- Build reusable team skills or prompts
- Create brand positioning, market research, or content outputs
- Explain or apply the ATLAS five-layer learning methodology
- Audit whether agent memory or learning files are safe to share

## Workflow

1. Identify the target runtime:
   - OpenClaw uses `~/.openclaw/workspace`.
   - Claude Code uses a project `CLAUDE.md` launcher and `.claude/skills/`.
   - Codex CLI uses project `AGENTS.md` instruction discovery.
   - Qwen Code CLI uses `~/.qwen/skills/` or `.qwen/skills/` skill directories.
   - Hermes uses `$HERMES_HOME/skills/` (default `~/.hermes/skills/`).
   - ChatGPT is a separate manual Project Starter Kit, not a shell/backend runtime.
2. Read the local workspace files before changing behavior:
   - `AGENTS.md`
   - `SOUL.md`
   - `TOOLS.md`
   - `MEMORY.md` only for direct owner sessions
3. Select the most relevant bundled skill from `skills/`.
4. Apply the five-layer learning rules:
   - Share enterprise, brand, department, and team knowledge only at the intended audience level.
   - Keep personal notes private and out of git.
   - Never expose credentials, tokens, or private memory in outputs.
5. Produce clear output and, when appropriate, write durable artifacts into `outputs/`.

## Installation Commands

```bash
./scripts/install-workspace.sh --target openclaw
./scripts/install-workspace.sh --target claude --dest ~/workspace/your-project
./scripts/install-workspace.sh --target codex --dest ~/workspace/your-project
./scripts/install-workspace.sh --target qwen
./scripts/install-workspace.sh --target hermes
./scripts/install-workspace.sh --target chatgpt --dest ~/Documents/atlas-chatgpt-kit
./scripts/install-workspace.sh --target all --dest ~/workspace/your-project
```

## Expected Behavior

- Prefer simple, explicit instructions over hidden automation.
- Keep all user-facing documentation in English unless the user asks otherwise.
- Explain managed-file replacement before installation. Existing launchers are backed up, not merged; use `--force` only with explicit approval.
- Treat `MEMORY.md`, `memory/`, and personal learning files as sensitive.
- Summarize architectural decisions in a way that future agents can reuse.

## Layout and integration boundaries

In the source/full workspace, the paths above are relative to the workspace
root. In an installed skill pack, use `templates/workspace/` as that root;
`assets/skills/` also contains the prompt workflows. The full workspace includes
all root Python modules, including `skill_registry.py` when supplied.
References are under `references/`, and full docs under `templates/workspace/docs/`.
Do not assume skill-relative files exist in the host project's current directory.

This pack is instructions plus optional code, not an automatically connected
backend. Prompts cannot enforce access control or OS isolation. Authenticate and
authorize protected backend operations in the actual integration; do not claim
learning/promotion or external actions without execution evidence. Keep private
context out of shared prompts. For ChatGPT, use only `starter/chatgpt/` and its
manual human review steps; no backend pipeline or local shell is wired there.

## References

- `README.md` for the short install guide.
- `docs/INSTALLATION.md` for runtime-specific installation details.
- `docs/METHODOLOGY.md` for the architecture and rationale.
- `docs/LEARN.md` for the five-layer learning reference.
