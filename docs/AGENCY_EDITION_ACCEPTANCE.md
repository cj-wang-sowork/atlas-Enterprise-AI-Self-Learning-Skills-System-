# Agency Edition v1.0 — acceptance scope and execution plan

## Product scope

ATLAS — Build Your AI Marketing Team Inside ChatGPT.

This edition is a **manual ChatGPT Project workflow**, one client per Project.
Five sequential professional roles are work stages of one conversation/model,
not five deployed autonomous agents. The existing generic Starter Kit and Python
identity/learning/safety implementation remain separate and are not replaced.
No CRM, background scheduler, automatic email/social publishing, production SSO
or automatic local/Project-file write-back is added by this edition.

The three-minute setup is a design target, not a measured usability result.
Native account, plan, memory and sharing permissions apply; file organization and
manual reviewer agreements are not an ATLAS backend isolation/authorization guarantee.

## Delivery and source boundaries

- Core authoring templates: AGENCY_SETUP, PROJECT_INSTRUCTIONS, CLIENT_BRIEF,
  AGENT_ROLES, WORKFLOW, TASK_BOARD, CURRENT_RULES and REVIEW_LOG.
- Self-contained SKILL_PACK adapts the six actual Brand to Social OS workflows;
  pin source commit `a230b7f6f5ed987fefbb8f4933c411681701c8ed`, retain its full
  MIT notice and provenance, and do not modify that upstream repository.
- Ready upload sources: CLIENT_BRIEF.md, AGENCY_PLAYBOOK.md, TASK_BOARD.md,
  CURRENT_RULES.md, REVIEW_LOG.md. Paste PROJECT_INSTRUCTIONS into Project settings.
  AGENCY_PLAYBOOK is deterministically compiled from AGENT_ROLES + WORKFLOW +
  SKILL_PACK. Do not upload competing duplicate authoring references alongside it.
- SAMPLE_WORK combines the separately labelled synthetic skincare brief and
  complete first-round example. It belongs only in a separate demo Project,
  never mixed into real client context.
- A dedicated `--target chatgpt-agency` exports all 13 supported payload files,
  including license/provenance; `--target chatgpt` retains its original eight files.
  Source/destination/symlink/type checks run before writes; documented executable,
  POSIX sh and actual available dash must work. No account is accessed by export.

## Acceptance matrix

1. **Agency Starter Kit / code-document gate:** required files, bounded complete
   Project instructions, one-line task, editable assumptions, first real draft
   before optional interviews; source-closure and license checks.
2. **Five-stage first round / code-document gate:** usable Client Brief, Research
   Brief, Strategy Brief, seven-day Content Calendar with all seven copy drafts,
   and QA Review Report. Missing evidence stays unknown/blocked; draft completion
   is not publication or human approval.
3. **Collaboration / protocol gate:** one task per chat, client/task/artifact/version
   bindings, human owner/reviewer, handoff proof and current shared documents;
   conflict handling and one maintainer. Two real humans completing this in the
   actual Project UI is a separate pending acceptance gate.
4. **Learning / protocol gate:** revise current work first, then actual feedback
   plus evidence may produce a scoped Candidate; exact-version human decision,
   manual current-rule update, and read-back in a new conversation. Initially
   zero approved rules. No synthetic or hypothetical feedback counts as human
   learning evidence; technical reviewer enforcement needs a trusted backend.
5. **Backend / not included in v1.0:** existing Python reference integrations remain
   untouched; no claim that uploading these files connects or runs them.
6. **Installation / real CLI gate:** isolated Agency export, all required assets
   byte-identical, generic compatibility, missing license rejection before writes,
   source/destination symlink rejection, hidden/unsupported/inherited-glob safety.
7. **Delivery / release gate:** full suite with pinned optional dependencies and
   zero skips, independent spec then code-quality review, exact-head hosted CI,
   pinned merge/read-back and a verified downloadable source package.

## Live/human and model evidence

At this plan checkpoint: no Agency Edition live ChatGPT Project installation,
non-engineer timing, two-human collaboration trial, cross-conversation human
approved-rule reuse or business uplift has been observed. Their rates and times
remain unmeasured, not zero-success claims. The user's qualitative feedback about
prior ATLAS setup is real but does not satisfy these new edition gates.

Any later model adherence probe must be registered before execution, bounded and
labelled as synthetic-client **agent QA / CLI proxy** unless performed in the
actual target interface. It must preserve original prompts/answers, configuration,
failures, source locks and unknown costs; do not call it two-human validation or
backend learning. No model trial has been run for this edition at this checkpoint.

## Platform reference checkpoint

Checked 2026-10-18 against official indexed excerpts of OpenAI's Projects article:
https://help.openai.com/en/articles/10169521-projects-in-chatgpt

Project settings instructions differ from uploaded reference files. Shared Project
members can create/branch task conversations; native chat/edit access differs,
and editors may alter instructions/files. Shared Projects use project-only memory;
account/workspace controls and actual UI availability still govern behavior.
Direct HTTP article retrieval was blocked in this environment, so these source
excerpts are not a live account/UI test. Do not confuse this file kit with native
Workspace Agents or imply ChatGPT has no other separately configured capabilities.

## Starting repository state

Write invitation `338298222` was accepted and repository push permission read back
as true. Earlier PR #4 had already been externally merged on 2026-10-18;
`main` commit `690ae8249cd38dd2fdb70043da0dd5b91d2985d7` has the exact previously
reviewed tree `ef0dc05cb1f5136071c3145617d3d3701d72a43c`. That external merge is not
attributed to this agent. Agency implementation is isolated from that verified base.
