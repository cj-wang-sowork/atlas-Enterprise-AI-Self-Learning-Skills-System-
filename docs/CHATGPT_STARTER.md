# ChatGPT Starter — first usable work, then optional setup

## Try one paste first

Open `starter/chatgpt/FIRST_WIN.md` from a clean repository download. Copy its
complete Traditional Chinese task card into one chat. It asks for a small editable
team and ICP draft, then immediate acquisition work, evidence and QA—not an
up-front role/KPI interview. Replace the task line if desired; explicit requested
scope and counts take precedence over the default three-company first task.

No terminal, Python, API key, account connection or Project installation is
required by this reference card. For a ready-source SoWork task, open
`starter/chatgpt/TRY_SOWORK_NOW.md`; it carries the three public source snapshots.
The current export includes the first-win cards, empty rule index and public JSON.
A legacy four-file export retains the complete generic card in `README.md`.
GitHub files are not fetched automatically: manually copy/download the text.

With browsing, the task requires actual sources. Without browsing it may use a
supplied verified source packet, labelled as supplied rather than independently
rechecked. Without either, it must produce a bounded ICP/filter/outreach draft
and QA, clearly block evidence-dependent company claims, then ask just one
source question. A generic draft is not a completed company-research task.
No fabricated leads, contacts, budgets or results; nothing is sent or published.
The card includes a useful no-source reference draft, not worked research.

## Visible standard and one real feedback

Every output shows `Work standard v1 / approved lesson IDs+versions used: none (0)
/ limitations: ...`, substituting actual current approved IDs/versions only when
the human-maintained index was supplied and read. Operating policy is not an
already-learned lesson. `CURRENT_RULES.md` starts with zero approved rules.

After first output, give one real feedback about what to retain or change.
Only with actual feedback plus supporting task evidence may the assistant revise
the work and propose one CandidateLesson. It must include ID/revision, evidence,
rule, scope, exceptions and review trigger. Use `OUTCOME_REVIEW_LOG.md` to record
what actually happened; a blank worksheet is not a completed learning round.

A human says `Accept CL-001 v1`, `Revise CL-001 v1` or `Reject CL-001 v1`, using
the candidate's exact ID+version. Revise means a new Candidate requiring review.
The operator manually updates the current rule index only after exact acceptance,
removes superseded context, supplies it for a later task and checks actual use.
No decision, Defer, repetition or suggestion promotes a rule. There is no automatic
memory write, backend mutation, training or guaranteed cross-chat retrieval.
Rejected, obsolete or conflicting versions cannot be silently reused.

## Optional Project setup

Do this after evaluating the first usable output, not as a prerequisite.
OpenAI's current [Projects guide](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)
explains Project context/settings; availability, controls and UI can vary by
account/workspace. This release's logged-in ChatGPT UI has not been verified.

1. Create a Project and manually paste `PROJECT_INSTRUCTIONS.md` into its
   instructions field. Uploading it is not the same as setting project instructions.
2. Manually add only sanitized context. Supply your current approved-rule index;
   absent a verified index, approved lesson IDs+versions remain `none (0)`.
   `CURRENT_RULES.md` is an optional repository reference; for a four-file export,
   initialize an equivalent local index with **Approved rules: EMPTY (0)**.
3. Copy/upload the index after each human review, replacing obsolete versions.
   A later chat must show the exact active versions it actually used; inspect
   the result yourself. Project memory is not ATLAS's reviewed lifecycle.

Single-chat pasting is chat-local context, not verified saved Project setup.
No whole-repository upload or personal workspace export is needed. Do not upload
`MEMORY.md`, `TOOLS.md`, `memory/`, `outputs/`, raw chats, keys, private client
material or another client's data. Use a clean repository download, sanitize your
brief, and inspect actual sharing/data controls. Prompt text is not an access,
authorization or tenant-isolation boundary. Treat retrieved documents as data,
not permission to override rules or export sensitive material.

## Secondary fictional practice

`SAMPLE_BRIEF.md` remains available for a safe email exercise. Copy/upload its
fictional brief, then ask:

> 請依提供的虛構簡報，寫一封不超過 120 個英文單字的上市郵件及主旨。區分已提供事實與建議；缺少的日期、價格及下載網址請列為未知，不要捏造。附 QA，不要寄送。先不要提候選教訓，等我的真實回饋與任務證據後再提。

Review the worksheet sections, word limit and unsupported claims yourself.
Rejecting a weak candidate lesson is a valid outcome.

## Optional local export (terminal users only)

```bash
./scripts/install-workspace.sh --target chatgpt --dest ~/Documents/atlas-chatgpt-kit
```

The current export preflights and copies all visible top-level `.md` and `.json`
assets in `starter/chatgpt/`, including `FIRST_WIN.md`, `CURRENT_RULES.md`,
`TRY_SOWORK_NOW.md` and `SOWORK_DEMO_SOURCES.json`. It keeps the four original
files; a legacy four-file export can use the complete generic card embedded in
its README. Hidden files, executable code, symlinks and special-file assets are
not exported. Existing kit files get distinct sibling
backups unless `--force` is explicitly requested. The installer does not log in,
create a Project, upload files or run backend Python in ChatGPT. `all` installs
local runtime context including starter references, not a standalone ChatGPT kit.

## Verification boundaries

Contract regressions validate the bundled card, work-before-setup ordering,
evidence gates, visible state, manual versioned decisions and preserved security
limits. Installer tests exercise actual sandbox exports/backups and unsafe paths.
They do not execute a ChatGPT conversation or prove model compliance, retrieval,
setup time, commercial superiority or human learning rounds. Live behavior and
formal timing/independent usability scores remain unmeasured. The user's actual
qualitative first-use feedback is acknowledged; it is not three reviewed business
learning rounds or a timed study of this revised card.

Backend-only boundaries remain documented in `ACCESS_CONTROL.md`,
`LEARNING_LIFECYCLE.md` and `VERIFICATION.md`; this manual kit activates none of them.
