# ATLAS Methodology

ATLAS exists because agent memory fails when every kind of knowledge is treated the same. Enterprise facts, brand rules, team experiments, and personal notes have different audiences and different risk levels. ATLAS makes those boundaries explicit.

## Design Goals

1. Make reusable agent learning portable across OpenClaw, Claude Code, Codex CLI, and Qwen Code CLI.
2. Keep installation simple enough for non-specialists.
3. Separate shared knowledge from private context.
4. Support repeated workflows without adding runtime dependencies.
5. Give teams an architecture they can explain, audit, and extend.

## Core Idea

ATLAS is not a model and not a hosted service. It is a workspace pattern:

```text
Instructions + skills + learning boundaries + optional Python helpers
```

The repository gives agents a stable operating environment. The runtime may change, but the agent still sees the same boot sequence, the same skill instructions, and the same rules for where learning belongs.

## Five-Layer Learning Model

| Layer | Question it answers | Examples | Risk control |
| --- | --- | --- | --- |
| Enterprise | What should every agent know? | Policies, approved processes, cross-market insights | No secrets or PII |
| Brand | What must stay consistent for this brand? | Voice, positioning, claim boundaries | Approved public or internal brand facts only |
| Department | What does this function need? | Marketing workflows, sales playbooks, engineering standards | Internal audience |
| Team | What did this team learn locally? | Experiment results, retrospectives, tactical decisions | Team-only sharing |
| Personal | What is private to one person or agent? | Preferences, drafts, local notes | Never committed or shared by default |

The method is intentionally simple: before saving learning, ask who should be allowed to use it. The answer determines the layer.

## Why This Matters

Agents improve when they can reuse context, but unmanaged memory creates three common failures:

- Scope creep: personal notes become team knowledge without review.
- Context pollution: old or local assumptions influence unrelated work.
- Security drift: credentials, PII, or private decisions are copied into shared files.

ATLAS reduces those failures by making memory placement part of the workflow. Learning is only useful when its audience is clear.

## Runtime Adapter Pattern

Each supported CLI has a different way to load instructions:

| Runtime | Adapter strategy |
| --- | --- |
| OpenClaw | Copy the full workspace to the OpenClaw workspace directory |
| Claude Code | Place a project `CLAUDE.md` launcher and a Claude skill directory |
| Codex CLI | Place a project `AGENTS.md` launcher for Codex instruction discovery |
| Qwen Code CLI | Place a `SKILL.md` directory in Qwen's skill search path |

The installer adapts file placement, not the methodology. This keeps the skill portable.

## Skill Structure

The top-level `SKILL.md` describes the reusable ATLAS workflow. The `skills/` directory contains task-level prompts:

- `brand-positioning.md`
- `web-research.md`
- `content-writer.md`

Agents should load the narrowest skill that matches the task, then apply the five-layer learning rules before writing any durable output.

## Current implementation contracts

Use `docs/ACCESS_CONTROL.md` and `docs/LEARNING_LIFECYCLE.md` for the authoritative scoped APIs. Legacy level-only loaders are intentionally denied. Prompts do not enforce filesystem isolation. Outcome verification and human approval are mandatory before reusable revisions; frequency is not correctness. See `docs/VERIFICATION.md` for evidence and limitations.

## Optional Python Layer

The Python modules are helpers for teams that want programmatic learning behavior:

| Module | Responsibility |
| --- | --- |
| `learn_system.py` | Authorize canonical tenant/brand/team/owner scope before content reads |
| `market_router.py` | Manage market-specific configuration and context |
| `security_checker.py` | Detect sensitive content and policy violations |
| `hermes_adapter.py` | Observe behavior and convert repeated patterns into adaptive rules |
| `market_intelligence.py` | Aggregate cross-market insights and system health |

These modules are optional. The skill pack still works as an instruction system without them.

## Operating Rules

1. Keep public documentation in English for maximum portability.
2. Keep runtime-specific instructions short and point to shared references.
3. Do not commit credentials, personal memory, raw logs, or private customer context.
4. Write durable outputs to `outputs/` when they are useful outside the current session.
5. Log only key decisions, not full transcripts.
6. Prefer explicit install paths over hidden global state.

## Extension Model

To add a new runtime:

1. Identify how the runtime discovers instructions or skills.
2. Add a target to `scripts/install-workspace.sh`.
3. Reuse the same `SKILL.md`, `skills/`, `docs/`, and workspace templates.
4. Document the runtime in `README.md` and `docs/INSTALLATION.md`.
5. Verify installation in a temporary directory before opening a PR.

To add a new workflow skill:

1. Create a Markdown file under `skills/`.
2. Define the trigger, inputs, process, and expected output.
3. Add it to `SKILL.md` and the README if it is part of the default pack.
4. Include security notes for any workflow that touches customer, market, or personal data.
