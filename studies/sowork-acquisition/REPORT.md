# SoWork first-value and acquisition A/B pilot

## What was actually exercised

On 2026-10-17, four real task calls and one nonsecret preflight completed using the same requested model (`gpt-6-astra`), reasoning `low`, Codex CLI 0.163.0, frozen public-source pool and available tools. All task traces recorded zero tool calls. A had no ATLAS operating packet; B used the revised Project instructions and the initially empty human-maintained index. There were no retries or invented responses.

**This is a Codex prompt-behavior proxy, not an ordinary ChatGPT web session or a live ChatGPT Project installation test.** The browser did not establish a usable ChatGPT conversation. Provider model-build identity and monetary cost were not independently exposed. These limits prevent claiming measured ChatGPT UI time-to-value or product superiority.

The actual user supplied qualitative first-use feedback about excessive setup. That feedback is acknowledged; it is not a timed observer study or three approved business-learning cycles.

## Observed first-response difference

Same user request: 「我要幫 SoWork 建立一支專門獲取 B2B 新客戶的 AI 行銷團隊。」

- **A / baseline:** six suggested AI roles plus a human owner; a five-company shortlist with partial dated facts, one unsent QNAP opening, no individual company-signal URLs in the response, then a request for three business inputs. **A did begin useful work**; it was not questions-only.
- **B / first use:** three functional roles, editable ICP, three dated source-linked candidates, three individual unsent openings, explicit uncertainty/QA, zero approved lessons, and one specific feedback request.
- Command wall times: A **44.188 s**, B **40.688 s**, one observation per condition. This is not statistically meaningful speed evidence or a measurement of the full acquisition/onboarding process.

The role/draft/input observations are **AI-assisted descriptive inspection of preserved answers**, not independent human quality ratings. Literal source-URL presence is separately computable. Read the originals:

- [A first response](run-20261017/outputs/run-01.txt)
- [B first response](run-20261017/outputs/run-02.txt)

The narrow supported finding is that the revised operating packet made the intended evidence-linked first-work format visible in this proxy run. It does not establish an exclusive capability: ordinary ChatGPT/model baselines can also perform useful work.

## Twenty-company task

Both conditions received the same fixed pool of 20 public research candidates and the same output contract. This tests **screening and drafting from supplied evidence**, not independent open-web lead discovery.

- A and B each returned **20 unique rows** with **20 matching source-ID/company/date/URL/access-class mappings**, explicit unknown budget/decision-maker/agency need/purchase intent, and unsent drafts within the requested 100-codepoint contract.
- These are **metadata/format/uncertainty checks**, not 100% factual accuracy, ICP fit, verified demand or effective outreach.
- Command wall times: A **128.077 s**, B **155.405 s**. B was slower on this task. Do not describe the richer QA output as a productivity win.
- Independent outreach/ICP/factual quality ratings: **not collected**. Editing time, real replies, meetings, revenue and conversion rates: **not measured**. Nothing was sent.

[Comparison CSV with both original outreach drafts](../../outputs/sowork-acquisition-20-comparison.csv), [A original JSON](run-20261017/outputs/run-04.txt), [B original JSON](run-20261017/outputs/run-03.txt), [machine measurements](measurements.json).

## Source strength and selection limits

The pool contains established/large Taiwan-facing technology/manufacturing brands. It is a draft ICP hypothesis, not a representative SME sample or proof of 20 independent purchasing accounts. Related companies may share a group, and contact/agency relationships remain unknown.

Source access at collection:

- **16** announcement bodies read from first-party pages, including one live-browser read without a separate TLS audit.
- **2** bodies obtained by the researcher after disabling local TLS certificate validation (**ADATA, AUO**). They remain explicitly `first_party_body_tls_unverified`, not upgraded to fully verified evidence.
- **2** official-search-snippet-only announcements (**MSI, GIGABYTE**) because full-page access was blocked.

Country/HQ evidence is separately classified. A press-release dateline or corporate office alone does not prove headquarters. AVer Information's HQ evidence is official-index-only; ASUSTOR's office is observed but HQ not independently established. Dates for announcements, planned events and actual completion are not interchangeable. ASUSTOR uses its verified Traditional Chinese page date, not a conflicting locale's index date.

[Source pool](source-pool.json), [integrity/access audit](source-verification.json). Thirty-four researcher evidence references had their provided checksums and quoted support verified; the three parent-researched signals were independently checked before inclusion. No raw private chats, personal contacts or full source-page dumps were published.

## C is blocked, not a fabricated winner

C has **not run** and has no score. There are **zero completed, human-approved business-learning cycles** in this pilot. A general operating policy, one qualitative product feedback, synthetic reviewers and earlier fictional tasks cannot be repackaged as three rounds.

C needs three genuine outcome/feedback/review cycles, exact accepted lesson revisions, and a new unseen holdout task. Then A/B/C must use matching tools/data/model/config. Keep allocation and independent rating forms private until scores are locked; this public repository cannot guarantee blinding. The blank [human scorecard](human-scorecard.json) is not an assessment already performed.

## What changed in the repository

- One-paste **[TRY_SOWORK_NOW.md](../../starter/chatgpt/TRY_SOWORK_NOW.md)** includes three checked public-source snapshots, so a first bounded deliverable need not wait for a role/KPI workshop or a Project setup.
- Generic **[FIRST_WIN.md](../../starter/chatgpt/FIRST_WIN.md)** and Project instructions prefer work before setup, respect requested counts, show evidence/approval state, and request one feedback after delivery.
- **CURRENT_RULES.md** starts empty. Real feedback plus task evidence can produce a Candidate; exact ID/version manual acceptance and index maintenance are still required. No automatic backend learning, cross-chat guarantee or model training is claimed.
- The actual exporter now preflights/copies all supported visible Markdown/JSON assets, rather than silently leaving new cards/index/sources out of the old four-file export. It still rejects unsafe source paths before writes and excludes hidden/executable assets.

**Conclusion:** this iteration fixes the first-deliverable sequence and makes work standards visible. It has not established better sales lists, business results, actual ChatGPT UI timing or the learning promise. The next useful evidence is real feedback on the delivered work and approved-rule reuse on a new task—not more simulated roles.

## Reproducibility and scope

[Protocol](PROTOCOL.md), [pre-execution revision](protocol-revision.json), [frozen plan](execution-plan.json), [actual manifest](run-20261017/manifest.json), [execution-time collector](run-20261017/runner-at-execution.py.txt). Original answers, event logs, prompt files and returned usage are retained; later document changes do not alter them. The code head and every input/packet/transport hash are recorded. Correctly labelled failed trials would remain evidence, not be replaced.

Platform reference (checked 2026-10-17): OpenAI's official
[Projects documentation](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)
separates uploading reference files from entering instructions in Project settings.
The kit follows that distinction; a repository file is not an executed backend.

The collector requires explicit `--execute`, a verified existing CLI path and new private output/work directories. It uses existing authorization in place; do not copy auth or run it as a multi-user service. Repeating trials incurs new model calls and requires a fresh versioned protocol/budget, not overwriting these observations.
